"""Unit tests for the ConstrainedJSONDecoder — Outlines-inspired utility.

Tests cover:
- JSON repair (codeblocks, trailing commas, missing braces, single quotes)
- Schema validation (jsonschema path + manual fallback)
- decode() with and without schema
- decode_with_schema() retry behavior
- Skill schema specifically
- Bengali unicode in JSON values
- Graceful fallback on irrecoverable failure
"""

import json

import pytest

from core.llm.constrained_decoder import (
    SKILL_SCHEMA,
    ConstrainedJSONDecoder,
    get_constrained_decoder,
    _repair_json,
    _validate_manual,
)


class TestJSONRepair:
    """Tests for the _repair_json function."""

    def test_repair_codeblock_with_json_lang(self):
        raw = '```json\n{"name": "test"}\n```'
        repaired = _repair_json(raw)
        assert json.loads(repaired) == {"name": "test"}

    def test_repair_codeblock_without_lang(self):
        raw = '```\n{"name": "test"}\n```'
        repaired = _repair_json(raw)
        assert json.loads(repaired) == {"name": "test"}

    def test_repair_trailing_comma(self):
        raw = '{"name": "test", "value": 42,}'
        repaired = _repair_json(raw)
        assert json.loads(repaired) == {"name": "test", "value": 42}

    def test_repair_missing_closing_brace(self):
        raw = '{"name": "test", "value": 42'
        repaired = _repair_json(raw)
        assert json.loads(repaired) == {"name": "test", "value": 42}

    def test_repair_leading_conversational_text(self):
        raw = "Here is the JSON:\n{\"name\": \"test\"}"
        repaired = _repair_json(raw)
        assert json.loads(repaired) == {"name": "test"}

    def test_repair_single_quoted_strings(self):
        raw = "{'name': 'test', 'value': 42}"
        repaired = _repair_json(raw)
        assert json.loads(repaired) == {"name": "test", "value": 42}

    def test_repair_nested_missing_brace(self):
        raw = '{"outer": {"inner": {"key": "val"'
        repaired = _repair_json(raw)
        assert json.loads(repaired) == {"outer": {"inner": {"key": "val"}}}

    def test_repair_empty_string(self):
        assert _repair_json("") == ""

    def test_repair_bengali_unicode(self):
        raw = '{"name": "সুপ্রিম", "description": "একটি স্কিল টেস্ট"}'
        repaired = _repair_json(raw)
        assert json.loads(repaired) == {"name": "সুপ্রিম", "description": "একটি স্কিল টেস্ট"}


class TestManualValidation:
    """Tests for the zero-dependency _validate_manual function."""

    def test_valid_object(self):
        schema = {"type": "object", "required": ["name"], "properties": {"name": {"type": "string"}}}
        errors = _validate_manual({"name": "test"}, schema)
        assert errors == []

    def test_missing_required(self):
        schema = {"type": "object", "required": ["name"], "properties": {"name": {"type": "string"}}}
        errors = _validate_manual({}, schema)
        assert any("Missing required" in e for e in errors)

    def test_wrong_type(self):
        schema = {"type": "object", "properties": {"count": {"type": "integer"}}}
        errors = _validate_manual({"count": "not_a_number"}, schema)
        assert any("Expected integer" in e for e in errors)

    def test_additional_properties_false(self):
        schema = {
            "type": "object",
            "properties": {"a": {"type": "string"}},
            "additionalProperties": False,
        }
        errors = _validate_manual({"a": "ok", "b": "extra"}, schema)
        assert any("Unexpected properties" in e for e in errors)

    def test_array_items(self):
        schema = {"type": "array", "items": {"type": "string"}}
        errors = _validate_manual(["a", 123], schema)
        assert len(errors) > 0

    def test_enum(self):
        schema = {"type": "string", "enum": ["a", "b", "c"]}
        errors = _validate_manual("d", schema)
        assert any("not in enum" in e for e in errors)


