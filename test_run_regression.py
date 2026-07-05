"""
测试回归测试运行器
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, r"C:\Users\lu\.workbuddy")

import run_regression


class TestRegressionRunner(unittest.TestCase):
    def test_discover_tests_finds_files(self):
        files = run_regression.discover_tests()
        self.assertTrue(any("test_brain.py" in f for f in files))
        self.assertTrue(any("test_new_modules.py" in f for f in files))

    def test_run_all_tests_success(self):
        report = run_regression.run_all_tests(["test_brain.py"])
        self.assertTrue(report["success"])
        self.assertEqual(report["total"], 1)
        self.assertEqual(report["failed"], 0)

    def test_html_report_generation(self):
        import tempfile
        report = run_regression.run_all_tests(["test_brain.py"])
        with tempfile.TemporaryDirectory() as tmp:
            html_path = Path(tmp) / "report.html"
            run_regression.generate_html(report, str(html_path))
            self.assertTrue(html_path.exists())
            self.assertIn("WorkBuddy Regression Report", html_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
