"""
WorkBuddy Trace / 可观测性

每个请求、路由、工具调用、错误都写入 trace，方便复盘和优化。
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


WORKBUDDY_DIR = Path(__file__).resolve().parent
TRACES_DIR = WORKBUDDY_DIR / "traces"


@dataclass
class TraceEvent:
    name: str
    timestamp: float
    duration_ms: float
    status: str = "ok"
    payload: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


class Tracer:
    """单次请求的 trace 记录器。"""

    def __init__(self, trace_id: Optional[str] = None):
        self.trace_id = trace_id or str(uuid.uuid4())
        self.events: List[TraceEvent] = []
        self.started_at = time.time()
        self.traces_dir = TRACES_DIR
        self.traces_dir.mkdir(parents=True, exist_ok=True)

    def log(self, name: str, payload: Optional[Dict[str, Any]] = None):
        self.events.append(
            TraceEvent(
                name=name,
                timestamp=time.time(),
                duration_ms=0.0,
                payload=payload or {},
            )
        )

    def span(self, name: str):
        return _TraceSpan(self, name)

    def record_error(self, name: str, exc: Exception, payload: Optional[Dict[str, Any]] = None):
        self.events.append(
            TraceEvent(
                name=name,
                timestamp=time.time(),
                duration_ms=0.0,
                status="error",
                payload=payload or {},
                error=str(exc),
            )
        )

    def save(self):
        duration_ms = (time.time() - self.started_at) * 1000
        data = {
            "trace_id": self.trace_id,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "duration_ms": duration_ms,
            "events": [
                {
                    "name": e.name,
                    "timestamp": e.timestamp,
                    "duration_ms": e.duration_ms,
                    "status": e.status,
                    "payload": e.payload,
                    "error": e.error,
                }
                for e in self.events
            ],
        }
        path = self.traces_dir / f"{self.trace_id}.json"
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return path


class _TraceSpan:
    def __init__(self, tracer: Tracer, name: str):
        self.tracer = tracer
        self.name = name
        self.start = None

    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (time.time() - self.start) * 1000 if self.start else 0.0
        event = TraceEvent(
            name=self.name,
            timestamp=time.time(),
            duration_ms=duration,
            status="error" if exc_val else "ok",
            error=str(exc_val) if exc_val else None,
        )
        self.tracer.events.append(event)