class TestConstrainedJSONDecoder:
    """Tests for the ConstrainedJSONDecoder class."""

    def test_decode_valid_json(self):
        decoder = ConstrainedJSONDecoder()
        result = decoder.decode('{"name": "test", "value": 42}')
        assert result == {"name": "test", "value": 42}

    def test_decode_codeblock_json(self):
        decoder = ConstrainedJSONDecoder()
        result = decoder.decode("```json\n{\"name\": \"test\"}\n```")
        assert result == {"name": "test"}

    def test_decode_with_schema_valid(self):
        decoder = ConstrainedJSONDecoder()
        schema = SKILL_SCHEMA
        raw = json.dumps({
            "skill_name": "TestSkill",
            "description": "A test skill",
            "parameters": [{"name": "url", "type": "string", "description": "target"}],
            "execution_steps": [{"action": "navigate", "url": "https://example.com"}],
        })
        result = decoder.decode(raw, schema)
        assert result["skill_name"] == "TestSkill"

    def test_decode_with_schema_invalid_missing_required(self):
        decoder = ConstrainedJSONDecoder()
        raw = '{"skill_name": "TestSkill"}'  # Missing description, parameters, execution_steps
        with pytest.raises(ValueError, match="schema validation failed"):
            decoder.decode(raw, SKILL_SCHEMA)

    def test_decode_irrecoverable_failure(self):
        decoder = ConstrainedJSONDecoder()
        with pytest.raises(json.JSONDecodeError):
            decoder.decode("this is not json at all")

    def test_decode_with_schema_repair_then_validate(self):
        """Test that repair happens before validation."""
        decoder = ConstrainedJSONDecoder()
        raw = '```json\n{"skill_name": "Test", "description": "d", "parameters": [], "execution_steps": []}\n```'
        result = decoder.decode(raw, SKILL_SCHEMA)
        assert result["skill_name"] == "Test"

    def test_decode_with_schema_trailing_comma_repair(self):
        decoder = ConstrainedJSONDecoder()
        raw = '{"skill_name": "Test", "description": "d", "parameters": [], "execution_steps": [],}'
        result = decoder.decode(raw, SKILL_SCHEMA)
        assert result["skill_name"] == "Test"

    def test_decode_with_schema_invalid_type(self):
        decoder = ConstrainedJSONDecoder()
        raw = '{"skill_name": 123, "description": "d", "parameters": [], "execution_steps": []}'
        with pytest.raises(ValueError, match="schema validation failed"):
            decoder.decode(raw, SKILL_SCHEMA)


class TestDecodeWithSchema:
    """Tests for decode_with_schema retry behavior."""

    def test_success_first_attempt(self):
        decoder = ConstrainedJSONDecoder()
        raw = '{"a": 1}'
        schema = {"type": "object", "properties": {"a": {"type": "integer"}}}
        result = decoder.decode_with_schema(raw, schema, max_retries=2)
        assert result == {"a": 1}

    def test_retry_with_corrective_prompt(self):
        decoder = ConstrainedJSONDecoder()
        # Start with broken JSON, corrective prompt is valid JSON
        raw = '{"a": broken'
        schema = {"type": "object", "properties": {"a": {"type": "integer"}}}
        corrective = '{"a": 1}'
        result = decoder.decode_with_schema(
            raw, schema, max_retries=2, corrective_prompt=corrective
        )
        assert result == {"a": 1}

    def test_fallback_returns_best_effort_on_irrecoverable(self):
        decoder = ConstrainedJSONDecoder()
        # Even with retries, if nothing works, falls back to best-effort parse
        raw = "garbage"
        schema = {"type": "object"}
        with pytest.raises(json.JSONDecodeError):
            decoder.decode_with_schema(raw, schema, max_retries=2, corrective_prompt="also garbage")


class TestSingleton:
    def test_get_constrained_decoder_returns_singleton(self):
        d1 = get_constrained_decoder()
        d2 = get_constrained_decoder()
        assert d1 is d2


class TestSkillSchema:
    """End-to-end tests using the actual SKILL_SCHEMA constant."""

    def test_valid_skill_schema(self):
        decoder = ConstrainedJSONDecoder()
        raw = json.dumps({
            "skill_name": "ExtractUrls",
            "description": "Extracts all URLs from webpage content",
            "parameters": [
                {"name": "html_content", "type": "string", "description": "Raw HTML to parse"}
            ],
            "execution_steps": [
                {"action": "parse_html", "input": "html_content"},
                {"action": "regex_extract", "pattern": r"https?://[^\s\"']+"},
            ],
        })
        result = decoder.decode(raw, SKILL_SCHEMA)
        assert result["skill_name"] == "ExtractUrls"
        assert len(result["parameters"]) == 1
        assert len(result["execution_steps"]) == 2

    def test_skill_schema_with_bengali_text(self):
        decoder = ConstrainedJSONDecoder()
        raw = json.dumps({
            "skill_name": "বাংলা_স্কিল",
            "description": "বাংলায় টেক্সট প্রক্রিয়াকরণ স্কিল",
            "parameters": [],
            "execution_steps": [],
        }, ensure_ascii=False)
        result = decoder.decode(raw, SKILL_SCHEMA)
        assert result["skill_name"] == "বাংলা_স্কিল"
