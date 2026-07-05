"""
WorkBuddy 定时自改进调度器

支持两种方式：
1. 立即运行一次
2. 在 Windows 任务计划程序中注册每日定时任务

用法：
  python scheduler.py run-once
  python scheduler.py install --hour 9 --minute 0
  python scheduler.py uninstall
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


WORKBUDDY_DIR = Path(__file__).resolve().parent
PYTHON = sys.executable
TASK_NAME = "WorkBuddySelfImprovement"


def run_once() -> int:
    print("[Scheduler] Running self-improvement tasks...")
    result = subprocess.run(
        [PYTHON, str(WORKBUDDY_DIR / "workbuddy.py"), "improve"],
        cwd=str(WORKBUDDY_DIR),
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)

    print("[Scheduler] Running regression tests...")
    result2 = subprocess.run(
        [PYTHON, str(WORKBUDDY_DIR / "run_regression.py")],
        cwd=str(WORKBUDDY_DIR),
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    print(result2.stdout)
    if result2.stderr:
        print(result2.stderr, file=sys.stderr)

    return 0 if result.returncode == 0 and result2.returncode == 0 else 1


def install_task(hour: int, minute: int) -> int:
    if sys.platform != "win32":
        print("[Scheduler] install is only supported on Windows. Use cron on Linux/macOS.")
        return 1

    action = f'{PYTHON} "{WORKBUDDY_DIR / "scheduler.py"}" run-once'
    cmd = [
        "schtasks",
        "/Create",
        "/F",
        "/TN", TASK_NAME,
        "/TR", action,
        "/SC", "DAILY",
        "/ST", f"{hour:02d}:{minute:02d}",
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True, encoding="utf-8")
        print(f"[Scheduler] Installed daily task '{TASK_NAME}' at {hour:02d}:{minute:02d}")
        return 0
    except subprocess.CalledProcessError as exc:
        print(f"[Scheduler] Failed to install task: {exc.stderr}")
        return 1


def uninstall_task() -> int:
    if sys.platform != "win32":
        print("[Scheduler] uninstall is only supported on Windows.")
        return 1
    try:
        subprocess.run(["schtasks", "/Delete", "/F", "/TN", TASK_NAME], check=True, capture_output=True, text=True, encoding="utf-8")
        print(f"[Scheduler] Removed task '{TASK_NAME}'")
        return 0
    except subprocess.CalledProcessError as exc:
        print(f"[Scheduler] Failed to remove task: {exc.stderr}")
        return 1


def main():
    parser = argparse.ArgumentParser(description="WorkBuddy scheduled self-improvement")
    sub = parser.add_subparsers(dest="command", required=True)

    p_run = sub.add_parser("run-once", help="立即运行一次自改进流程")
    p_run.set_defaults(func=lambda _: run_once())

    p_install = sub.add_parser("install", help="注册 Windows 定时任务")
    p_install.add_argument("--hour", type=int, default=9, help="小时")
    p_install.add_argument("--minute", type=int, default=0, help="分钟")
    p_install.set_defaults(func=lambda args: install_task(args.hour, args.minute))

    p_uninstall = sub.add_parser("uninstall", help="移除 Windows 定时任务")
    p_uninstall.set_defaults(func=lambda _: uninstall_task())

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
