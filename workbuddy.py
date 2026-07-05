"""
WorkBuddy 统一入口

把 Brain + Router + Agents + Memory + Tools + Self-improvement 串成一条命令：

  python workbuddy.py think "帮我设计一个A股量化交易系统"
  python workbuddy.py run "写个营销方案"
  python workbuddy.py plan "帮我写一个 Python 脚本读取 CSV"
  python workbuddy.py verify output.md
  python workbuddy.py improve
  python workbuddy.py test
  python workbuddy.py memory search "主板股票"
  python workbuddy.py agent "看看这个股票"
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

WORKBUDDY_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(WORKBUDDY_DIR))

from workbuddy_brain import WorkBuddyBrain  # noqa: E402


def _brain() -> WorkBuddyBrain:
    return WorkBuddyBrain()


def cmd_think(args: argparse.Namespace) -> int:
    plan = _brain().think(args.prompt)
    print(json.dumps(plan, ensure_ascii=False, indent=2))
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    brain = _brain()
    plan = brain.think(args.prompt)
    print(json.dumps(plan, ensure_ascii=False, indent=2))
    print("--- executing ---")
    try:
        brain.run(args.prompt)
    except Exception as exc:
        print(f"[WorkBuddy] CLI execution failed: {exc}")
        return 1
    return 0


def cmd_plan(args: argparse.Namespace) -> int:
    from multi_agent.memory_orchestrator import MemoryOrchestrator

    orchestrator = MemoryOrchestrator()
    result = orchestrator.run(args.task)
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    from meta_cognition import QualityGate

    gate = QualityGate()
    result = gate.verify_file(args.path)
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    return 0 if result["passed"] else 1


def cmd_improve(args: argparse.Namespace) -> int:
    import importlib.util

    runner_path = WORKBUDDY_DIR / "self-improving" / "runner.py"
    spec = importlib.util.spec_from_file_location("self_improving_runner", runner_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    runner = mod.SelfImprovementRunner()
    runner.run()
    return 0


def cmd_test(args: argparse.Namespace) -> int:
    from run_regression import run_all_tests

    report = run_all_tests()
    print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
    return 0 if report["success"] else 1


def cmd_memory(args: argparse.Namespace) -> int:
    from memory.chroma_memory import ChromaMemory

    mem = ChromaMemory(collection_name="workbuddy_tasks")
    if args.action == "search":
        results = mem.query(args.query, n_results=args.n)
        print(json.dumps(results, ensure_ascii=False, indent=2, default=str))
    elif args.action == "add":
        entry_id = mem.add(args.text, metadata=args.meta or {})
        print(f"[WorkBuddy] added memory entry {entry_id}")
    return 0


def cmd_agent(args: argparse.Namespace) -> int:
    from agents.registry import AgentRegistry

    registry = AgentRegistry(str(WORKBUDDY_DIR / "agents"))
    matches = registry.match(args.prompt, top_k=args.top_k)
    print(
        json.dumps(
            [{"id": a.id, "description": a.description, "trigger_words": a.trigger_words} for a in matches],
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="workbuddy", description="WorkBuddy 统一入口")
    sub = parser.add_subparsers(dest="command", required=True)

    p_think = sub.add_parser("think", help="分析 prompt 并返回路由计划（不执行）")
    p_think.add_argument("prompt", help="用户请求")
    p_think.set_defaults(func=cmd_think)

    p_run = sub.add_parser("run", help="分析 prompt 并调用 WorkBuddy CLI 执行")
    p_run.add_argument("prompt", help="用户请求")
    p_run.set_defaults(func=cmd_run)

    p_plan = sub.add_parser("plan", help="使用多 Agent Orchestrator 生成执行计划")
    p_plan.add_argument("task", help="任务描述")
    p_plan.set_defaults(func=cmd_plan)

    p_verify = sub.add_parser("verify", help="验证文件或文本是否符合质量门")
    p_verify.add_argument("path", help="待验证文件路径")
    p_verify.set_defaults(func=cmd_verify)

    p_improve = sub.add_parser("improve", help="运行自改进流程")
    p_improve.set_defaults(func=cmd_improve)

    p_test = sub.add_parser("test", help="运行自动化回归测试")
    p_test.set_defaults(func=cmd_test)

    p_memory = sub.add_parser("memory", help="操作长期记忆")
    p_memory.add_argument("action", choices=["search", "add"], help="动作")
    p_memory.add_argument("query", nargs="?", default="", help="查询文本或要保存的文本")
    p_memory.add_argument("--n", type=int, default=3, help="返回条数")
    p_memory.add_argument("--meta", type=json.loads, default=None, help="JSON 格式元数据")
    p_memory.set_defaults(func=cmd_memory)

    p_agent = sub.add_parser("agent", help="匹配领域 Agent")
    p_agent.add_argument("prompt", help="用户请求")
    p_agent.add_argument("--top-k", type=int, default=1, help="返回 agent 数量")
    p_agent.set_defaults(func=cmd_agent)

    return parser


def main(argv: list | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
