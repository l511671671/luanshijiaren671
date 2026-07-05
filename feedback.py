"""
用户反馈与纠错自动沉淀

会话结束后收集满意度与纠正意见，自动写入 self-improving/corrections.md。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

WORKBUDDY_DIR = Path(__file__).resolve().parent

from meta_cognition import RuleUpdater  # noqa: E402


class FeedbackCollector:
    """收集用户反馈并沉淀为改进项。"""

    def __init__(self):
        self.rule_updater = RuleUpdater()

    def collect(
        self,
        task: str,
        output: str,
        rating: int,  # 1-5
        correction: str = "",
    ) -> Dict[str, any]:
        record = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "task": task,
            "output": output[:500],
            "rating": rating,
            "correction": correction,
        }
        if rating < 4 or correction:
            self.rule_updater.add_correction(
                issue=correction or f"user rating {rating}/5",
                context=task,
            )
        return record


if __name__ == "__main__":
    collector = FeedbackCollector()
    print(collector.collect("写个脚本", "print(1)", rating=2, correction="应该用 pandas"))
