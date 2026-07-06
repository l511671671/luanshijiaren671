"""Tests for project_context and git_workflow."""

from pathlib import Path

import project_context
import git_workflow


def test_project_context_loads_agents(tmp_path):
    (tmp_path / "AGENTS.md").write_text("# AGENTS\nRule 1", encoding="utf-8")
    (tmp_path / ".workbuddy_project").write_text("", encoding="utf-8")
    ctx = project_context.ProjectContext.from_path(tmp_path)
    assert "AGENTS.md" in ctx.files
    assert "Rule 1" in ctx.to_prompt_context()


def test_project_context_missing_files(tmp_path):
    ctx = project_context.ProjectContext.from_path(tmp_path)
    assert ctx.files == {}


def test_get_project_root(tmp_path):
    sub = tmp_path / "sub"
    sub.mkdir()
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    assert git_workflow.get_project_root(sub) == tmp_path


def test_workflow_result(tmp_path):
    wf = git_workflow.GitWorkflow(tmp_path)
    res = wf.run_tests()
    assert isinstance(res.success, bool)
