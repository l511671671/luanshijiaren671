"""
成本/质量感知路由

基于 usage_tracker 的历史数据，动态调整模型选择。
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from router.model_router import ModelRouter, ModelConfig, RouterResult

USAGE_LOG_PATH = Path(__file__).resolve().parent / "usage-log.json"


@dataclass
class ModelStats:
    model_id: str
    count: int
    avg_duration_ms: float
    total_cost: float
    success_rate: float


def load_usage_records(log_path: Optional[Path] = None) -> List[Dict]:
    path = log_path or USAGE_LOG_PATH
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


def compute_stats(records: List[Dict]) -> Dict[str, ModelStats]:
    """按 model_id 聚合历史记录。"""
    buckets: Dict[str, List[Dict]] = {}
    for r in records:
        mid = r.get("model_id") or r.get("model", "unknown")
        buckets.setdefault(mid, []).append(r)

    stats = {}
    for mid, items in buckets.items():
        durations = [i.get("duration_ms", 0) for i in items if "duration_ms" in i]
        costs = [i.get("estimated_cost", 0) for i in items]
        successes = [i for i in items if i.get("success", True) is True]
        avg_duration = sum(durations) / len(durations) if durations else 0.0
        total_cost = sum(costs)
        success_rate = len(successes) / len(items) if items else 1.0
        stats[mid] = ModelStats(
            model_id=mid,
            count=len(items),
            avg_duration_ms=avg_duration,
            total_cost=total_cost,
            success_rate=success_rate,
        )
    return stats


def _score_model(model: ModelConfig, stats: Dict[str, ModelStats]) -> float:
    """分数越低越优。"""
    stat = stats.get(model.id)
    if stat:
        # 历史数据存在时，优先用历史表现
        cost_score = model.cost_index
        latency_score = model.latency_index
        if stat.avg_duration_ms > 0:
            latency_score = min(latency_score, stat.avg_duration_ms / 1000.0)
        if stat.total_cost > 0:
            cost_score = min(cost_score, stat.total_cost / stat.count * 1000)
        # 成功率越低惩罚越大
        return (cost_score + latency_score) / max(0.1, stat.success_rate)
    return model.cost_index + model.latency_index


class SmartRouter:
    def __init__(self, model_router: Optional[ModelRouter] = None, log_path: Optional[Path] = None):
        self.model_router = model_router or ModelRouter()
        self.log_path = log_path or USAGE_LOG_PATH

    def route(self, prompt: str) -> RouterResult:
        result = self.model_router.route(prompt)
        stats = compute_stats(load_usage_records(self.log_path))

        # 对主模型 + fallback 链按历史表现重新排序
        all_models = [result.selected] + result.fallback_chain
        scored = sorted(all_models, key=lambda m: _score_model(m, stats))

        if scored:
            result.selected = scored[0]
            result.fallback_chain = scored[1:]
            result.reasoning += (
                f"\n[smart_router] 基于 {len(stats)} 条历史记录重新排序，"
                f"首选 {result.selected.name}。"
            )
        return result

    def route_with_fallback(self, prompt: str, attempt_results: Optional[List[str]] = None) -> RouterResult:
        result = self.route(prompt)
        failed = set(attempt_results or [])
        result.fallback_chain = [m for m in result.fallback_chain if m.id not in failed]
        return result


def main(argv: list | None = None) -> int:
    import argparse
    import json

    parser = argparse.ArgumentParser(description="WorkBuddy Smart Router")
    parser.add_argument("prompt", help="用户请求")
    args = parser.parse_args(argv)

    router = SmartRouter()
    result = router.route(args.prompt)
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
