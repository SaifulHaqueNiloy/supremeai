"""SQL injection guard for SupremeAI.

Validates incoming request parameters against common SQL injection
patterns. Dependency-free and safe to instantiate at import time.
"""

from __future__ import annotations

import re
from typing import Any

# Patterns tuned to catch classic injection attempts without false positives on
# ordinary text. Each is an anchored substring/keyword matcher.
_SQLI_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"(?i)(\b(union|select|insert|update|delete|drop|alter|truncate)\b.*\bfrom\b)"),
    re.compile(r"(?i)(\b(or|and)\b\s+[\w'\"\s]*=[\w'\"\s]*--)"),
    re.compile(r"(?i)(;\s*(drop|delete|update|insert|truncate|alter)\b)"),
    re.compile(r"(?i)(\bexec\b|\bxp_cmdshell\b)"),
    re.compile(r"(?i)('|\")\s*(\bor\b|\band\b)\s*('|\")\s*="),
    re.compile(r"(?i)/\*.*\*/"),
    re.compile(r"(?i)\b(0x[0-9a-f]{4,})\b"),
]


class SQLInjectionMiddleware:
    """Inspects request parameters and tracks blocked-request counters."""

    def __init__(self) -> None:
        self.request_counter = 0
        self.blocked_requests = 0

    @staticmethod
    def _is_suspicious(value: str) -> bool:
        return any(p.search(value) for p in _SQLI_PATTERNS)

    async def validate_request_params(self, params: dict[str, Any]) -> None:
        """Raise ``ValueError`` if any parameter looks like an injection attempt."""
        self.request_counter += 1
        for key, value in params.items():
            candidates = value if isinstance(value, (list, tuple)) else [value]
            for candidate in candidates:
                if isinstance(candidate, str) and self._is_suspicious(candidate):
                    self.blocked_requests += 1
                    raise ValueError(f"Potential SQL injection in parameter '{key}'")

    def get_stats(self) -> dict[str, int]:
        return {
            "request_counter": self.request_counter,
            "blocked_requests": self.blocked_requests,
        }


sql_injection_middleware = SQLInjectionMiddleware()
