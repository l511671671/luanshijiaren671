"""
WorkBuddy Git 工具客户端

使用 subprocess 调用本地 git，支持常见的仓库操作。
所有危险操作默认只读，写操作需要显式启用。
"""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class GitResult:
    returncode: int
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        return self.returncode == 0

    def raise_for_status(self):
        if not self.ok:
            raise RuntimeError(f"git failed ({self.returncode}): {self.stderr}")

    def validate(self) -> dict:
        if not self.ok:
            return {"passed": False, "issues": [f"git failed ({self.returncode}): {self.stderr}"]}
        return {"passed": True, "issues": []}


class GitClient:
    def __init__(self, repo_path: str = ".", allow_write: bool = False):
        self.repo_path = repo_path
        self.allow_write = allow_write

    def _run(
        self,
        args: List[str],
        cwd: Optional[str] = None,
        check: bool = True,
    ) -> GitResult:
        cmd = ["git"] + args
        try:
            proc = subprocess.run(
                cmd,
                cwd=cwd or self.repo_path,
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
            )
        except FileNotFoundError as exc:
            raise RuntimeError("git executable not found") from exc

        result = GitResult(
            returncode=proc.returncode,
            stdout=proc.stdout.strip(),
            stderr=proc.stderr.strip(),
        )
        if check:
            result.raise_for_status()
        return result

    # ---- read-only operations ----

    def status(self) -> GitResult:
        return self._run(["status", "--short"])

    def log(self, n: int = 5) -> GitResult:
        return self._run(["log", f"-{n}", "--oneline"])

    def diff(self) -> GitResult:
        return self._run(["diff"])

    def branch(self) -> GitResult:
        return self._run(["branch", "--show-current"])

    def remote_url(self) -> GitResult:
        return self._run(["remote", "get-url", "origin"], check=False)

    # ---- write operations (require allow_write=True) ----

    def add(self, path: str = ".") -> GitResult:
        self._guard_write("add")
        return self._run(["add", path])

    def commit(self, message: str) -> GitResult:
        self._guard_write("commit")
        return self._run(["commit", "-m", message])

    def push(self, remote: str = "origin", branch: str = "main") -> GitResult:
        self._guard_write("push")
        return self._run(["push", remote, branch])

    def _guard_write(self, operation: str):
        if not self.allow_write:
            raise PermissionError(
                f"Git write operation '{operation}' is disabled. "
                "Set allow_write=True to enable."
            )


if __name__ == "__main__":
    client = GitClient(repo_path=r"C:\Users\lu\.workbuddy")
    try:
        print(client.status().stdout)
        print(client.log(3).stdout)
    except Exception as exc:
        print(f"git error: {exc}")
