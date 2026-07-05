"""
WorkBuddy 自动化回归测试

运行所有测试文件，生成结构化报告：

  python run_regression.py
  python run_regression.py --html report.html
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


WORKBUDDY_DIR = Path(__file__).resolve().parent


@dataclass
class RegressionReport:
    timestamp: str
    total: int = 0
    passed: int = 0
    failed: int = 0
    errors: int = 0
    duration_ms: float = 0.0
    suites: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "total": self.total,
            "passed": self.passed,
            "failed": self.failed,
            "errors": self.errors,
            "duration_ms": self.duration_ms,
            "success": self.failed == 0 and self.errors == 0,
            "suites": self.suites,
        }


def discover_tests() -> list[str]:
    test_files = []
    for f in WORKBUDDY_DIR.glob("test_*.py"):
        test_files.append(str(f.name))
    return sorted(test_files)


def run_test_file(file_name: str) -> dict:
    file_path = WORKBUDDY_DIR / file_name
    start = time.time()
    try:
        result = subprocess.run(
            [sys.executable, str(file_path)],
            cwd=str(WORKBUDDY_DIR),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        elapsed = (time.time() - start) * 1000
        return {
            "name": file_name,
            "returncode": result.returncode,
            "passed": result.returncode == 0,
            "stdout": _sanitize((result.stdout or "")[-500:]),
            "stderr": _sanitize((result.stderr or "")[-500:]),
            "duration_ms": elapsed,
        }
    except Exception as exc:
        return {
            "name": file_name,
            "returncode": -1,
            "passed": False,
            "stdout": "",
            "stderr": f"runner exception: {exc}\n{traceback.format_exc()}",
            "duration_ms": (time.time() - start) * 1000,
        }


def _sanitize(text: str) -> str:
    """移除或替换无法在当前终端编码中输出的字符。"""
    text = text.encode("utf-8", errors="replace").decode("utf-8", errors="replace")
    return text.replace("\ufffd", "?")


def run_all_tests(test_files: list[str] | None = None) -> dict:
    files = test_files or discover_tests()
    report = RegressionReport(timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    start_all = time.time()

    for f in files:
        suite = run_test_file(f)
        report.suites.append(suite)
        if suite["passed"]:
            report.passed += 1
        else:
            report.failed += 1

    report.total = len(files)
    report.duration_ms = (time.time() - start_all) * 1000
    return report.to_dict()


def generate_html(report: dict, output_path: str):
    rows = ""
    for suite in report["suites"]:
        status = "<span style='color:green'>PASS</span>" if suite["passed"] else "<span style='color:red'>FAIL</span>"
        rows += f"<tr><td>{suite['name']}</td><td>{status}</td><td>{suite['duration_ms']:.1f} ms</td></tr>"

    html = f"""
<!DOCTYPE html>
<html>
<head><title>WorkBuddy Regression Report</title></head>
<body>
<h1>WorkBuddy Regression Report</h1>
<p>Timestamp: {report['timestamp']}</p>
<p>Total: {report['total']} | Passed: {report['passed']} | Failed: {report['failed']}</p>
<table border="1" cellpadding="5">
<tr><th>Suite</th><th>Status</th><th>Duration</th></tr>
{rows}
</table>
</body>
</html>
"""
    Path(output_path).write_text(html, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="WorkBuddy regression runner")
    parser.add_argument("--html", help="生成 HTML 报告路径")
    parser.add_argument("--json", dest="json_path", help="生成 JSON 报告路径")
    args = parser.parse_args()

    report = run_all_tests()
    # Use ASCII-escaped JSON for terminal output to avoid GBK encoding errors on Windows
    print(json.dumps(report, ensure_ascii=True, indent=2))

    if args.json_path:
        Path(args.json_path).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.html:
        generate_html(report, args.html)
        print(f"[Regression] HTML report written to {args.html}")

    return 0 if report["success"] else 1


if __name__ == "__main__":
    sys.exit(main())
