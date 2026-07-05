"""
WorkBuddy 用量与成本追踪

记录每次路由/调用使用的模型、耗时、估算成本，用于后续路由优化。
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional


WORKBUDDY_DIR = Path(__file__).resolve().parent
USAGE_LOG_PATH = WORKBUDDY_DIR / "usage-log.json"


@dataclass
class UsageRecord:
    model_id: str
    tier: str
    prompt: str
    start_time: float
    end_time: float
    cost_index: int = 5

    @property
    def duration_ms(self) -> float:
        return (self.end_time - self.start_time) * 1000

    @property
    def estimated_cost(self) -> float:
        """简单估算成本：cost_index * 0.001 美元。"""
        return self.cost_index * 0.001

    def to_dict(self) -> Dict[str, any]:
        return {
            "model_id": self.model_id,
            "tier": self.tier,
            "prompt": self.prompt,
            "duration_ms": self.duration_ms,
            "estimated_cost": self.estimated_cost,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }


class UsageTracker:
    def __init__(self, log_path: Optional[str] = None):
        self.log_path = Path(log_path) if log_path else USAGE_LOG_PATH

    def log(self, model_id: str, tier: str, prompt: str, cost_index: int = 5) -> UsageRecord:
        now = time.time()
        record = UsageRecord(
            model_id=model_id,
            tier=tier,
            prompt=prompt,
            start_time=now,
            end_time=now,
            cost_index=cost_index,
        )
        self._append(record.to_dict())
        return record

    def mark_end(self, record: UsageRecord):
        record.end_time = time.time()
        self._append(record.to_dict())

    def _append(self, data: Dict[str, any]):
        records = []
        if self.log_path.exists():
            try:
                loaded = json.loads(self.log_path.read_text(encoding="utf-8"))
                if isinstance(loaded, list):
                    records = loaded
            except Exception:
                pass
        records.append(data)
        self.log_path.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")

    def summary(self) -> Dict[str, any]:
        if not self.log_path.exists():
            return {"total": 0, "cost": 0.0, "avg_duration_ms": 0.0}
        records = json.loads(self.log_path.read_text(encoding="utf-8"))
        total_cost = sum(r.get("estimated_cost", 0) for r in records)
        durations = [r.get("duration_ms", 0) for r in records if "duration_ms" in r]
        avg_duration = sum(durations) / len(durations) if durations else 0.0
        return {
            "total": len(records),
            "cost": round(total_cost, 4),
            "avg_duration_ms": round(avg_duration, 2),
        }
