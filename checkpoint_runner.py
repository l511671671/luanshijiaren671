"""
跨会话任务续跑

用法：
    python checkpoint_runner.py --list
    python checkpoint_runner.py --resume <task_id>
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from checkpoint import Checkpoint, CheckpointStore, generate_task_id

WORKBUDDY_DIR = Path(__file__).resolve().parent


class CheckpointRunner:
    def __init__(self, store: Optional[CheckpointStore] = None):
        self.store = store or CheckpointStore()

    def create(self, task: str, steps: List[Dict[str, Any]]) -> Checkpoint:
        task_id = generate_task_id(task)
        cp = Checkpoint(
            task_id=task_id,
            task=task,
            status="running",
            steps_done=[],
            steps_pending=steps,
        )
        self.store.save(cp)
        return cp

    def list_active(self) -> List[Checkpoint]:
        return self.store.list_active()

    def resume(self, task_id: str) -> Dict[str, Any]:
        cp = self.store.load(task_id)
        if cp is None:
            return {"success": False, "error": f"checkpoint {task_id} not found"}

        cp.status = "running"
        self.store.save(cp)

        results = []
        while cp.steps_pending:
            step = cp.steps_pending.pop(0)
            result = self._execute_step(step)
            cp.steps_done.append({"step": step, "result": result})
            if not result.get("success"):
                cp.status = "paused"
                self.store.save(cp)
                return {
                    "success": False,
                    "task_id": task_id,
                    "failed_step": step,
                    "results": results,
                }
            results.append(result)

        cp.status = "completed"
        self.store.save(cp)
        return {"success": True, "task_id": task_id, "results": results}

    def _execute_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        command = step.get("command")
        if not command:
            return {"success": True, "output": "no command"}
        try:
            proc = subprocess.run(
                command,
                shell=True,
                cwd=str(WORKBUDDY_DIR),
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            return {
                "success": proc.returncode == 0,
                "returncode": proc.returncode,
                "stdout": proc.stdout,
                "stderr": proc.stderr,
            }
        except Exception as exc:  # pragma: no cover
            return {"success": False, "error": str(exc)}


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(description="WorkBuddy Checkpoint Runner")
    parser.add_argument("--list", action="store_true", help="列出活跃 checkpoint")
    parser.add_argument("--resume", help="恢复指定 task_id")
    parser.add_argument("--create", help="创建 checkpoint 的任务描述")
    parser.add_argument("--steps", type=json.loads, default="[]", help="JSON 步骤列表")
    args = parser.parse_args(argv)

    runner = CheckpointRunner()

    if args.list:
        cps = runner.list_active()
        for cp in cps:
            print(f"{cp.task_id}\t{cp.status}\t{cp.task}")
        return 0

    if args.resume:
        result = runner.resume(args.resume)
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
        return 0 if result["success"] else 1

    if args.create:
        cp = runner.create(args.create, steps=args.steps)
        print(f"[checkpoint] created {cp.task_id}")
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
