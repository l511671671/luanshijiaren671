"""
测试元认知层
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, r"C:\Users\lu\.workbuddy")

from meta_cognition import QualityGate, SessionReview, RuleUpdater


class TestQualityGate(unittest.TestCase):
    def test_short_text_fails(self):
        gate = QualityGate()
        result = gate.verify_text("short")
        self.assertFalse(result["passed"])
        self.assertIn("issues", result["score"])

    def test_good_text_passes(self):
        gate = QualityGate()
        text = (
            "This is a detailed and actionable plan for building a Python script. "
            "1. Open the source CSV file using pandas. "
            "2. Implement the parsing logic with proper error handling. "
            "3. Write unit tests to cover edge cases. "
            "Example code block: ```python import pandas as pd; df = pd.read_csv('data.csv')```. "
            "4. Run the script and verify the output matches expectations."
        )
        result = gate.verify_text(text)
        self.assertTrue(result["passed"])
        self.assertGreater(result["score"]["overall"], 0.0)

    def test_verify_missing_file(self):
        gate = QualityGate()
        result = gate.verify_file("/nonexistent/path/file.txt")
        self.assertFalse(result["passed"])
        self.assertIn("error", result)


class TestSessionReview(unittest.TestCase):
    def test_review_appends_memory(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "memory.md"
            review = SessionReview(str(path))
            record = review.review("test task", "1. step one\n2. step two", success=True)
            self.assertIn("quality", record)
            self.assertTrue(path.exists())
            content = path.read_text(encoding="utf-8")
            self.assertIn("test task", content)


class TestRuleUpdater(unittest.TestCase):
    def test_add_correction(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "corrections.md"
            updater = RuleUpdater()
            updater.corrections_path = path
            updater.add_correction("test issue", "test context")
            self.assertTrue(path.exists())
            content = path.read_text(encoding="utf-8")
            self.assertIn("test issue", content)


if __name__ == "__main__":
    unittest.main()
