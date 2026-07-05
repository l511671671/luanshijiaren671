"""
Verified Orchestrator：推理-执行-验证-重试闭环

每个步骤执行后自动验证，不通过则重试，直到成功或达到最大重试次数。
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from .message_queue import Message
from .orchestrator import MultiAgentOrchestrator


class StepVerifier:
    """步骤结果验证器。未来可接入 LLM 做语义验证。"""

    def verify(self, step: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
        status = result.get("status")
        passed = status == "success"
        issues = []
        if not passed:
            issues.append(f"step returned status={status}")
        output = result.get("output")
        if output and isinstance(output, str) and len(output) < 5:
            issues.append("output too short")
            passed = False
        return {"passed": passed, "issues": issues}


class VerifiedOrchestrator(MultiAgentOrchestrator):
    """
    在 MultiAgentOrchestrator 基础上增加验证与重试。
    """

    def __init__(self, max_retries: int = 2):
        super().__init__()
        self.max_retries = max_retries
        self.verifier = StepVerifier()

    def run(self, task: str, handlers: Optional[Dict[str, Callable]] = None) -> Dict[str, Any]:
        if handlers:
            for action, func in handlers.items():
                self.executor.register_handler(action, func)

        plan = self.planner.run(task, executor_id=self.executor.agent_id)
        msg = self.queue.receive(self.executor.agent_id, timeout=0.5)
        if msg is None:
            raise RuntimeError("Executor did not receive plan message")

        # 逐个步骤执行并验证，失败则重试
        original_steps = list(msg.payload.get("steps", []))
        results = []
        for step in original_steps:
            result = self._execute_with_retry(step)
            results.append(result)

        # 覆盖 results
        self.executor.results = results
        self.queue.send(
            Message(
                sender=self.executor.agent_id,
                receiver="orchestrator",
                action="done",
                payload={"results": results},
            )
        )
        return {"task": task, "plan": plan, "results": results}

    def _execute_with_retry(self, step: Dict[str, Any]) -> Dict[str, Any]:
        for attempt in range(self.max_retries + 1):
            result = self.executor.execute_step(step)
            verification = self.verifier.verify(step, result)
            result["verification"] = verification
            if verification["passed"]:
                return result
            if attempt < self.max_retries:
                # 简单重试：下次尝试可能会成功
                continue
        return result
