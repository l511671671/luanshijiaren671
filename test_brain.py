"""
测试 WorkBuddy Brain、Agent Registry、Memory Orchestrator
"""

import sys
import unittest

sys.path.insert(0, r"C:\Users\lu\.workbuddy")

from agents.registry import AgentRegistry
from workbuddy_brain import WorkBuddyBrain
from multi_agent.memory_orchestrator import MemoryOrchestrator


class TestAgentRegistry(unittest.TestCase):
    def test_match_trading(self):
        registry = AgentRegistry(r"C:\Users\lu\.workbuddy\agents")
        agents = registry.match("帮我看看这个股票")
        self.assertTrue(any(a.id == "trading-agent" for a in agents))

    def test_match_property(self):
        registry = AgentRegistry(r"C:\Users\lu\.workbuddy\agents")
        agents = registry.match("武汉光谷租金")
        self.assertTrue(any(a.id == "property-agent" for a in agents))


class TestWorkBuddyBrain(unittest.TestCase):
    def test_think_trading(self):
        brain = WorkBuddyBrain()
        plan = brain.think("帮我看看这个股票")
        self.assertEqual(plan["agent"], "trading-agent")
        self.assertIn(plan["tier"], ["tier_1_light", "tier_2_standard"])

    def test_think_marketing(self):
        brain = WorkBuddyBrain()
        plan = brain.think("写个营销方案")
        self.assertEqual(plan["agent"], "marketing-agent")


class TestMemoryOrchestrator(unittest.TestCase):
    def test_run_returns_result(self):
        orchestrator = MemoryOrchestrator()
        result = orchestrator.run("帮我写一个脚本")
        self.assertIn("results", result)
        self.assertIn("similar_past_tasks", result)


if __name__ == "__main__":
    unittest.main()
