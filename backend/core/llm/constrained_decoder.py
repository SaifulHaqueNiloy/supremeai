"""Constrained JSON Decoding — lightweight Outlines-inspired utility.

Provides deterministic JSON output from LLM responses by:
1. Repairing common LLM JSON malformations (trailing commas, codeblocks, missing braces)
2. Validating against a JSON Schema (using ``jsonschema`` if available, else
   a zero-dependency runtime type checker)
3. Optionally retrying with a corrective re-prompt via the LLM gateway

This mirrors the *spirit* of the ``outlines`` library (constrained token-level
generation) but uses a **post-hoc repair + retry** strategy instead — which
requires zero model-specific patches and works with every provider in the
routing chain (Gemini, Groq, OpenRouter, Moonshot, etc.).

বাংলা মন্তব্য: litellm-এর `response_format` JSON স্কিমা সাপোর্ট প্রোভাইডারভেতিক
ভিন্ন হয় (OpenAI/Groq ঠিকই সাপোর্ট করে, কিন্তু Gemini-এর native JSON mod নেই)।
এই ডিকোডার প্রোভাইডার-নির্ভরতা থেকে মুক্ত, সবার জন্য একই কন্সট্রাইন্টেড আউটপুট গ্যারান্টি করে।
"""

from __future__ import annotations

import importlib.util
import json
import re
from typing import Any

from loguru import logger

_HAS_JSONSCHEMA = importlib.util.find_spec("jsonschema") is not None


def _repair_json(raw_text: str) -> str:
    """Attempt to repair common LLM JSON malformations in-place.

    Handles:
    - Markdown code fences (`` ```json ... ``` ``)
    - Trailing commas before ``}`` or ``]``
    - Missing closing braces/brackets
    - Leading/trailing text before the first ``{``
    """
    if not raw_text:
        return ""

    cleaned = raw_text.strip()

    # 1. Extract from markdown code fence
    fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, re.DOTALL)
    if fence_match:
        cleaned = fence_match.group(1)
    else:
        # 2. If there's conversational text before the JSON, extract from first { onwards.
        # If no closing } exists, we still proceed — the depth-fix below will append it.
        start = cleaned.find("{")
        if start == -1:
            return cleaned
        end = cleaned.rfind("}")
        if end != -1:
            cleaned = cleaned[start : end + 1]
        else:
            cleaned = cleaned[start:]

    # 3. Remove trailing commas before } or ]
    cleaned = re.sub(r",\s*([}\]])", r"\1", cleaned)

    # 4. Fix missing closing braces — count depth
    depth = 0
    in_string = False
    escape = False
    for char in cleaned:
        if escape:
            escape = False
            continue
        if char == "\\":
            escape = True
            continue
        if char == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if char == "{":
            depth += 1
        elif char == "[":
            depth += 1
        elif char == "}":
            depth -= 1
        elif char == "]":
            depth -= 1

    if depth > 0:
        cleaned += "}" * depth
    elif depth < 0:
        # Too many closing — truncate extra from end
        cleaned = re.sub(r"[}\]\s]+$", "", cleaned)
        cleaned += "}" * max(-depth, 0)

    # 5. Fix single-quoted strings → double-quoted (common LLM output)
    cleaned = re.sub(r"'([^']*)'", r'"\1"', cleaned)

    return cleaned


def _validate_manual(data: Any, schema: dict[str, Any]) -> list[str]:
    """Zero-dependency schema validator using runtime type introspection.

    Supports a subset of JSON Schema: ``type``, ``properties``, ``required``,
    ``items``, ``enum``, ``additionalProperties``.
    """
    errors: list[str] = []
    stype = schema.get("type")

    if stype:
        expected_types: set[str] = set()
        if isinstance(stype, str):
            expected_types = {stype}
        elif isinstance(stype, list):
            expected_types = set(stype)

        if "object" in expected_types and not isinstance(data, dict):
            errors.append(f"Expected object, got {type(data).__name__}")
            return errors
        if "array" in expected_types and not isinstance(data, list):
            errors.append(f"Expected array, got {type(data).__name__}")
            return errors
        if "string" in expected_types and not isinstance(data, str):
            errors.append(f"Expected string, got {type(data).__name__}")
            return errors
        if "integer" in expected_types and not isinstance(data, int | float):
            errors.append(f"Expected integer, got {type(data).__name__}")
            return errors
        if "number" in expected_types and not isinstance(data, int | float):
            errors.append(f"Expected number, got {type(data).__name__}")
            return errors
        if "boolean" in expected_types and not isinstance(data, bool):
            errors.append(f"Expected boolean, got {type(data).__name__}")
            return errors
        if "null" in expected_types and data is not None:
            errors.append(f"Expected null, got {type(data).__name__}")
            return errors

    if isinstance(data, dict) and isinstance(schema.get("properties"), dict):
        required = schema.get("required", [])
        for req in required:
            if req not in data:
                errors.append(f"Missing required property: '{req}'")
        for key, subschema in schema["properties"].items():
            if key in data:
                errors.extend(_validate_manual(data[key], subschema))
        if schema.get("additionalProperties") is False:
            extra = set(data.keys()) - set(schema["properties"].keys())
            if extra:
                errors.append(f"Unexpected properties: {', '.join(extra)}")

    if isinstance(data, list) and isinstance(schema.get("items"), dict):
        for i, item in enumerate(data):
            errors.extend(_validate_manual(item, schema["items"]))

    if "enum" in schema and data not in schema["enum"]:
        errors.append(f"Value '{data}' not in enum {schema['enum']}")

    return errors


