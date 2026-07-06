"""
测试 workbuddy_router 的模型选择逻辑
"""

import json
import os
import sys
import unittest

sys.path.insert(0, r"C:\Users\lu\.workbuddy")

from workbuddy_router import select_workbuddy_model, load_routing_config  # noqa: E402


class TestWorkBuddyRouter(unittest.TestCase):
    def test_load_routing_config(self):
        config = load_routing_config()
        self.assertIn("tier_to_model", config)
        self.assertIn("fallback_chain", config)

    def test_light_prompt(self):
        config = {
            "tier_to_model": {
                "tier_1_light": "deepseek-v4-flash",
                "tier_2_standard": "deepseek-v4-flash",
                "tier_3_complex": "deepseek-v4-pro",
                "tier_4_verify": "kimi-k2.7",
            },
            "fallback_chain": {
                "tier_1_light": ["deepseek-v4-flash"],
                "tier_2_standard": ["deepseek-v4-flash"],
                "tier_3_complex": ["deepseek-v4-pro", "deepseek-v4-flash"],
                "tier_4_verify": ["kimi-k2.7", "deepseek-v4-pro"],
            },
        }
        model_id, fallbacks, tier = select_workbuddy_model("hello", config)
        self.assertEqual(tier, "tier_1_light")
        self.assertEqual(model_id, "deepseek-v4-flash")

    def test_complex_prompt(self):
        config = {
            "tier_to_model": {
                "tier_1_light": "deepseek-v4-flash",
                "tier_2_standard": "deepseek-v4-flash",
                "tier_3_complex": "deepseek-v4-pro",
                "tier_4_verify": "kimi-k2.7",
            },
            "fallback_chain": {
                "tier_1_light": ["deepseek-v4-flash"],
                "tier_2_standard": ["deepseek-v4-flash"],
                "tier_3_complex": ["deepseek-v4-pro", "deepseek-v4-flash"],
                "tier_4_verify": ["kimi-k2.7", "deepseek-v4-pro"],
            },
        }
        model_id, fallbacks, tier = select_workbuddy_model("帮我设计一个交易系统", config)
        self.assertEqual(tier, "tier_3_complex")
        self.assertEqual(model_id, "deepseek-v4-pro")
        self.assertIn("deepseek-v4-flash", fallbacks)

    def test_verify_prompt(self):
        config = {
            "tier_to_model": {
                "tier_1_light": "deepseek-v4-flash",
                "tier_2_standard": "deepseek-v4-flash",
                "tier_3_complex": "deepseek-v4-pro",
                "tier_4_verify": "kimi-k2.7",
            },
            "fallback_chain": {
                "tier_1_light": ["deepseek-v4-flash"],
                "tier_2_standard": ["deepseek-v4-flash"],
                "tier_3_complex": ["deepseek-v4-pro", "deepseek-v4-flash"],
                "tier_4_verify": ["kimi-k2.7", "deepseek-v4-pro"],
            },
        }
        model_id, fallbacks, tier = select_workbuddy_model("检查代码", config)
        self.assertEqual(tier, "tier_4_verify")
        self.assertEqual(model_id, "kimi-k2.7")


if __name__ == "__main__":
    unittest.main()
