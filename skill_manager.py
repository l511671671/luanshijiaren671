"""
智能 Skill 管理

- 列出已安装 skill
- 根据任务关键词推荐 skill
- 启用/禁用 skill
- 清理长期未使用的 skill

用法：
    python skill_manager.py list
    python skill_manager.py recommend "写个营销方案"
    python skill_manager.py enable <skill_name>
    python skill_manager.py disable <skill_name>
    python skill_manager.py prune --days 60
"""

from __future__ import annotations

import argparse
import datetime
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

WORKBUDDY_DIR = Path(__file__).resolve().parent
SKILLS_DIR = WORKBUDDY_DIR / "skills"
CONFIG_PATH = WORKBUDDY_DIR / "skills_config.json"
USAGE_PATH = WORKBUDDY_DIR / "skill_usage.json"


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


class SkillInfo:
    def __init__(self, path: Path):
        self.path = path
        self.name = path.name
        self.skill_md = path / "SKILL.md"
        self.meta_file = path / "_skillhub_meta.json"
        self.disabled_marker = path / ".disabled"
        self._meta: Optional[Dict] = None

    @property
    def exists(self) -> bool:
        return self.skill_md.exists()

    @property
    def meta(self) -> Dict[str, Any]:
        if self._meta is None:
            self._meta = _read_json(self.meta_file, {})
        return self._meta

    @property
    def description(self) -> str:
        desc = self.meta.get("description") or self.meta.get("examples_zh", [""])
        if isinstance(desc, list):
            return "; ".join(desc[:2])
        return str(desc)

    @property
    def enabled(self) -> bool:
        return not self.disabled_marker.exists()

    def disable(self) -> None:
        self.disabled_marker.write_text("", encoding="utf-8")

    def enable(self) -> None:
        if self.disabled_marker.exists():
            self.disabled_marker.unlink()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "enabled": self.enabled,
            "path": str(self.path),
        }


class SkillManager:
    def __init__(self, skills_dir: Optional[Path] = None):
        self.skills_dir = skills_dir or SKILLS_DIR

    def list_skills(self) -> List[SkillInfo]:
        skills = []
        if not self.skills_dir.exists():
            return skills
        for path in sorted(self.skills_dir.iterdir()):
            if path.is_dir() and (path / "SKILL.md").exists():
                skills.append(SkillInfo(path))
        return skills

    def recommend(self, task: str, top_k: int = 3) -> List[SkillInfo]:
        """基于任务关键词匹配 skill 名称和描述。"""
        task_lower = task.lower()
        scored = []
        for skill in self.list_skills():
            text = (skill.name + " " + skill.description).lower()
            # 简单按空格拆分任务词，统计命中数
            hits = sum(1 for word in task_lower.split() if len(word) > 1 and word in text)
            if hits > 0:
                scored.append((hits, skill))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [s for _, s in scored[:top_k]]

    def disable(self, name: str) -> bool:
        info = SkillInfo(self.skills_dir / name)
        if not info.exists:
            return False
        info.disable()
        return True

    def enable(self, name: str) -> bool:
        info = SkillInfo(self.skills_dir / name)
        if not info.exists:
            return False
        info.enable()
        return True

    def record_usage(self, name: str) -> None:
        usage = _read_json(USAGE_PATH, {})
        usage[name] = datetime.datetime.now().isoformat()
        _write_json(USAGE_PATH, usage)

    def prune_candidates(self, days: int = 60) -> List[str]:
        """返回超过 N 天未使用且非强依赖的 skill 名称。"""
        usage = _read_json(USAGE_PATH, {})
        cutoff = datetime.datetime.now() - datetime.timedelta(days=days)
        candidates = []
        for skill in self.list_skills():
            last = usage.get(skill.name)
            if not last:
                candidates.append(skill.name)
                continue
            try:
                last_dt = datetime.datetime.fromisoformat(last)
                if last_dt < cutoff:
                    candidates.append(skill.name)
            except Exception:
                candidates.append(skill.name)
        return candidates


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(description="WorkBuddy Skill Manager")
    sub = parser.add_subparsers(dest="command", required=True)

    p_list = sub.add_parser("list", help="列出已安装 skill")
    p_recommend = sub.add_parser("recommend", help="根据任务推荐 skill")
    p_recommend.add_argument("task", help="任务描述")
    p_recommend.add_argument("--top-k", type=int, default=3)

    p_enable = sub.add_parser("enable", help="启用 skill")
    p_enable.add_argument("name", help="skill 名称")

    p_disable = sub.add_parser("disable", help="禁用 skill")
    p_disable.add_argument("name", help="skill 名称")

    p_prune = sub.add_parser("prune", help="列出可清理 skill")
    p_prune.add_argument("--days", type=int, default=60, help="未使用天数阈值")

    args = parser.parse_args(argv)
    manager = SkillManager()

    if args.command == "list":
        for skill in manager.list_skills():
            print(f"{'[E]' if skill.enabled else '[D]'} {skill.name}\n  {skill.description}")
    elif args.command == "recommend":
        for skill in manager.recommend(args.task, args.top_k):
            print(f"- {skill.name}: {skill.description}")
    elif args.command == "enable":
        ok = manager.enable(args.name)
        print(f"{'enabled' if ok else 'not found'} {args.name}")
    elif args.command == "disable":
        ok = manager.disable(args.name)
        print(f"{'disabled' if ok else 'not found'} {args.name}")
    elif args.command == "prune":
        for name in manager.prune_candidates(args.days):
            print(f"prune candidate: {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
