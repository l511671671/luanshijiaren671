"""
Agent Registry：根据用户 prompt 自动匹配领域专家 Agent。

读取 agents/*.md 中的 frontmatter / 关键词，返回最匹配的 Agent。
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class AgentSpec:
    id: str
    file_path: str
    trigger_words: List[str] = field(default_factory=list)
    description: str = ""


class AgentRegistry:
    def __init__(self, agents_dir: Optional[str] = None):
        self.agents_dir = Path(agents_dir) if agents_dir else Path(__file__).parent
        self._agents: List[AgentSpec] = []
        self._load()

    def _load(self):
        for md_file in self.agents_dir.glob("*.md"):
            if md_file.name == "README.md":
                continue
            spec = self._parse_agent(md_file)
            if spec:
                self._agents.append(spec)

    def _parse_agent(self, path: Path) -> Optional[AgentSpec]:
        text = path.read_text(encoding="utf-8")
        agent_id = path.stem
        trigger_words = []
        description = ""

        # 简单 frontmatter 解析
        if text.startswith("# "):
            title_line = text.splitlines()[0]
            description = title_line.lstrip("# ").strip()

        # 触发词：找 "触发词" / "触发场景" / "专长" 等段落后面的关键词
        for section in ["触发词", "触发场景", "核心关注", "专长", "Active Domains"]:
            pattern = rf"#+\s*{section}.*?(?=\n#+\s|\Z)"
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                section_text = match.group(0)
                # 提取所有顿号/逗号/换行分隔的短语
                words = re.split(r"[、,，\n]", section_text)
                for w in words:
                    w = w.strip(" -")
                    if w and len(w) >= 2:
                        trigger_words.append(w)

        # 兜底：根据 agent id 注入领域关键词
        fallback_keywords = {
            "trading-agent": ["股票", "交易", "A股", "买点", "止损", "复盘", "K线", "持仓", "通道", "轮动"],
            "property-agent": ["租房", "租客", "租金", "空置", "房产", "光谷", "房东", "物业"],
            "marketing-agent": ["营销", "推广", "文案", "招租", "活动", "渠道", "投放", "获客"],
        }
        trigger_words.extend(fallback_keywords.get(agent_id, []))

        return AgentSpec(
            id=agent_id,
            file_path=str(path),
            trigger_words=trigger_words,
            description=description,
        )

    def match(self, prompt: str, top_k: int = 1) -> List[AgentSpec]:
        prompt_lower = prompt.lower()
        scores: Dict[str, float] = {}
        for agent in self._agents:
            score = 0.0
            for word in agent.trigger_words:
                if word.lower() in prompt_lower:
                    score += 1.0
            if score > 0:
                scores[agent.id] = score

        ranked = sorted(
            [(aid, score) for aid, score in scores.items()],
            key=lambda x: x[1],
            reverse=True,
        )
        ids = {aid for aid, _ in ranked[:top_k]}
        return [a for a in self._agents if a.id in ids]

    def get(self, agent_id: str) -> Optional[AgentSpec]:
        for a in self._agents:
            if a.id == agent_id:
                return a
        return None


if __name__ == "__main__":
    registry = AgentRegistry()
    print(registry.match("帮我看看这个股票"))
