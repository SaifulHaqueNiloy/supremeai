"""
Tests for structured JSON schema validation in BaseSkill and SkillManager.

Verifies that tool arguments are validated and type-coerced before
execution, preventing hallucinated or malformed inputs from causing
runtime errors.
"""

import pytest

from core.skills.base import BaseSkill


class TestSchemaValidation:
    """Unit tests for BaseSkill.validate_args()."""

    def test_valid_args_pass_validation(self):
        class MySkill(BaseSkill):
            name = "my_skill"
            parameters = [
                {"name": "url", "type": "string", "description": "Target URL"},
                {"name": "timeout", "type": "integer", "description": "Timeout in seconds", "default": 30},
            ]

        skill = MySkill()
        result = skill.validate_args({"url": "https://example.com", "timeout": 60})
        assert result["url"] == "https://example.com"
        assert result["timeout"] == 60

    def test_missing_required_arg_raises(self):
        class MySkill(BaseSkill):
            name = "my_skill"
            parameters = [
                {"name": "query", "type": "string", "description": "Search query"},
            ]

        skill = MySkill()
        with pytest.raises(ValueError, match="Missing required parameter: query"):
            skill.validate_args({"limit": 10})

    def test_default_value_used_when_missing(self):
        class MySkill(BaseSkill):
            name = "my_skill"
            parameters = [
                {"name": "limit", "type": "integer", "description": "Max results", "default": 5},
            ]

        skill = MySkill()
        result = skill.validate_args({})
        assert result["limit"] == 5

    def test_type_coercion_string_to_int(self):
        class MySkill(BaseSkill):
            name = "my_skill"
            parameters = [
                {"name": "count", "type": "integer", "description": "Count"},
            ]

        skill = MySkill()
        result = skill.validate_args({"count": "42"})
        assert result["count"] == 42
        assert isinstance(result["count"], int)

    def test_type_coercion_string_to_float(self):
        class MySkill(BaseSkill):
            name = "my_skill"
            parameters = [
                {"name": "rate", "type": "number", "description": "Rate"},
            ]

        skill = MySkill()
        result = skill.validate_args({"rate": "3.14"})
        assert result["rate"] == 3.14
        assert isinstance(result["rate"], float)

    def test_type_coercion_string_to_bool(self):
        class MySkill(BaseSkill):
            name = "my_skill"
            parameters = [
                {"name": "enabled", "type": "boolean", "description": "Enable flag"},
            ]

        skill = MySkill()
        result = skill.validate_args({"enabled": "true"})
        assert result["enabled"] is True

    def test_invalid_type_coercion_raises(self):
        class MySkill(BaseSkill):
            name = "my_skill"
            parameters = [
                {"name": "count", "type": "integer", "description": "Count"},
            ]

        skill = MySkill()
        with pytest.raises(ValueError, match="cannot coerce"):
            skill.validate_args({"count": "not_a_number"})

    def test_no_schema_passes_through(self):
        class NoSchemaSkill(BaseSkill):
            name = "no_schema"

        skill = NoSchemaSkill()
        result = skill.validate_args({"anything": "goes"})
        assert result == {"anything": "goes"}

    def test_extra_args_filtered(self):
        class MySkill(BaseSkill):
            name = "my_skill"
            parameters = [
                {"name": "query", "type": "string", "description": "Search query"},
            ]

        skill = MySkill()
        result = skill.validate_args({"query": "test", "unexpected": "value"})
        assert "unexpected" not in result
        assert result["query"] == "test"


class TestSkillManagerValidation:
    """Tests for SkillManager.validate_and_sanitize_tool_input()."""

    @pytest.mark.asyncio
    async def test_manager_validates_registered_skill(self, monkeypatch):
        from core.skill_manager import SkillManager

        class MockSkill(BaseSkill):
            name = "mock_skill"
            parameters = [
                {"name": "action", "type": "string", "description": "Action to perform"},
            ]
            async def run(self, **kwargs):
                return kwargs

        mgr = SkillManager()
        mgr.register_skill(MockSkill())

        result = await mgr.validate_and_sanitize_tool_input("mock_skill", {"action": "test"})
        assert result["action"] == "test"

    @pytest.mark.asyncio
    async def test_manager_rejects_bad_input(self, monkeypatch):
        from core.skill_manager import SkillManager

        class MockSkill(BaseSkill):
            name = "strict_skill"
            parameters = [
                {"name": "required_field", "type": "string", "description": "Required"},
            ]
            async def run(self, **kwargs):
                return kwargs

        mgr = SkillManager()
        mgr.register_skill(MockSkill())

        with pytest.raises(ValueError, match="Missing required parameter: required_field"):
            await mgr.validate_and_sanitize_tool_input("strict_skill", {"other": "value"})
