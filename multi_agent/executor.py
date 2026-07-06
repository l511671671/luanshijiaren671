"""
Executor Agent：执行 Planner 下发的步骤，并返回结果。
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List

from .message_queue import Message, MessageQueue


class ExecutorAgent:
    def __init__(
        self,
        agent_id: str = "executor",
        queue: MessageQueue = None,
        handlers: Dict[str, Callable] = None,
    ):
        self.agent_id = agent_id
        self.queue = queue or MessageQueue()
        self.queue.register(self.agent_id)
        self.handlers = handlers or {}
        self.results: List[Dict[str, Any]] = []

    def register_handler(self, action: str, func: Callable):
        self.handlers[action] = func

    def execute_step(self, step: Dict) -> Dict[str, Any]:
        action = step.get("action")
        handler = self.handlers.get(action)
        if handler:
            try:
                output = handler(step)
                return {"step": step, "status": "success", "output": output}
            except Exception as exc:
                return {"step": step, "status": "error", "output": str(exc)}
        return {"step": step, "status": "skipped", "output": f"no handler for {action}"}

    def run(self, plan_msg: Message) -> List[Dict[str, Any]]:
        steps = plan_msg.payload.get("steps", [])
        for step in steps:
            result = self.execute_step(step)
            self.results.append(result)

        # 通知 orchestrator 完成
        self.queue.send(
            Message(
                sender=self.agent_id,
                receiver="orchestrator",
                action="done",
                payload={"results": self.results},
            )
        )
        return self.results
