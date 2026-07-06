"""Tests for connectors."""

from connectors import ConnectorRunner, IMConnector, CalendarConnector, EmailConnector
from connectors.base import ConnectorResult


def test_im_connector():
    conn = IMConnector({"message": "hello"})
    result = conn.run()
    assert result.success
    assert "hello" in result.output


def test_runner_unknown():
    runner = ConnectorRunner()
    results = runner.run(["unknown"])
    assert len(results) == 1
    assert not results[0].success


def test_runner_all_stubs():
    runner = ConnectorRunner()
    results = runner.run(["im", "calendar", "email"])
    assert all(r.success for r in results)
