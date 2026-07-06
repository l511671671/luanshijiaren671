"""Tests for skill_manager."""

from skill_manager import SkillManager, SkillInfo


def test_recommend(tmp_path):
    skill_dir = tmp_path / "skills" / "web-search"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("web search skill", encoding="utf-8")
    manager = SkillManager(skills_dir=tmp_path / "skills")
    results = manager.recommend("search web")
    assert len(results) == 1
    assert results[0].name == "web-search"


def test_enable_disable(tmp_path):
    skill_dir = tmp_path / "skills" / "demo"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("demo", encoding="utf-8")
    manager = SkillManager(skills_dir=tmp_path / "skills")
    assert manager.disable("demo")
    info = SkillInfo(skill_dir)
    assert not info.enabled
    assert manager.enable("demo")
    assert SkillInfo(skill_dir).enabled
