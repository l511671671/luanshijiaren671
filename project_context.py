"""
项目感知上下文加载器

用法：
    from project_context import ProjectContext
    ctx = ProjectContext.from_path("/path/to/project")
    print(ctx.to_prompt_context())
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

WORKBUDDY_DIR = Path(__file__).resolve().parent

CONTEXT_FILES = ["AGENTS.md", "CLAUDE.md", "SOUL.md", "USER.md", "MEMORY.md", "HEARTBEAT.md"]
PROJECT_MARKER = ".workbuddy_project"


class ProjectContext:
    def __init__(self, root: Path, files: Optional[Dict[str, str]] = None):
        self.root = Path(root)
        self.files: Dict[str, str] = files or {}

    @classmethod
    def from_path(cls, start_path: Optional[Path] = None) -> "ProjectContext":
        """从给定路径向上查找项目根目录。"""
        path = Path(start_path or Path.cwd()).resolve()
        root = None
        for parent in [path, *path.parents]:
            if (parent / PROJECT_MARKER).exists() or (parent / "AGENTS.md").exists():
                root = parent
                break
        if root is None:
            root = path

        files: Dict[str, str] = {}
        for filename in CONTEXT_FILES:
            file_path = root / filename
            if file_path.exists():
                try:
                    files[filename] = file_path.read_text(encoding="utf-8", errors="ignore")
                except Exception as exc:  # pragma: no cover
                    files[filename] = f"[读取 {filename} 失败: {exc}]"
        return cls(root, files)

    def has_context(self, filename: str) -> bool:
        return filename in self.files

    def get(self, filename: str, default: str = "") -> str:
        return self.files.get(filename, default)

    def to_prompt_context(self, max_chars_per_file: int = 3000) -> str:
        """生成适合作为 system prompt 的项目上下文字符串。"""
        parts = [f"# 项目上下文\n\n项目根目录: {self.root}\n"]
        for filename in CONTEXT_FILES:
            if filename not in self.files:
                continue
            content = self.files[filename]
            if len(content) > max_chars_per_file:
                content = content[:max_chars_per_file] + "\n[...truncated...]"
            parts.append(f"## {filename}\n{content}\n")
        return "\n".join(parts)

    def summary(self) -> Dict:
        return {
            "root": str(self.root),
            "files_loaded": list(self.files.keys()),
            "file_sizes": {k: len(v) for k, v in self.files.items()},
        }


def main(argv: list | None = None) -> int:
    import argparse
    import json
    import sys

    parser = argparse.ArgumentParser(description="WorkBuddy 项目上下文")
    parser.add_argument("--path", type=Path, default=Path.cwd(), help="起始路径")
    parser.add_argument("--json", action="store_true", help="输出 JSON 摘要")
    args = parser.parse_args(argv)

    ctx = ProjectContext.from_path(args.path)
    if args.json:
        print(json.dumps(ctx.summary(), ensure_ascii=False, indent=2))
    else:
        print(ctx.to_prompt_context())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
