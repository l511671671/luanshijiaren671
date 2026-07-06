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


def cmd_review(args: argparse.Namespace) -> int:
    from auto_review import review_text, write_daily_review, format_memory_entry

    if args.transcript:
        text = Path(args.transcript).read_text(encoding="utf-8", errors="ignore")
    elif args.file:
        text = Path(args.file).read_text(encoding="utf-8", errors="ignore")
    else:
        text = args.text or ""

    review = review_text(text)
    if args.write_daily:
        path = write_daily_review(review)
        print(f"[WorkBuddy] review written to {path}")
    if args.memory:
        print("[WorkBuddy] suggested memory entry:")
        print(format_memory_entry(review))
    if not args.write_daily and not args.memory:
        print(format_memory_entry(review))
    return 0


def cmd_project_info(args: argparse.Namespace) -> int:
    from project_context import ProjectContext

    ctx = ProjectContext.from_path(args.path)
    if args.json:
        print(json.dumps(ctx.summary(), ensure_ascii=False, indent=2))
    else:
        print(ctx.to_prompt_context())
    return 0


def cmd_ship(args: argparse.Namespace) -> int:
    from git_workflow import GitWorkflow, get_project_root

    repo = get_project_root(args.repo)
    wf = GitWorkflow(repo)
    result = wf.ship(args.message, run_tests=not args.skip_tests)
    for step in result.steps:
        status = "OK" if step["ok"] else "FAIL"
        print(f"[{status}] {step['name']}")
        if step["output"]:
            print(step["output"])
    return 0 if result.success else 1


def cmd_debate(args: argparse.Namespace) -> int:
    from multi_agent.debate import DebateOrchestrator

    orchestrator = DebateOrchestrator()
    result = orchestrator.run(args.prompt, draft=args.draft, rounds=args.rounds)
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    return 0


def cmd_run_connectors(args: argparse.Namespace) -> int:
    from connectors import ConnectorRunner

    runner = ConnectorRunner(config=args.config or {})
    names = args.connector if args.connector else (list(runner.REGISTERED.keys()) if args.all else [])
    if not names:
        print("[WorkBuddy] 请指定 --connector 或 --all")
        return 1
    results = runner.run(names)
    report = runner.to_report(results)
    print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
    return 0 if report["success"] else 1


def cmd_self_eval(args: argparse.Namespace) -> int:
    from self_eval import evaluate, write_daily_eval

    result = evaluate(args.prompt, args.output, args.trace, rounds=args.rounds)
    if args.write_daily:
        path = write_daily_eval(result)
        print(f"[WorkBuddy] self-eval written to {path}")
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    return 0


def cmd_checkpoint_list(args: argparse.Namespace) -> int:
    from checkpoint_runner import CheckpointRunner

    runner = CheckpointRunner()
    cps = runner.list_active()
    for cp in cps:
        print(f"{cp.task_id}\t{cp.status}\t{cp.task}")
    return 0


def cmd_checkpoint_resume(args: argparse.Namespace) -> int:
    from checkpoint_runner import CheckpointRunner

    runner = CheckpointRunner()
    result = runner.resume(args.task_id)
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    return 0 if result["success"] else 1


def cmd_checkpoint_create(args: argparse.Namespace) -> int:
    from checkpoint_runner import CheckpointRunner

    runner = CheckpointRunner()
    cp = runner.create(args.task, steps=args.steps)
    print(f"[WorkBuddy] checkpoint created: {cp.task_id}")
    return 0


