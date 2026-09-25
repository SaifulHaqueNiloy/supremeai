"""Tests for agents/skill_gc.py — Skill garbage collector."""
import pytest
from agents.skill_gc import SkillGarbageCollector


class TestSkillGarbageCollector:
    def test_init(self):
        gc = SkillGarbageCollector()
        assert gc is not None

    @pytest.mark.asyncio
    async def test_collect_unused_skills(self):
        gc = SkillGarbageCollector()
        result = await gc.collect()
        assert result is not None
        assert isinstance(result, (list, dict))

    @pytest.mark.asyncio
    async def test_mark_skill_used(self):
        gc = SkillGarbageCollector()
        gc.mark_used("skill-1")
        result = await gc.collect()
        assert result is not None

    def test_set_ttl(self):
        gc = SkillGarbageCollector()
        gc.set_ttl(3600)
        assert gc.ttl == 3600 or gc._ttl == 3600
