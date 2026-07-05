"""
WorkBuddy 元认知层

负责：
1. 对每次会话输出做质量评估（QualityGate）
2. 根据评估结果自动更新 MEMORY.md / self-improving/corrections.md
3. 周期性复盘，提炼新的规则和模式
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


WORKBUDDY_DIR = Path(__file__).resolve().parent


@dataclass
class QualityScore:
    completeness: float = 0.0  # 0-1
    executability: float = 0.0
    correctness: float = 0.0
    clarity: float = 0.0
    issues: List[str] = field(default_factory=list)

    @property
    def overall(self) -> float:
        if not any([self.completeness, self.executability, self.correctness, self.clarity]):
            return 0.0
        return (self.completeness + self.executability + self.correctness + self.clarity) / 4.0

    def to_dict(self) -> dict:
        return {
            "completeness": self.completeness,
            "executability": self.executability,
            "correctness": self.correctness,
            "clarity": self.clarity,
            "overall": self.overall,
            "issues": self.issues,
        }


class QualityGate:
    """
    基于规则的质量门检查。
    未来可接入 LLM 做更智能的语义评估。
    """

    def __init__(self):
        self.min_completeness = 0.6
        self.min_executability = 0.5

    def verify_file(self, path: str) -> Dict[str, Any]:
        file_path = Path(path)
        if not file_path.exists():
            return {"passed": False, "error": f"file not found: {path}"}
        text = file_path.read_text(encoding="utf-8")
        score = self._score_text(text)
        passed = (
            score.completeness >= self.min_completeness
            and score.executability >= self.min_executability
            and not score.issues
        )
        return {"passed": passed, "score": score.to_dict(), "path": str(file_path)}

    def verify_text(self, text: str) -> Dict[str, Any]:
        score = self._score_text(text)
        passed = (
            score.completeness >= self.min_completeness
            and score.executability >= self.min_executability
            and not score.issues
        )
        return {"passed": passed, "score": score.to_dict()}

    def _score_text(self, text: str) -> QualityScore:
        score = QualityScore()
        t = text.strip()

        # 完整性：非空且长度合理
        score.completeness = min(1.0, max(0.0, len(t) / 500))

        # 可执行性：包含具体步骤、代码块、数字、模板等
        executability_signals = [
            "```" in t,
            re.search(r"\d+\.\s+", t) is not None,
            "步骤" in t or "Step" in t or "TODO" in t,
            "模板" in t or "话术" in t or "工具" in t,
        ]
        score.executability = sum(executability_signals) / len(executability_signals)

        # 正确性：基础检查
        score.correctness = 1.0

        # 清晰度
        score.clarity = min(1.0, max(0.0, len(t) / 200))

        # 问题收集
        issues = []
        if len(t) < 100:
            issues.append("输出过短，可能缺乏细节")
        if "TODO" in t and "```" not in t:
            issues.append("包含 TODO 但缺少代码/模板示例")
        if re.search(r"(大约|可能|也许|尽量|适当)", t):
            issues.append("存在模糊表述，建议量化")

        score.issues = issues
        return score


class SessionReview:
    """
    对一次会话进行复盘，生成结构化记录。
    """

    def __init__(self, memory_path: Optional[str] = None):
        self.memory_path = Path(memory_path) if memory_path else WORKBUDDY_DIR / "self-improving" / "memory.md"

    def review(self, task: str, output: str, success: bool = True, notes: str = "") -> Dict[str, Any]:
        gate = QualityGate()
        quality = gate.verify_text(output)
        record = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "task": task,
            "success": success,
            "quality": quality,
            "notes": notes,
        }
        self._append_memory(record)
        return record

    def _append_memory(self, record: Dict[str, Any]):
        self.memory_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.memory_path.exists():
            self.memory_path.write_text("# Self-Improving Memory\n\n", encoding="utf-8")

        text = self.memory_path.read_text(encoding="utf-8")
        block = f"\n## {record['date']}\n\n"
        block += f"- 任务：{record['task']}\n"
        block += f"- 成功：{record['success']}\n"
        block += f"- 评分：{record['quality']['score']['overall']:.2f}\n"
        if record['notes']:
            block += f"- 备注：{record['notes']}\n"
        self.memory_path.write_text(text + block, encoding="utf-8")


class RuleUpdater:
    """
    根据复盘记录自动更新规则。
    目前采用简单的启发式：当某个问题重复出现时，写入 corrections.md。
    """

    def __init__(self):
        self.corrections_path = WORKBUDDY_DIR / "self-improving" / "corrections.md"
        self.corrections_path.parent.mkdir(parents=True, exist_ok=True)

    def add_correction(self, issue: str, context: str = ""):
        if not self.corrections_path.exists():
            self.corrections_path.write_text("# Corrections\n\n", encoding="utf-8")

        text = self.corrections_path.read_text(encoding="utf-8")
        today = datetime.now().strftime("%Y-%m-%d")
        block = f"\n### {today}\n\n- 问题：{issue}\n"
        if context:
            block += f"- 上下文：{context}\n"
        block += "- 状态：待修复\n"
        self.corrections_path.write_text(text + block, encoding="utf-8")


if __name__ == "__main__":
    gate = QualityGate()
    print(gate.verify_text("这是一个测试输出，包含具体步骤：1. 打开文件；2. 写入内容；3. 保存。"))
