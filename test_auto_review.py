"""Tests for auto_review."""

import json
from pathlib import Path

import auto_review


def test_extract_tool_calls():
    text = "Use Bash.run\nThen Edit.write\nFinally Bash.run again"
    calls = auto_review.extract_tool_calls(text)
    assert calls == ["Bash.run", "Edit.write", "Bash.run"]


def test_extract_errors_and_corrections():
    text = "Traceback (most recent call last):\nValueError: failed\n不对，这里错了。"
    assert len(auto_review.extract_errors(text)) == 2
    assert len(auto_review.extract_corrections(text)) == 1


def test_review_text():
    review = auto_review.review_text("Bash.run command\n修正一下")
    assert review["tool_count"] == 1
    assert review["correction_count"] == 1
    assert review["suggested_rules"]


def test_write_daily_review(tmp_path):
    review = auto_review.review_text("Bash.run command\n修正一下")
    path = auto_review.write_daily_review(review, base_dir=tmp_path)
    assert path.exists()
    content = path.read_text(encoding="utf-8")
    assert "# 复盘" in content
    assert "Bash.run" in content


def test_format_memory_entry():
    review = auto_review.review_text("Bash.run command\n修正一下")
    entry = auto_review.format_memory_entry(review)
    assert "会话复盘" in entry
    assert "建议规则" in entry
