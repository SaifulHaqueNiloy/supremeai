"""Schema-constrained output boundary with bounded parse retries."""
from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any, TypeVar

T = TypeVar("T")


class StructuredOutputError(ValueError):
    pass


class StructuredOutputRouter:
    def __init__(self, *, max_retries: int = 2) -> None:
        self.max_retries = max(0, min(max_retries, 5))

    def parse(self, raw: str, validator: Callable[[Any], T]) -> T:
        candidate = raw.strip()
        for attempt in range(self.max_retries + 1):
            try:
                value = json.loads(candidate)
                return validator(value)
            except (json.JSONDecodeError, TypeError, ValueError) as exc:
                if attempt == self.max_retries:
                    raise StructuredOutputError("model output did not satisfy the requested schema") from exc
                candidate = self._extract_json(candidate)
        raise AssertionError("unreachable")

    @staticmethod
    def _extract_json(raw: str) -> str:
        start = min((index for index in (raw.find("{"), raw.find("[")) if index >= 0), default=-1)
        end = max(raw.rfind("}"), raw.rfind("]"))
        if start < 0 or end < start:
            return raw
        return raw[start : end + 1]


__all__ = ["StructuredOutputError", "StructuredOutputRouter"]
