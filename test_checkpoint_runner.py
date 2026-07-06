"""Tests for checkpoint_runner."""

from checkpoint_runner import CheckpointRunner


def test_create_and_resume(tmp_path):
    runner = CheckpointRunner()
    runner.store.dir = tmp_path
    cp = runner.create("test task", steps=[{"command": "echo hello"}])
    assert cp.status == "running"

    result = runner.resume(cp.task_id)
    assert result["success"]
    assert any("hello" in str(r) for r in result["results"])


def test_resume_not_found(tmp_path):
    runner = CheckpointRunner()
    runner.store.dir = tmp_path
    result = runner.resume("missing")
    assert not result["success"]
