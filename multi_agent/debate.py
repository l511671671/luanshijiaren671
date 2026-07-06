"""
多 Agent 质量辩论

通过 Critic / RedTeam / Verifier / Synthesizer 对初稿进行多轮审视，
最终输出更可靠的答案。
"""

from __future__ import annotations

import os
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional


class LLMBackend(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> str:
        ...


class EchoBackend(LLMBackend):
    """默认占位 backend，用于测试和无 LLM 环境。"""

    def generate(self, prompt: str) -> str:
        return f"[echo] {prompt[:80]}..."


class CodeBuddyBackend(LLMBackend):
    """调用 WorkBuddy CLI 的 LLM backend。"""

    def __init__(self, model: str = "deepseek-v4-flash", timeout: int = 120):
        self.model = model
        self.timeout = timeout

    def generate(self, prompt: str) -> str:
        cli = "codebuddy"
        # Windows 下 codebuddy 是 node 脚本
        import sys

        if sys.platform == "win32" and not cli.endswith(('.exe', '.cmd', '.bat')):
            cmd = ["node", cli, "--model", self.model, "-p", "--", prompt]
        else:
            cmd = [cli, "--model", self.model, "-p", "--", prompt]
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=self.timeout,
            )
            if proc.returncode == 0:
                return proc.stdout.strip()
            return f"[codebuddy error: {proc.stderr.strip()[:200]}]"
        except Exception as exc:  # pragma: no cover
            return f"[codebuddy failed: {exc}]"


def get_default_backend() -> LLMBackend:
    if os.environ.get("WORKBUDDY_DEBATE_LLM"):
        return CodeBuddyBackend()
    return EchoBackend()


@dataclass
class DebateMessage:
    role: str
    content: str


class DebateAgent:
    def __init__(self, role: str, system_prompt: str, backend: LLMBackend):
        self.role = role
        self.system_prompt = system_prompt
        self.backend = backend

    def respond(self, prompt: str, context: List[DebateMessage]) -> str:
        parts = [f"{m.role}: {m.content}" for m in context]
        parts.append(f"user: {prompt}")
        parts.append(f"{self.role}: 请你以 {self.system_prompt} 的角度审视并给出意见。")
        full_prompt = "\n".join(parts)
        return self.backend.generate(full_prompt)


class CriticAgent(DebateAgent):
    def __init__(self, backend: LLMBackend):
        super().__init__("Critic", "找出方案中的缺陷、遗漏和潜在风险", backend)


class RedTeamAgent(DebateAgent):
    def __init__(self, backend: LLMBackend):
        super().__init__("RedTeam", "站在反对/攻击角度，挑战方案的假设和结论", backend)


class VerifierAgent(DebateAgent):
    def __init__(self, backend: LLMBackend):
        super().__init__("Verifier", "验证方案是否满足原始需求，并检查事实准确性", backend)


class SynthesizerAgent(DebateAgent):
    def __init__(self, backend: LLMBackend):
        super().__init__("Synthesizer", "整合各方意见，输出最终经过权衡的答案", backend)


class DebateOrchestrator:
    def __init__(self, backend: Optional[LLMBackend] = None):
        self.backend = backend or get_default_backend()
        self.critic = CriticAgent(self.backend)
        self.red_team = RedTeamAgent(self.backend)
        self.verifier = VerifierAgent(self.backend)
        self.synthesizer = SynthesizerAgent(self.backend)

    def run(self, prompt: str, draft: Optional[str] = None, rounds: int = 2) -> Dict:
        if draft is None:
            draft = f"[初始方案] {prompt}"

        context: List[DebateMessage] = [DebateMessage("Initial", draft)]
        transcript: List[Dict] = [{"role": "Initial", "content": draft}]

        for round_idx in range(1, rounds + 1):
            for agent, name in [
                (self.critic, "Critic"),
                (self.red_team, "RedTeam"),
                (self.verifier, "Verifier"),
            ]:
                content = agent.respond(prompt, context)
                msg = DebateMessage(name, content)
                context.append(msg)
                transcript.append({"round": round_idx, "role": name, "content": content})

        final = self.synthesizer.respond(prompt, context)
        transcript.append({"role": "Synthesizer", "content": final})

        return {
            "prompt": prompt,
            "rounds": rounds,
            "transcript": transcript,
            "final_answer": final,
        }


if __name__ == "__main__":
    orchestrator = DebateOrchestrator()
    result = orchestrator.run("帮我设计一个A股量化交易系统", rounds=1)
    import json
    print(json.dumps(result, ensure_ascii=False, indent=2))
