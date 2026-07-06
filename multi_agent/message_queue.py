"""
简单内存消息队列，用于 Planner 与 Executor 之间通信。
生产环境可替换为 Redis / RabbitMQ。
"""

from __future__ import annotations

import queue
import threading
import time
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional
from uuid import uuid4


@dataclass
class Message:
    sender: str
    receiver: str
    action: str  # e.g. plan, execute, done, error
    payload: Dict = field(default_factory=dict)
    msg_id: str = field(default_factory=lambda: str(uuid4())[:8])
    timestamp: float = field(default_factory=time.time)


class MessageQueue:
    def __init__(self):
        self._lock = threading.Lock()
        self._queues: Dict[str, queue.Queue] = {}
        self._history: List[Message] = []

    def register(self, agent_id: str):
        with self._lock:
            if agent_id not in self._queues:
                self._queues[agent_id] = queue.Queue()

    def send(self, msg: Message):
        self.register(msg.receiver)
        with self._lock:
            self._queues[msg.receiver].put(msg)
            self._history.append(msg)

    def receive(self, agent_id: str, timeout: Optional[float] = None) -> Optional[Message]:
        self.register(agent_id)
        try:
            return self._queues[agent_id].get(timeout=timeout)
        except queue.Empty:
            return None

    def history(self, sender: Optional[str] = None) -> List[Message]:
        with self._lock:
            if sender is None:
                return list(self._history)
            return [m for m in self._history if m.sender == sender]
