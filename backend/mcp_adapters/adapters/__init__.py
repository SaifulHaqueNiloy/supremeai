"""External builder adapters — Bolt (playwright deep-link) + Lovable (official MCP/API)।

Design principle (integrations/__init__ parity): heavy/optional dependencies
(playwright) importlib-guarded — missing lib → adapter reports unavailable,
সিস্টেম স্বাভাবিক চলে (zero-cost fallback)। #943 MESH-5।
"""

from __future__ import annotations

import importlib.util


def _available(module: str) -> bool:
    return importlib.util.find_spec(module) is not None


PLAYWRIGHT_AVAILABLE = _available("playwright")

__all__ = ["PLAYWRIGHT_AVAILABLE"]
