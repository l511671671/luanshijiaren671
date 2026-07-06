"""
WorkBuddy 多模型路由模块

根据 MODEL-STRATEGY.md 中的四层任务分级策略，
将用户请求路由到合适的模型，并提供 fallback 机制。

兼容独立运行与集成到 WorkBuddy 主程序。
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, List, Optional


class TaskTier(Enum):
    TIER_1_LIGHT = "tier_1_light"          # 轻量级：快速问答、格式转换
    TIER_2_STANDARD = "tier_2_standard"    # 标准：代码/文档生成
    TIER_3_COMPLEX = "tier_3_complex"      # 复杂：架构、多文件、深度推理
    TIER_4_VERIFY = "tier_4_verify"        # 验证/复核：高精度、细粒度检查


@dataclass
class ModelConfig:
    id: str
    name: str
    vendor: str
    tier: str  # light / standard / complex / verify
    supports_tools: bool = False
    supports_vision: bool = False
    supports_reasoning: bool = False
    reasoning_effort: Optional[str] = None  # low / medium / high / max
    fallback_order: int = 99
    # 成本与延迟用于二次排序，越小越优
    cost_index: int = 5
    latency_index: int = 5

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "vendor": self.vendor,
            "tier": self.tier,
            "supports_tools": self.supports_tools,
            "supports_vision": self.supports_vision,
            "supports_reasoning": self.supports_reasoning,
            "reasoning_effort": self.reasoning_effort,
            "fallback_order": self.fallback_order,
        }


@dataclass
class RouterResult:
    prompt: str
    tier: TaskTier
    selected: ModelConfig
    reasoning: str
    fallback_chain: List[ModelConfig] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "prompt": self.prompt,
            "tier": self.tier.value,
            "selected": self.selected.to_dict(),
            "reasoning": self.reasoning,
            "fallback_chain": [m.to_dict() for m in self.fallback_chain],
        }


# 内置关键词规则，用于将 prompt 快速映射到 Tier
TIER_KEYWORDS: Dict[TaskTier, List[str]] = {
    TaskTier.TIER_4_VERIFY: [
        "验证", "检查", "复核", "review", "audit", "排查", "回归",
        "verify", "check", "inspect", "proofread", "bug",
    ],
    TaskTier.TIER_3_COMPLEX: [
        "架构", "重构", "设计", "方案", "对比", "选型", "多文件",
        "长期任务", "跨会话", "checkpoint", "orchestrator", "规划",
        "architect", "redesign", "compare", "multi-step", "plan",
    ],
    TaskTier.TIER_2_STANDARD: [
        "写代码", "生成", "文档", "脚本", "模块", "组件",
        "code", "script", "module", "component", "document",
    ],
    TaskTier.TIER_1_LIGHT: [
        "摘要", "翻译", "格式化", "转换", "总结", "解释",
        "summarize", "translate", "format", "convert", "explain",
    ],
}


# 默认模型池，与 MODEL-STRATEGY.md 对齐
DEFAULT_MODELS: List[ModelConfig] = [
    ModelConfig(
        id="deepseek-v4-flash",
        name="DeepSeek-V4 Flash",
        vendor="DeepSeek",
        tier="standard",
        supports_tools=True,
        supports_reasoning=True,
        reasoning_effort="high",
        fallback_order=1,
        cost_index=1,
        latency_index=1,
    ),
    ModelConfig(
        id="deepseek-v4",
        name="DeepSeek-V4",
        vendor="DeepSeek",
        tier="complex",
        supports_tools=True,
        supports_reasoning=True,
        reasoning_effort="max",
        fallback_order=2,
        cost_index=3,
        latency_index=3,
    ),
    ModelConfig(
        id="deepseek-r1",
        name="DeepSeek-R1",
        vendor="DeepSeek",
        tier="verify",
        supports_tools=True,
        supports_reasoning=True,
        reasoning_effort="max",
        fallback_order=3,
        cost_index=4,
        latency_index=4,
    ),
    ModelConfig(
        id="qwen3-7b-light",
        name="Qwen3.7-Flash",
        vendor="Qwen",
        tier="light",
        supports_tools=False,
        supports_reasoning=False,
        reasoning_effort="low",
        fallback_order=4,
        cost_index=1,
        latency_index=1,
    ),
]


def classify_tier(prompt: str) -> TaskTier:
    """
    基于关键词启发式对 prompt 进行分级。
    命中高 Tier 关键词则直接返回；否则根据长度和结构判定。

    注意：复杂任务关键词（如 checkpoint/架构/规划）优先级高于通用
    验证词（如检查/复核），避免规划类任务被误判为验证任务。
    """
    prompt_lower = prompt.lower()

    # 1. 复杂任务关键词更具体，优先判断
    for tier in [TaskTier.TIER_3_COMPLEX]:
        if any(kw.lower() in prompt_lower for kw in TIER_KEYWORDS[tier]):
            return tier

    # 2. 验证、标准、轻量关键词
    for tier in [
        TaskTier.TIER_4_VERIFY,
        TaskTier.TIER_2_STANDARD,
    ]:
        if any(kw.lower() in prompt_lower for kw in TIER_KEYWORDS[tier]):
            return tier

    # 3. 长度和结构启发式
    if len(prompt) > 300 and ("\n" in prompt or "文件" in prompt):
        return TaskTier.TIER_3_COMPLEX

    if len(prompt) > 150:
        return TaskTier.TIER_2_STANDARD

    return TaskTier.TIER_1_LIGHT


def _tier_to_model_tier(tier: TaskTier) -> str:
    mapping = {
        TaskTier.TIER_1_LIGHT: "light",
        TaskTier.TIER_2_STANDARD: "standard",
        TaskTier.TIER_3_COMPLEX: "complex",
        TaskTier.TIER_4_VERIFY: "verify",
    }
    return mapping[tier]


def _select_primary_model(
    tier: TaskTier,
    models: List[ModelConfig],
) -> Optional[ModelConfig]:
    target_tier = _tier_to_model_tier(tier)

    # 精确 tier 匹配
    exact_matches = [m for m in models if m.tier == target_tier]
    if exact_matches:
        return sorted(exact_matches, key=lambda m: (m.fallback_order, m.cost_index))[0]

    # 向上兼容：复杂任务可降级到 standard，验证任务优先 complex
    if tier == TaskTier.TIER_4_VERIFY:
        candidates = [m for m in models if m.tier in ("complex", "standard")]
    elif tier == TaskTier.TIER_3_COMPLEX:
        candidates = [m for m in models if m.tier == "standard"]
    elif tier == TaskTier.TIER_2_STANDARD:
        candidates = [m for m in models if m.tier == "light"]
    else:
        candidates = models

    if candidates:
        return sorted(candidates, key=lambda m: (m.fallback_order, m.cost_index))[0]

    return models[0] if models else None


def _build_fallback_chain(
    selected: ModelConfig,
    tier: TaskTier,
    models: List[ModelConfig],
) -> List[ModelConfig]:
    """
    构建 fallback 链：同厂商其他模型 -> 不同厂商 -> 降 effort -> 提示用户
    """
    chain: List[ModelConfig] = []
    remaining = [m for m in models if m.id != selected.id]

    # 1) 同 tier 其他模型
    same_tier = [m for m in remaining if m.tier == selected.tier]
    chain.extend(sorted(same_tier, key=lambda m: (m.fallback_order, m.cost_index)))

    # 2) 更高 tier（更复杂）模型
    tier_order = ["light", "standard", "complex", "verify"]
    try:
        selected_idx = tier_order.index(selected.tier)
    except ValueError:
        selected_idx = -1

    higher = [m for m in remaining if tier_order.index(m.tier) > selected_idx]
    chain.extend(sorted(higher, key=lambda m: (tier_order.index(m.tier), m.fallback_order, m.cost_index)))

    # 3) 去重
    seen = set()
    unique_chain = []
    for m in chain:
        if m.id not in seen:
            seen.add(m.id)
            unique_chain.append(m)

    return unique_chain


class ModelRouter:
    def __init__(
        self,
        models: Optional[List[ModelConfig]] = None,
        classifier: Optional[Callable[[str], TaskTier]] = None,
    ):
        self.models = models if models is not None else DEFAULT_MODELS.copy()
        self.classifier = classifier or classify_tier

    def route(self, prompt: str) -> RouterResult:
        tier = self.classifier(prompt)
        selected = _select_primary_model(tier, self.models)
        if selected is None:
            raise ValueError("模型池为空，无法路由")

        reasoning = (
            f"请求命中 {tier.value}，"
            f"主模型选择 {selected.name}({selected.id})，"
            f"reasoning effort={selected.reasoning_effort or 'default'}"
        )

        fallback_chain = _build_fallback_chain(selected, tier, self.models)
        return RouterResult(
            prompt=prompt,
            tier=tier,
            selected=selected,
            reasoning=reasoning,
            fallback_chain=fallback_chain,
        )

    def route_with_fallback(
        self,
        prompt: str,
        attempt_results: Optional[List[str]] = None,
    ) -> RouterResult:
        """
        如果之前已经尝试过某些模型且失败，路由时会跳过这些模型。
        attempt_results: 已经失败的模型 id 列表
        """
        result = self.route(prompt)
        failed = set(attempt_results or [])
        result.fallback_chain = [
            m for m in result.fallback_chain if m.id not in failed
        ]
        return result


if __name__ == "__main__":
    import sys

    router = ModelRouter()

    if len(sys.argv) > 1:
        test_prompt = sys.argv[1]
    else:
        test_prompt = "帮我检查一下这份交易计划有没有问题"

    result = router.route(test_prompt)
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
