"""
测试新增能力：Trace、Checkpoint、UsageTracker、ModelEval、Feedback
"""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, r"C:\Users\lu\.workbuddy")

import unittest

from tracer import Tracer
from checkpoint import CheckpointStore, Checkpoint, generate_task_id
from usage_tracker import UsageTracker
from model_eval import ModelEvaluator
from feedback import FeedbackCollector


class TestTracer(unittest.TestCase):
    def test_trace_save(self):
        tracer = Tracer()
        tracer.log("test.event", {"x": 1})
        with tracer.span("test.span"):
            pass
        path = tracer.save()
        self.assertTrue(path.exists())


class TestCheckpoint(unittest.TestCase):
    def test_save_load(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = CheckpointStore(tmp)
            cp = Checkpoint(
                task_id="abc",
                task="test task",
                status="running",
                steps_done=[{"step": 1}],
                steps_pending=[{"step": 2}],
            )
            store.save(cp)
            loaded = store.load("abc")
            self.assertEqual(loaded.task, "test task")
            self.assertEqual(len(loaded.steps_done), 1)

    def test_generate_task_id(self):
        tid = generate_task_id("hello")
        self.assertEqual(len(tid), 12)


class TestUsageTracker(unittest.TestCase):
    def test_log_and_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "usage.json"
            tracker = UsageTracker(str(path))
            tracker.log("m1", "tier_1_light", "hello")
            summary = tracker.summary()
            self.assertEqual(summary["total"], 1)


class TestModelEvaluator(unittest.TestCase):
    def test_evaluate(self):
        evaluator = ModelEvaluator()
        result = evaluator.evaluate("设计一个A股量化交易系统")
        self.assertIn("best_model", result)
        self.assertGreater(len(result["results"]), 0)


class TestFeedbackCollector(unittest.TestCase):
    def test_low_rating_creates_correction(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            collector = FeedbackCollector()
            collector.rule_updater.corrections_path = Path(tmp) / "corrections.md"
            record = collector.collect("task", "output", rating=2, correction="fix it")
            self.assertEqual(record["rating"], 2)
            self.assertTrue(collector.rule_updater.corrections_path.exists())


if __name__ == "__main__":
    unittest.main()
