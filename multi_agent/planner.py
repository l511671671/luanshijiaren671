"""
Planner Agent：将用户请求拆解为可执行步骤。
"""

from __future__ import annotations

from typing import List

from .message_queue import Message, MessageQueue


class PlannerAgent:
    def __init__(self, agent_id: str = "planner", queue: MessageQueue = None):
        self.agent_id = agent_id
        self.queue = queue or MessageQueue()
        self.queue.register(self.agent_id)

    def plan(self, task: str, max_steps: int = 5) -> List[dict]:
        """
        简易规则化任务拆解。
        未来可接入 LLM 做智能规划。
        """
        steps = []
        lower = task.lower()

        if "设计" in task or "架构" in task or "方案" in task:
            steps = [
                {"step": 1, "action": "collect_requirements", "description": "收集需求和约束"},
                {"step": 2, "action": "draft_design", "description": "产出初步设计方案"},
                {"step": 3, "action": "review_design", "description": "内部复核设计"},
                {"step": 4, "action": "finalize", "description": "输出最终方案"},
            ]
        elif "写" in task or "生成" in task or "code" in lower:
            steps = [
                {"step": 1, "action": "analyze", "description": "分析任务和输入"},
                {"step": 2, "action": "implement", "description": "编写核心代码"},
                {"step": 3, "action": "test", "description": "运行最小验证"},
                {"step": 4, "action": "deliver", "description": "交付结果"},
            ]
        elif "检查" in task or "验证" in task or "review" in lower:
            steps = [
                {"step": 1, "action": "inspect", "description": "检查输入内容"},
                {"step": 2, "action": "identify_issues", "description": "识别问题"},
                {"step": 3, "action": "report", "description": "输出检查报告"},
            ]
        else:
            steps = [
                {"step": 1, "action": "analyze", "description": "分析任务"},
                {"step": 2, "action": "execute", "description": "执行主要动作"},
                {"step": 3, "action": "verify", "description": "验证结果"},
            ]

        return steps[:max_steps]

    def run(self, task: str, executor_id: str = "executor"):
        steps = self.plan(task)
        msg = Message(
            sender=self.agent_id,
            receiver=executor_id,
            action="plan",
            payload={"task": task, "steps": steps},
        )
        self.queue.send(msg)
        return steps
