"""
增强版 Orchestrator：集成长期记忆。

在规划前查询相似经验，执行后把成功方案写入记忆。
"""

from __future__ import annotations

import sys
from typing import Any, Callable, Dict, List, Optional

from .orchestrator import MultiAgentOrchestrator

WORKBUDDY_DIR = __import__("os").path.dirname(__import__("os").path.dirname(__file__))
sys.path.insert(0, WORKBUDDY_DIR)

try:
    from memory import ChromaMemory
    HAS_MEMORY = True
except ImportError:
    HAS_MEMORY = False

from .handlers import DefaultHandlers


class MemoryOrchestrator(MultiAgentOrchestrator):
    def __init__(self, memory: Optional[Any] = None):
        super().__init__()
        self.memory = memory
        if self.memory is None and HAS_MEMORY:
            self.memory = ChromaMemory(collection_name="workbuddy_tasks")

        # 注册默认执行 handler，避免所有 step 都被 skipped
        default_handlers = DefaultHandlers()
        for action, handler in default_handlers.handlers.items():
            self.executor.register_handler(action, handler)

    def run(self, task: str, handlers: Optional[Dict[str, Callable]] = None) -> Dict[str, Any]:
        # 1. 检索相似历史任务
        similar = []
        if self.memory:
            try:
                similar = self.memory.query(task, n_results=2)
            except Exception:
                similar = []

        # 2. 父类执行规划
        result = super().run(task, handlers=handlers)

        # 3. 写入成功记忆
        if self.memory:
            try:
                self.memory.add(
                    text=task,
                    metadata={
                        "plan": str(result.get("plan")),
                        "success": all(r.get("status") == "success" for r in result.get("results", [])),
                    },
                )
            except Exception:
                pass

        result["similar_past_tasks"] = similar
        return result


if __name__ == "__main__":
    orchestrator = MemoryOrchestrator()
    result = orchestrator.run("帮我写一个 Python 脚本")
    print(result)
