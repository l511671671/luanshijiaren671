"""
自动自评与规则进化闭环

每次任务结束后，用辩论 + 复盘对输出打分，
生成改进建议并沉淀到长期记忆候选。

用法：
    python self_eval.py --prompt "设计A股交易系统" --output "方案..." --trace "Bash..."
"""

from __future__ import annotations

import argparse
import datetime
import json
from pathlib import Path
from typing import Dict, List, Optional

from auto_review import review_text, format_memory_entry
from multi_agent.debate import DebateOrchestrator, EchoBackend, CodeBuddyBackend, get_default_backend


WORKBUDDY_DIR = Path(__file__).resolve().parent


def score_output(review: Dict, debate: Dict) -> Dict:
    """基于复盘和辩论结果给出质量评分。"""
    error_count = review.get("error_count", 0)
    correction_count = review.get("correction_count", 0)
    debate_rounds = debate.get("rounds", 0)

    # 基础分 10，按问题扣减
    score = 10.0
    score -= min(error_count * 1.5, 4.0)
    score -= min(correction_count * 1.0, 3.0)
    score = max(0.0, min(10.0, score))

    verdict = "pass" if score >= 7 else "needs_improvement"
    return {
        "score": round(score, 1),
        "verdict": verdict,
        "factors": {
            "errors": error_count,
            "corrections": correction_count,
            "debate_rounds": debate_rounds,
        },
    }


def suggest_rules(review: Dict, debate: Dict) -> List[str]:
    """合并复盘与辩论意见，生成规则建议。"""
    rules = set(review.get("suggested_rules", []))
    # 从辩论 transcript 里提取 Synthesizer 的最终意见
    for item in debate.get("transcript", []):
        if item.get("role") == "Synthesizer":
            content = item.get("content", "")
            # 简单按行拆分，取前 3 条建议
            for line in content.split("\n")[:3]:
                line = line.strip()
                if line and len(line) > 5:
                    rules.add(line)
    return list(rules)


def evaluate(prompt: str, output: str, trace: str = "", rounds: int = 1) -> Dict:
    """对一次任务输出进行完整自评。"""
    full_text = f"PROMPT:\n{prompt}\n\nOUTPUT:\n{output}\n\nTRACE:\n{trace}"
    review = review_text(full_text)

    draft = f"用户请求：{prompt}\n\n系统输出：{output}\n\n执行轨迹：{trace}".strip()
    orchestrator = DebateOrchestrator(backend=get_default_backend())
    debate = orchestrator.run(prompt, draft=draft, rounds=rounds)

    scoring = score_output(review, debate)
    rules = suggest_rules(review, debate)

    return {
        "prompt": prompt,
        "scoring": scoring,
        "review": review,
        "debate": debate,
        "suggested_rules": rules,
        "memory_entry": format_memory_entry(review),
    }


def write_daily_eval(eval_result: Dict, base_dir: Optional[Path] = None) -> Path:
    base_dir = base_dir or WORKBUDDY_DIR / "memory"
    base_dir.mkdir(parents=True, exist_ok=True)
    date_str = datetime.date.today().isoformat()
    path = base_dir / f"{date_str}_self_eval.json"

    data = []
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            data = []
    data.append(eval_result)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(description="WorkBuddy 自动自评")
    parser.add_argument("--prompt", required=True, help="原始用户请求")
    parser.add_argument("--output", default="", help="系统输出文本")
    parser.add_argument("--trace", default="", help="执行轨迹/日志")
    parser.add_argument("--rounds", type=int, default=1, help="辩论轮数")
    parser.add_argument("--write-daily", action="store_true", help="写入 memory/YYYY-MM-DD_self_eval.json")
    args = parser.parse_args(argv)

    result = evaluate(args.prompt, args.output, args.trace, rounds=args.rounds)
    print(json.dumps(result, ensure_ascii=False, indent=2))

    if args.write_daily:
        path = write_daily_eval(result)
        print(f"[self_eval] written to {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
