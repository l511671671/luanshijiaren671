"""
自动复盘与规则进化

用法：
    python auto_review.py --transcript session.txt
    python auto_review.py --text "本次对话..."
    python auto_review.py --file workbuddy.log
"""

from __future__ import annotations

import argparse
import datetime
import json
import re
from pathlib import Path
from typing import Dict, List, Optional

WORKBUDDY_DIR = Path(__file__).resolve().parent

_TOOL_CALL_RE = re.compile(r"^\s*(\w+\.(?:Read|Edit|Write|Bash|Grep|Agent|AskUserQuestion|TodoWrite|Skill|WebFetch|WebSearch|ImageGen|ImageSearch|NotebookEdit))", re.MULTILINE)
_ERROR_RE = re.compile(r"(?i)(error|exception|traceback|failed|failure|fatal|wrong|incorrect|invalid)")
_CORRECTION_RE = re.compile(r"(?i)(不对|错了|应该|修正|纠正|改一下|重试|not what I want|that's wrong|please fix|correction)")


def extract_tool_calls(text: str) -> List[str]:
    return [m.group(1) for m in _TOOL_CALL_RE.finditer(text)]


def extract_errors(text: str) -> List[str]:
    lines = text.splitlines()
    hits = []
    for i, line in enumerate(lines):
        if _ERROR_RE.search(line):
            hits.append(f"line {i + 1}: {line.strip()[:120]}")
    return hits


def extract_corrections(text: str) -> List[str]:
    lines = text.splitlines()
    hits = []
    for i, line in enumerate(lines):
        if _CORRECTION_RE.search(line):
            hits.append(f"line {i + 1}: {line.strip()[:120]}")
    return hits


def summarize(text: str, max_chars: int = 500) -> str:
    text = text.strip()
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rsplit("\n", 1)[0] + "\n..."


def suggest_rule(successes: List[str], failures: List[str], corrections: List[str]) -> List[str]:
    """基于本次会话的得失，生成候选规则/注意事项。"""
    rules = []
    if failures:
        rules.append("遇到外部工具失败时，先重试一次并打印原始错误，再升级 fallback。")
    if corrections:
        rules.append("用户对输出格式/结果有明确纠正时，优先把纠正内容加入长期记忆。")
    if "Edit" in successes or "Write" in successes:
        rules.append("修改文件前务必用 Read 确认上下文，避免 off-by-one 错误。")
    if not rules:
        rules.append("本次无明显问题，保持当前工作流即可。")
    return rules


def review_text(text: str, date_str: Optional[str] = None) -> Dict:
    """对一段会话文本生成结构化复盘。"""
    tool_calls = extract_tool_calls(text)
    errors = extract_errors(text)
    corrections = extract_corrections(text)
    summary = summarize(text)

    successes = list({t for t in tool_calls})  # 去重
    return {
        "date": date_str or datetime.date.today().isoformat(),
        "summary": summary,
        "tools_used": successes,
        "tool_count": len(tool_calls),
        "errors": errors,
        "error_count": len(errors),
        "corrections": corrections,
        "correction_count": len(corrections),
        "suggested_rules": suggest_rule(successes, errors, corrections),
    }


def format_memory_entry(review: Dict) -> str:
    """生成建议写入 MEMORY.md 的条目。"""
    parts = [
        f"会话复盘 {review['date']}:",
        f"- 工具使用: {review['tool_count']} 次 ({', '.join(review['tools_used'][:5])})",
        f"- 错误/异常: {review['error_count']} 次",
        f"- 用户纠正: {review['correction_count']} 次",
        "- 建议规则:",
    ]
    for rule in review["suggested_rules"]:
        parts.append(f"  · {rule}")
    return "\n".join(parts)


def write_daily_review(review: Dict, base_dir: Optional[Path] = None) -> Path:
    """把复盘写入 memory/YYYY-MM-DD_review.md。"""
    base_dir = base_dir or WORKBUDDY_DIR / "memory"
    base_dir.mkdir(parents=True, exist_ok=True)
    date_str = review["date"]
    path = base_dir / f"{date_str}_review.md"

    lines = [
        f"# 复盘 {date_str}",
        "",
        "## 摘要",
        review["summary"],
        "",
        f"## 工具使用（{review['tool_count']} 次）",
        "",
        *["- " + t for t in review["tools_used"]],
        "",
        f"## 错误/异常（{review['error_count']} 处）",
        "",
        *["- " + e for e in review["errors"]],
        "",
        f"## 用户纠正（{review['correction_count']} 处）",
        "",
        *["- " + c for c in review["corrections"]],
        "",
        "## 建议规则",
        "",
        *["- " + r for r in review["suggested_rules"]],
        "",
        "## 建议 MEMORY 条目",
        "",
        "```text",
        format_memory_entry(review),
        "```",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(description="WorkBuddy 自动复盘")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--transcript", type=Path, help="会话记录文件路径")
    group.add_argument("--text", help="会话文本")
    group.add_argument("--file", type=Path, help="任意日志文件路径")
    parser.add_argument("--out-json", action="store_true", help="输出 JSON")
    parser.add_argument("--write-daily", action="store_true", help="写入 memory/YYYY-MM-DD_review.md")
    args = parser.parse_args(argv)

    if args.transcript:
        text = args.transcript.read_text(encoding="utf-8", errors="ignore")
    elif args.text:
        text = args.text
    else:
        text = args.file.read_text(encoding="utf-8", errors="ignore")

    review = review_text(text)
    if args.write_daily:
        path = write_daily_review(review)
        print(f"[auto_review] written to {path}")
    if args.out_json:
        print(json.dumps(review, ensure_ascii=False, indent=2))
    else:
        print(format_memory_entry(review))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
