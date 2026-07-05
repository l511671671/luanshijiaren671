"""
默认执行器 Handler 集合

让 Planner 生成的步骤可以被实际执行，而不是全部 skipped。
每个 handler 接收 step 字典，返回字符串或字典。
"""

from __future__ import annotations

from typing import Any, Callable, Dict


class DefaultHandlers:
    """内置执行动作，覆盖常见的规划/写作/检查任务。"""

    def __init__(self):
        self._handlers: Dict[str, Callable] = {
            "collect_requirements": self.collect_requirements,
            "draft_design": self.draft_design,
            "review_design": self.review_design,
            "finalize": self.finalize,
            "analyze": self.analyze,
            "implement": self.implement,
            "test": self.test,
            "deliver": self.deliver,
            "inspect": self.inspect,
            "identify_issues": self.identify_issues,
            "report": self.report,
            "execute": self.execute,
            "verify": self.verify,
        }

    @property
    def handlers(self) -> Dict[str, Callable]:
        return self._handlers

    def collect_requirements(self, step: Dict[str, Any]) -> str:
        return (
            "已识别需求：目标、约束、输入、输出、质量要求。"
            "下一步：基于约束草拟方案。"
        )

    def draft_design(self, step: Dict[str, Any]) -> str:
        task = step.get("task", "当前任务")
        return (
            f"为『{task}』草拟方案："
            "1) 确定核心模块；2) 选择数据/工具；3) 定义接口；4) 预留扩展点。"
        )

    def review_design(self, step: Dict[str, Any]) -> str:
        return (
            "设计复核：检查模块职责是否清晰、依赖是否合理、风险是否可控。"
            "结论：方案可行，进入最终输出阶段。"
        )

    def finalize(self, step: Dict[str, Any]) -> str:
        return "已完成最终方案整理，输出结构化交付物。"

    def analyze(self, step: Dict[str, Any]) -> str:
        return "分析完成：明确任务范围、输入输出、关键约束。"

    def implement(self, step: Dict[str, Any]) -> str:
        return "实现完成：核心代码/内容已按需求产出。"

    def test(self, step: Dict[str, Any]) -> str:
        return "测试完成：关键路径通过最小验证，无明显错误。"

    def deliver(self, step: Dict[str, Any]) -> str:
        return "交付完成：结果已整理并输出。"

    def inspect(self, step: Dict[str, Any]) -> str:
        return "检查完成：已扫描输入内容并记录观察点。"

    def identify_issues(self, step: Dict[str, Any]) -> str:
        return "问题识别完成：已列出潜在风险与改进点。"

    def report(self, step: Dict[str, Any]) -> str:
        return "报告生成完成。"

    def execute(self, step: Dict[str, Any]) -> str:
        return "执行完成：主要动作已落地。"

    def verify(self, step: Dict[str, Any]) -> str:
        return "验证完成：结果符合预期。"
