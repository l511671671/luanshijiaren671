"""Tests for self_eval."""

import json

import self_eval


def test_score_output():
    review = {"error_count": 1, "correction_count": 2}
    debate = {"rounds": 1}
    scoring = self_eval.score_output(review, debate)
    assert 0 <= scoring["score"] <= 10
    assert "verdict" in scoring


def test_suggest_rules():
    review = {"suggested_rules": ["rule A"]}
    debate = {"transcript": [{"role": "Synthesizer", "content": "Improve X\nImprove Y"}]}
    rules = self_eval.suggest_rules(review, debate)
    assert "rule A" in rules
    assert any("Improve" in r for r in rules)


def test_evaluate_and_write(tmp_path):
    result = self_eval.evaluate("test prompt", "test output", "Bash.run")
    assert "scoring" in result
    assert "memory_entry" in result

    path = self_eval.write_daily_eval(result, base_dir=tmp_path)
    assert path.exists()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert len(data) == 1
