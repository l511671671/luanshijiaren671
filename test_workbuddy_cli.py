"""
测试 WorkBuddy 统一入口 workbuddy.py
"""

import sys
import unittest

sys.path.insert(0, r"C:\Users\lu\.workbuddy")

import workbuddy


class TestWorkBuddyCLI(unittest.TestCase):
    def test_think_routes_trading(self):
        code = workbuddy.main(["think", "帮我看看这个股票"])
        self.assertEqual(code, 0)

    def test_agent_matches_trading(self):
        code = workbuddy.main(["agent", "帮我看看这个股票"])
        self.assertEqual(code, 0)

    def test_memory_search(self):
        code = workbuddy.main(["memory", "search", "主板股票"])
        self.assertEqual(code, 0)

    def test_plan_runs(self):
        code = workbuddy.main(["plan", "帮我写一个 Python 脚本读取 CSV"])
        self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
