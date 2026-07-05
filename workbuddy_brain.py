"""
WorkBuddy Brain — 统一入口

把以下能力串成一条链：
  1. 领域 Agent 识别
  2. 任务复杂度分级
  3. 多模型路由
  4. 长期记忆查询
  5. 复杂任务多 Agent 规划
  6. 调用 WorkBuddy CLI

用法：
  python workbuddy_brain.py "帮我设计一个A股量化交易系统"
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

WORKBUDDY_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(WORKBUDDY_DIR))

from agents.registry import AgentRegistry  # noqa: E402
from router.model_router import ModelRouter, ModelConfig  # noqa: E402
from tracer import Tracer  # noqa: E402
from usage_tracker import UsageTracker  # noqa: E402

ROUTING_CONFIG_PATH = WORKBUDDY_DIR / "model-routing.json"


class WorkBuddyBrain:
    def __init__(self):
        self.registry = AgentRegistry(str(WORKBUDDY_DIR / "agents"))
        self.router = self._build_router()
        self.routing_config = self._load_routing_config()
        self.tracer = Tracer()
        self.usage = UsageTracker()

    def _build_router(self):
        models = [
            ModelConfig(
                id="deepseek-v4-flash",
                name="DeepSeek-V4 Flash",
                vendor="DeepSeek",
                tier="standard",
                fallback_order=1,
            ),
            ModelConfig(
                id="deepseek-v4-pro",
                name="DeepSeek-V4 Pro",
                vendor="DeepSeek",
                tier="complex",
                fallback_order=2,
            ),
            ModelConfig(
                id="kimi-k2.7",
                name="Kimi-K2.7",
                vendor="Moonshot",
                tier="verify",
                fallback_order=3,
            ),
        ]
        return ModelRouter(models=models)

    def _load_routing_config(self) -> dict:
        with open(ROUTING_CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    def think(self, prompt: str) -> dict:
        """返回任务分析结果，但不执行 CLI。"""
        with self.tracer.span("brain.think") as span:
            # 1. 领域 Agent
            agents = self.registry.match(prompt, top_k=1)
            agent_id = agents[0].id if agents else "general"

            # 2. 任务复杂度
            route = self.router.route(prompt)
            tier = route.tier.value
            model_id = self.routing_config["tier_to_model"].get(tier, route.selected.id)
            fallbacks = self.routing_config["fallback_chain"].get(tier, [])
            fallbacks = [f for f in fallbacks if f != model_id]

            plan = {
                "prompt": prompt,
                "agent": agent_id,
                "tier": tier,
                "model": model_id,
                "fallback": fallbacks[:1],
            }
            self.tracer.log("brain.plan", plan)
            self.usage.log(model_id, tier, prompt, cost_index=route.selected.cost_index)
            return plan

    def run(self, prompt: str) -> str:
        plan = self.think(prompt)
        cli_path = self.routing_config.get("cli_path", "codebuddy")

        cmd = [cli_path, "--model", plan["model"]]
        if plan["fallback"]:
            cmd.extend(["--fallback-model", plan["fallback"][0]])
        cmd.extend(["-p", "--", prompt])

        # Windows 下 codebuddy 是 node 脚本
        if cli_path.lower().endswith("codebuddy") and not cli_path.lower().endswith((".exe", ".cmd", ".bat")):
            cmd.insert(0, "node")

        subprocess.run(cmd, check=True)
        return plan["model"]


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python workbuddy_brain.py <prompt>")
        sys.exit(1)

    prompt = sys.argv[1]
    brain = WorkBuddyBrain()
    plan = brain.think(prompt)
    print(json.dumps(plan, ensure_ascii=False, indent=2))
    print("--- executing ---")
    brain.run(prompt)
