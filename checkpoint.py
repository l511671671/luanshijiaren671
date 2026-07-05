"""
WorkBuddy Checkpoint / 跨会话断点续作

复杂任务可保存进度，新会话启动时自动读取并续作。
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


WORKBUDDY_DIR = Path(__file__).resolve().parent
CHECKPOINTS_DIR = WORKBUDDY_DIR / "checkpoints"


@dataclass
class Checkpoint:
    task_id: str
    task: str
    status: str  # running / paused / completed / failed
    steps_done: List[Dict[str, Any]]
    steps_pending: List[Dict[str, Any]]
    context: Dict[str, Any] = field(default_factory=dict)
    updated_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "task": self.task,
            "status": self.status,
            "steps_done": self.steps_done,
            "steps_pending": self.steps_pending,
            "context": self.context,
            "updated_at": self.updated_at,
        }


class CheckpointStore:
    def __init__(self, checkpoints_dir: Optional[str] = None):
        self.dir = Path(checkpoints_dir) if checkpoints_dir else CHECKPOINTS_DIR
        self.dir.mkdir(parents=True, exist_ok=True)

    def _path(self, task_id: str) -> Path:
        return self.dir / f"{task_id}.json"

    def save(self, checkpoint: Checkpoint) -> str:
        checkpoint.updated_at = time.time()
        path = self._path(checkpoint.task_id)
        path.write_text(json.dumps(checkpoint.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        return str(path)

    def load(self, task_id: str) -> Optional[Checkpoint]:
        path = self._path(task_id)
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        return Checkpoint(**data)

    def list_active(self) -> List[Checkpoint]:
        active = []
        for path in self.dir.glob("*.json"):
            cp = self.load(path.stem)
            if cp and cp.status in ("running", "paused"):
                active.append(cp)
        return active

    def resume(self, task_id: str) -> Optional[Checkpoint]:
        cp = self.load(task_id)
        if cp:
            cp.status = "running"
            self.save(cp)
        return cp


def generate_task_id(task: str) -> str:
    import hashlib
    return hashlib.md5(f"{task}{time.time()}".encode("utf-8")).hexdigest()[:12]
