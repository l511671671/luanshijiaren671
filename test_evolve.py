"""Tests for evolve."""

from evolve import EvolveRunner


def test_evolve_run(tmp_path, monkeypatch):
    monkeypatch.setattr("evolve.ConnectorRunner", lambda: type("R", (), {"run": staticmethod(lambda names: []), "to_report": staticmethod(lambda x: {"success": True})})())
    monkeypatch.setattr("evolve.run_all_tests", lambda: {"success": True})

    runner = EvolveRunner(report_dir=tmp_path)
    report = runner.run()
    assert report["success"]
    assert "connectors" in report
    assert "tests" in report
