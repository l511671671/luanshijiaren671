"""Tests for smart_router."""

import json
from pathlib import Path

import smart_router
from router.model_router import ModelRouter


def test_compute_stats():
    records = [
        {"model_id": "a", "duration_ms": 100, "estimated_cost": 0.01, "success": True},
        {"model_id": "a", "duration_ms": 200, "estimated_cost": 0.02, "success": True},
        {"model_id": "b", "duration_ms": 50, "estimated_cost": 0.005, "success": False},
    ]
    stats = smart_router.compute_stats(records)
    assert "a" in stats
    assert stats["a"].avg_duration_ms == 150.0
    assert stats["b"].success_rate == 0.0


def test_smart_router_selects_cheaper(tmp_path):
    router = smart_router.SmartRouter(log_path=tmp_path / "usage.json")
    result = router.route("摘要")
    assert result.selected is not None
    assert "smart_router" in result.reasoning


def test_load_usage_records_empty(tmp_path):
    assert smart_router.load_usage_records(tmp_path / "missing.json") == []


def test_load_usage_records(tmp_path):
    path = tmp_path / "usage.json"
    path.write_text(json.dumps([{"model_id": "a"}], ensure_ascii=True), encoding="utf-8")
    assert smart_router.load_usage_records(path)
