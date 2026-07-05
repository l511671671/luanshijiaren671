"""
测试定时任务调度器
"""

import sys
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, r"C:\Users\lu\.workbuddy")

import scheduler


class TestScheduler(unittest.TestCase):
    def test_run_once_invokes_improve_and_regression(self):
        with patch("scheduler.subprocess.run") as mock_run:
            mock_proc = MagicMock()
            mock_proc.returncode = 0
            mock_proc.stdout = "ok"
            mock_proc.stderr = ""
            mock_run.return_value = mock_proc
            code = scheduler.run_once()
            self.assertEqual(code, 0)
            self.assertGreaterEqual(mock_run.call_count, 2)


if __name__ == "__main__":
    unittest.main()