def cmd_skill(args: argparse.Namespace) -> int:
    from skill_manager import SkillManager

    manager = SkillManager()
    if args.skill_command == "list":
        for skill in manager.list_skills():
            print(f"{'[E]' if skill.enabled else '[D]'} {skill.name}\n  {skill.description}")
    elif args.skill_command == "recommend":
        for skill in manager.recommend(args.task, args.top_k):
            print(f"- {skill.name}: {skill.description}")
    elif args.skill_command == "enable":
        ok = manager.enable(args.name)
        print(f"{'enabled' if ok else 'not found'} {args.name}")
    elif args.skill_command == "disable":
        ok = manager.disable(args.name)
        print(f"{'disabled' if ok else 'not found'} {args.name}")
    elif args.skill_command == "prune":
        for name in manager.prune_candidates(args.days):
            print(f"prune candidate: {name}")
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

    p_review = sub.add_parser("review", help="自动复盘本次会话")
    group = p_review.add_mutually_exclusive_group()
    group.add_argument("--transcript", help="会话记录文件路径")
    group.add_argument("--file", help="任意日志文件路径")
    group.add_argument("--text", help="会话文本")
    p_review.add_argument("--write-daily", action="store_true", help="写入 memory/YYYY-MM-DD_review.md")
    p_review.add_argument("--memory", action="store_true", help="输出建议的 MEMORY.md 条目")
    p_review.set_defaults(func=cmd_review)

    p_project = sub.add_parser("project-info", help="加载项目上下文")
    p_project.add_argument("--path", type=Path, default=Path.cwd(), help="起始路径")
    p_project.add_argument("--json", action="store_true", help="输出 JSON 摘要")
    p_project.set_defaults(func=cmd_project_info)

    p_ship = sub.add_parser("ship", help="测试 -> 提交 -> 推送")
    p_ship.add_argument("--repo", type=Path, default=None, help="仓库路径")
    p_ship.add_argument("--message", default="WorkBuddy auto commit", help="提交信息")
    p_ship.add_argument("--skip-tests", action="store_true", help="跳过测试")
    p_ship.set_defaults(func=cmd_ship)

    p_debate = sub.add_parser("debate", help="多 Agent 质量辩论")
    p_debate.add_argument("prompt", help="待辩论的命题")
    p_debate.add_argument("--draft", default=None, help="初始方案")
    p_debate.add_argument("--rounds", type=int, default=1, help="辩论轮数")
    p_debate.set_defaults(func=cmd_debate)

    p_connectors = sub.add_parser("run-connectors", help="运行外部连接器")
    p_connectors.add_argument("--connector", action="append", help="指定连接器，可多次使用")
    p_connectors.add_argument("--all", action="store_true", dest="run_all", help="运行所有连接器")
    p_connectors.add_argument("--config", type=json.loads, default={}, help="JSON 配置")
    p_connectors.set_defaults(func=cmd_run_connectors)

    p_self_eval = sub.add_parser("self-eval", help="自动自评任务输出")
    p_self_eval.add_argument("--prompt", required=True, help="原始用户请求")
    p_self_eval.add_argument("--output", default="", help="系统输出文本")
    p_self_eval.add_argument("--trace", default="", help="执行轨迹/日志")
    p_self_eval.add_argument("--rounds", type=int, default=1, help="辩论轮数")
    p_self_eval.add_argument("--write-daily", action="store_true", help="写入 memory/YYYY-MM-DD_self_eval.json")
    p_self_eval.set_defaults(func=cmd_self_eval)

    p_cp = sub.add_parser("checkpoint", help="跨会话任务续跑")
    cp_sub = p_cp.add_subparsers(dest="cp_command", required=True)
    p_cp_list = cp_sub.add_parser("list", help="列出活跃 checkpoint")
    p_cp_list.set_defaults(func=cmd_checkpoint_list)
    p_cp_resume = cp_sub.add_parser("resume", help="恢复指定 checkpoint")
    p_cp_resume.add_argument("task_id", help="task_id")
    p_cp_resume.set_defaults(func=cmd_checkpoint_resume)
    p_cp_create = cp_sub.add_parser("create", help="创建 checkpoint")
    p_cp_create.add_argument("task", help="任务描述")
    p_cp_create.add_argument("--steps", type=json.loads, default=[], help="JSON 步骤列表")
    p_cp_create.set_defaults(func=cmd_checkpoint_create)

    p_skill = sub.add_parser("skill", help="Skill 管理")
    skill_sub = p_skill.add_subparsers(dest="skill_command", required=True)
    p_skill_list = skill_sub.add_parser("list", help="列出已安装 skill")
    p_skill_list.set_defaults(func=cmd_skill)
    p_skill_rec = skill_sub.add_parser("recommend", help="根据任务推荐 skill")
    p_skill_rec.add_argument("task", help="任务描述")
    p_skill_rec.add_argument("--top-k", type=int, default=3)
    p_skill_rec.set_defaults(func=cmd_skill)
    p_skill_enable = skill_sub.add_parser("enable", help="启用 skill")
    p_skill_enable.add_argument("name", help="skill 名称")
    p_skill_enable.set_defaults(func=cmd_skill)
    p_skill_disable = skill_sub.add_parser("disable", help="禁用 skill")
    p_skill_disable.add_argument("name", help="skill 名称")
    p_skill_disable.set_defaults(func=cmd_skill)
    p_skill_prune = skill_sub.add_parser("prune", help="列出可清理 skill")
    p_skill_prune.add_argument("--days", type=int, default=60)
    p_skill_prune.set_defaults(func=cmd_skill)

    return parser


def main(argv: list | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
