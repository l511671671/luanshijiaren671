"""
模型 A/B 评估框架

对同一任务运行多个模型/路由策略，用质量门打分，输出最优选择。
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any, Dict, List

from meta_cognition import QualityGate


@dataclass
class EvalResult:
    model_id: str
    prompt: str
    output: str
    score: Dict[str, Any]
    duration_ms: float


class ModelEvaluator:
    """模拟模型调用与评估。未来可接入真实 LLM API。"""

    def __init__(self, models: List[str] = None):
        self.models = models or ["deepseek-v4-flash", "deepseek-v4-pro", "kimi-k2.7"]
        self.quality_gate = QualityGate()

    def call_model(self, model_id: str, prompt: str) -> str:
        """模拟模型输出，后续可替换为真实 API 调用。"""
        return f"[{model_id}] generated plan for: {prompt[:50]}..."

    def evaluate(self, prompt: str) -> Dict[str, Any]:
        results = []
        for model_id in self.models:
            start = time.time()
            output = self.call_model(model_id, prompt)
            duration_ms = (time.time() - start) * 1000
            score = self.quality_gate.verify_text(output)
            results.append(
                EvalResult(
                    model_id=model_id,
                    prompt=prompt,
                    output=output,
                    score=score,
                    duration_ms=duration_ms,
                )
            )

        best = max(results, key=lambda r: r.score["score"]["overall"])
        return {
            "prompt": prompt,
            "best_model": best.model_id,
            "results": [
                {
                    "model_id": r.model_id,
                    "score": r.score,
                    "duration_ms": r.duration_ms,
                    "output": r.output,
                }
                for r in results
            ],
        }


if __name__ == "__main__":
    evaluator = ModelEvaluator()
    print(json.dumps(evaluator.evaluate("设计一个A股量化交易系统"), ensure_ascii=False, indent=2))
