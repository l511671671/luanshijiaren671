"""
项目 Git 工作流：测试、提交、推送一条龙

用法：
    python git_workflow.py --repo /path/to/repo --message "fix bug"
    python git_workflow.py --ship  # 在 .workbuddy_project 标记的项目里执行
"""

from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from tools.git_client import GitClient


@dataclass
class WorkflowResult:
    success: bool
    steps: List[Dict] = field(default_factory=list)

    def add(self, name: str, ok: bool, output: str = "") -> None:
        self.steps.append({"name": name, "ok": ok, "output": output})


def run_command(cmd: List[str], cwd: Optional[Path] = None, check: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=check,
    )


class GitWorkflow:
    def __init__(self, repo_path: Path, test_command: Optional[List[str]] = None):
        self.repo_path = Path(repo_path)
        self.test_command = test_command or ["python", "-m", "pytest", "-q"]
        self.git = GitClient(str(self.repo_path), allow_write=True)

    def run_tests(self) -> WorkflowResult:
        result = WorkflowResult(success=False)
        proc = run_command(self.test_command, cwd=self.repo_path)
        ok = proc.returncode == 0
        result.add("test", ok, proc.stdout or proc.stderr)
        result.success = ok
        return result

    def commit(self, message: str, allow_empty: bool = False) -> WorkflowResult:
        result = WorkflowResult(success=False)
        status = self.git.status()
        if not status.stdout.strip() and not allow_empty:
            result.add("status", True, "nothing to commit")
            result.success = True
            return result

        self.git.add(".")
        commit = self.git.commit(message)
        ok = commit.ok
        result.add("commit", ok, commit.stdout or commit.stderr)
        result.success = ok
        return result

    def push(self, remote: str = "origin", branch: str = "main") -> WorkflowResult:
        result = WorkflowResult(success=False)
        push = self.git.push(remote, branch)
        result.add("push", push.ok, push.stdout or push.stderr)
        result.success = push.ok
        return result

    def ship(self, message: str, run_tests: bool = True) -> WorkflowResult:
        """测试 -> 提交 -> 推送。"""
        result = WorkflowResult(success=False)
        if run_tests:
            test_result = self.run_tests()
            result.steps.extend(test_result.steps)
            if not test_result.success:
                return result
        commit_result = self.commit(message)
        result.steps.extend(commit_result.steps)
        if not commit_result.success:
            return result
        push_result = self.push()
        result.steps.extend(push_result.steps)
        result.success = push_result.success
        return result


def get_project_root(start_path: Optional[Path] = None) -> Path:
    path = Path(start_path or Path.cwd()).resolve()
    for parent in [path, *path.parents]:
        if (parent / ".workbuddy_project").exists() or (parent / ".git").exists():
            return parent
    return path


def main(argv: list | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="WorkBuddy Git 工作流")
    parser.add_argument("--repo", type=Path, default=None, help="仓库路径")
    parser.add_argument("--message", default="WorkBuddy auto commit", help="提交信息")
    parser.add_argument("--skip-tests", action="store_true", help="跳过测试")
    parser.add_argument("--ship", action="store_true", help="执行 test -> commit -> push")
    parser.add_argument("--push-only", action="store_true", help="只推送")
    args = parser.parse_args(argv)

    repo = Path(args.repo) if args.repo else get_project_root()
    wf = GitWorkflow(repo)

    if args.push_only:
        result = wf.push()
    elif args.ship:
        result = wf.ship(args.message, run_tests=not args.skip_tests)
    else:
        result = wf.commit(args.message)

    for step in result.steps:
        status = "OK" if step["ok"] else "FAIL"
        print(f"[{status}] {step['name']}")
        if step["output"]:
            print(step["output"])
    return 0 if result.success else 1


if __name__ == "__main__":
    raise SystemExit(main())