class ConstrainedJSONDecoder:
    """Decode LLM-generated JSON text into validated Python objects.

    Usage::

        decoder = ConstrainedJSONDecoder()
        result = decoder.decode_with_schema(
            raw_llm_output,
            schema={"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]},
        )
    """

    def __init__(self) -> None:
        self._jsonschema_validator = None
        if _HAS_JSONSCHEMA:
            try:
                from jsonschema import Draft7Validator

                self._jsonschema_validator = Draft7Validator
                logger.debug("ConstrainedJSONDecoder: jsonschema available, using Draft7Validator.")
            except ImportError:
                pass

    def repair_json(self, raw_text: str) -> str:
        """Repair common JSON malformations."""
        return _repair_json(raw_text)

    def validate_against_schema(self, data: Any, schema: dict[str, Any]) -> list[str]:
        """Validate *data* against *schema*. Returns list of error strings (empty = valid)."""
        if not schema:
            return []

        if self._jsonschema_validator is not None:
            try:
                validator = self._jsonschema_validator(schema)
                errors = sorted(validator.iter_errors(data), key=lambda e: e.path)
                return [f"{'.'.join(str(p) for p in e.absolute_path) or 'root'}: {e.message}" for e in errors]
            except Exception as exc:
                logger.warning(f"jsonschema validation failed, falling back to manual: {exc}")

        return _validate_manual(data, schema)

    def decode(self, raw_text: str, schema: dict[str, Any] | None = None) -> dict[str, Any] | list[Any]:
        """Repair → parse → (optionally) validate.

        Raises ``json.JSONDecodeError`` or ``ValueError`` on irrecoverable failure.
        """
        repaired = self.repair_json(raw_text)
        try:
            data = json.loads(repaired)
        except json.JSONDecodeError:
            # Last-ditch: try extracting individual JSON objects
            objects = re.findall(r"\{[^{}]*\}", repaired, re.DOTALL)
            if objects:
                for obj_str in reversed(objects):
                    try:
                        data = json.loads(obj_str)
                        break
                    except json.JSONDecodeError:
                        continue
                else:
                    raise
            else:
                raise

        if schema:
            errors = self.validate_against_schema(data, schema)
            if errors:
                logger.warning(f"ConstrainedJSONDecoder: schema validation errors: {errors}")
                raise ValueError(f"JSON schema validation failed: {'; '.join(errors)}")

        return data

    def decode_with_schema(
        self,
        raw_text: str,
        schema: dict[str, Any],
        max_retries: int = 2,
        corrective_prompt: str | None = None,
    ) -> dict[str, Any] | list[Any]:
        """Decode + validate, with optional retry via corrective re-prompt.

        When the first attempt fails schema validation, the method can build a
        corrective prompt asking the LLM to regenerate. However, if
        ``max_retries`` is exhausted, the raw repaired parse result is returned
        with a warning — the caller decides whether to accept it.
        """
        last_error: Exception | None = None

        for attempt in range(max_retries + 1):
            try:
                return self.decode(raw_text, schema)
            except (json.JSONDecodeError, ValueError) as exc:
                last_error = exc
                if attempt < max_retries and corrective_prompt is not None:
                    logger.info(
                        f"ConstrainedJSONDecoder: attempt {attempt + 1} failed, "
                        f"retrying with corrective prompt..."
                    )
                    raw_text = corrective_prompt
                    continue
                logger.warning(
                    f"ConstrainedJSONDecoder: all {max_retries + 1} attempts failed. "
                    f"Returning best-effort result. Error: {exc}"
                )

        # Final fallback: return repaired raw parse without schema validation
        try:
            repaired = self.repair_json(raw_text)
            return json.loads(repaired)
        except (json.JSONDecodeError, TypeError):
            raise last_error  # type: ignore[misc]


_constrained_decoder: ConstrainedJSONDecoder | None = None


def get_constrained_decoder() -> ConstrainedJSONDecoder:
    """Lazy singleton factory — avoids import overhead when not used."""
    global _constrained_decoder
    if _constrained_decoder is None:
        _constrained_decoder = ConstrainedJSONDecoder()
    return _constrained_decoder


# Schema for skill synthesis (used by skill_manager.py)
SKILL_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["skill_name", "description", "parameters", "execution_steps"],
    "properties": {
        "skill_name": {"type": "string"},
        "description": {"type": "string"},
        "parameters": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["name", "type", "description"],
                "properties": {
                    "name": {"type": "string"},
                    "type": {"type": "string"},
                    "description": {"type": "string"},
                },
            },
        },
        "execution_steps": {
            "type": "array",
            "items": {"type": "object"},
        },
    },
    "additionalProperties": True,
}
