"""
WorkBuddy 新增模块测试

运行：
  python test_new_modules.py
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# 将 .workbuddy 加入路径，支持绝对导入
sys.path.insert(0, r"C:\Users\lu\.workbuddy")

from multi_agent import MessageQueue, PlannerAgent, ExecutorAgent, MultiAgentOrchestrator
from tools.web_client import WebClient, WebResponse
from tools.git_client import GitClient
from memory import ChromaMemory


class TestMessageQueue(unittest.TestCase):
    def test_send_and_receive(self):
        q = MessageQueue()
        q.send(MagicMock(sender="a", receiver="b", action="test", payload={}))
        msg = q.receive("b", timeout=1.0)
        self.assertIsNotNone(msg)

    def test_history(self):
        q = MessageQueue()
        m = MagicMock(sender="planner", receiver="executor", action="plan", payload={})
        q.send(m)
        self.assertEqual(len(q.history("planner")), 1)


class TestPlannerAgent(unittest.TestCase):
    def test_plan_returns_steps(self):
        agent = PlannerAgent()
        steps = agent.plan("帮我设计一个交易系统")
        self.assertGreater(len(steps), 0)
        self.assertIn("step", steps[0])

    def test_plan_routes_to_executor(self):
        agent = PlannerAgent()
        steps = agent.run("帮我写一个脚本")
        self.assertTrue(len(steps) > 0)


class TestExecutorAgent(unittest.TestCase):
    def test_execute_step_with_handler(self):
        executor = ExecutorAgent()
        executor.register_handler("echo", lambda s: "ok")
        result = executor.execute_step({"action": "echo"})
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["output"], "ok")

    def test_execute_step_no_handler(self):
        executor = ExecutorAgent()
        result = executor.execute_step({"action": "unknown"})
        self.assertEqual(result["status"], "skipped")


class TestOrchestrator(unittest.TestCase):
    def test_run_simple_task(self):
        orchestrator = MultiAgentOrchestrator()
        result = orchestrator.run("帮我写一个 Python 脚本")
        self.assertEqual(result["task"], "帮我写一个 Python 脚本")
        self.assertGreater(len(result["results"]), 0)


class TestWebClient(unittest.TestCase):
    @patch("tools.web_client.requests.Session.request")
    def test_get_ok(self, mock_request):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_response.text = '{"ok": true}'
        mock_response.json.return_value = {"ok": True}
        mock_response.elapsed.total_seconds.return_value = 0.1
        mock_request.return_value = mock_response

        client = WebClient()
        resp = client.get("https://example.com")
        self.assertTrue(resp.ok)
        self.assertEqual(resp.json_data, {"ok": True})


class TestGitClient(unittest.TestCase):
    @patch("tools.git_client.subprocess.run")
    def test_status(self, mock_run):
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = "M README.md"
        mock_proc.stderr = ""
        mock_run.return_value = mock_proc

        client = GitClient(repo_path=r"C:\\fake")
        result = client.status()
        self.assertTrue(result.ok)
        self.assertIn("README.md", result.stdout)


class TestChromaMemory(unittest.TestCase):
    def test_add_and_query(self):
        mem = ChromaMemory(collection_name="test")
        mem.add("A 股主板规则", {"domain": "trading"})
        mem.add("武汉光谷租金", {"domain": "property"})
        results = mem.query("主板股票")
        self.assertGreater(len(results), 0)
        # 最相关的结果应包含"主板"
        top = results[0]
        self.assertIn("主板", top["text"])


if __name__ == "__main__":
    unittest.main()
