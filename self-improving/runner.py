"""
Self-Improvement Runner

周期性扫描 self-improving/ 目录，生成可执行的改进项，
并更新到 self-improving/memory.md。

运行：
  python self-improving/runner.py
"""

from __future__ import annotations

import os
import re
from datetime import datetime
from pathlib import Path
from typing import List


class SelfImprovementRunner:
    def __init__(self, base_dir: str = None):
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).parent
        self.corrections_path = self.base_dir / "corrections.md"
        self.memory_path = self.base_dir / "memory.md"

    def read_file(self, path: Path) -> str:
        if not path.exists():
            return ""
        return path.read_text(encoding="utf-8")

    def count_recent_corrections(self) -> int:
        text = self.read_file(self.corrections_path)
        # 简单统计 "### YYYY-MM-DD" 标题数量
        return len(re.findall(r"###\s*\d{4}-\d{2}-\d{2}", text))

    def generate_actions(self) -> List[str]:
        actions = []
        correction_count = self.count_recent_corrections()
        if correction_count > 0:
            actions.append(f"review and close {correction_count} open corrections")

        actions.extend([
            "review MEMORY.md for outdated rules",
            "run all tests and fix regressions",
            "check model routing accuracy for last 10 prompts",
        ])
        return actions

    def update_memory(self, actions: List[str]):
        text = self.read_file(self.memory_path)
        today = datetime.now().strftime("%Y-%m-%d")
        block = f"\n\n## Auto Review {today}\n\n- " + "\n- ".join(actions) + "\n"

        if "## Auto Review" in text:
            # 替换最新自动复盘块
            text = re.sub(r"## Auto Review.*?(?=\n## |\Z)", block.strip() + "\n", text, flags=re.DOTALL)
        else:
            text += block

        self.memory_path.write_text(text, encoding="utf-8")

    def run(self):
        actions = self.generate_actions()
        self.update_memory(actions)
        print("Self-improvement actions:")
        for a in actions:
            print(f" - {a}")


if __name__ == "__main__":
    runner = SelfImprovementRunner()
    runner.run()
