"""
Multi-Agent Orchestrator

协调 Planner 与 Executor，完成复杂任务。
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from .message_queue import MessageQueue
from .planner import PlannerAgent
from .executor import ExecutorAgent


class MultiAgentOrchestrator:
    def __init__(self):
        self.queue = MessageQueue()
        self.planner = PlannerAgent(queue=self.queue)
        self.executor = ExecutorAgent(queue=self.queue)

    def run(self, task: str, handlers: Optional[Dict[str, Callable]] = None) -> Dict[str, Any]:
        if handlers:
            for action, func in handlers.items():
                self.executor.register_handler(action, func)

        plan = self.planner.run(task, executor_id=self.executor.agent_id)
        # 在真实异步环境中，orchestrator 会监听消息队列
        # 这里为了可运行，直接调用 executor.run
        msg = self.queue.receive(self.executor.agent_id, timeout=0.5)
        if msg is None:
            raise RuntimeError("Executor did not receive plan message")
        results = self.executor.run(msg)
        return {"task": task, "plan": plan, "results": results}


if __name__ == "__main__":
    orchestrator = MultiAgentOrchestrator()
    result = orchestrator.run("帮我写一个 Python 脚本读取 CSV")
    print(result)
