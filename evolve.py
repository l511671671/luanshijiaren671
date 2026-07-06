"""
持续进化运行器

每日自动执行：
1. 运行外部连接器（行情、IM/邮件通知）
2. 清理长期未使用的 skill
3. 运行回归测试
4. 生成进化日报

用法：
    python evolve.py
    python workbuddy.py improve
"""

from __future__ import annotations

import argparse
import datetime
import json
from pathlib import Path
from typing import Any, Dict, List

from connectors import ConnectorRunner
from run_regression import run_all_tests
from skill_manager import SkillManager


WORKBUDDY_DIR = Path(__file__).resolve().parent


class EvolveRunner:
    def __init__(self, report_dir: Path | None = None):
        self.report_dir = report_dir or WORKBUDDY_DIR / "memory"
        self.report_dir.mkdir(parents=True, exist_ok=True)

    def run_connectors(self) -> Dict[str, Any]:
        runner = ConnectorRunner()
        results = runner.run(["a_stock_quote", "index_quote"])
        return runner.to_report(results)

    def prune_skills(self, days: int = 60) -> List[str]:
        manager = SkillManager()
        return manager.prune_candidates(days)

    def run_tests(self) -> Dict[str, Any]:
        return run_all_tests()

    def run(self, connector_days: int = 60) -> Dict[str, Any]:
        date_str = datetime.date.today().isoformat()
        report = {
            "date": date_str,
            "connectors": self.run_connectors(),
            "skill_prune": self.prune_skills(connector_days),
            "tests": self.run_tests(),
        }
        report["success"] = (
            report["connectors"].get("success", False)
            and report["tests"].get("success", False)
        )
        self._write(report)
        return report

    def _write(self, report: Dict[str, Any]) -> Path:
        path = self.report_dir / f"{report['date']}_evolve.json"
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        return path


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(description="WorkBuddy 持续进化")
    parser.add_argument("--days", type=int, default=60, help="skill 清理阈值")
    args = parser.parse_args(argv)

    runner = EvolveRunner()
    report = runner.run(args.days)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
