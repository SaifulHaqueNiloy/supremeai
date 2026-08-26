"""SupremeAI services package.

global_http_client is initialized at app startup (see core/lifespan.py:90)
as a shared httpx.AsyncClient with 50 keep-alive connections.

Module-level declaration here (None) allows `from services import global_http_client`
to succeed at import time, even before lifespan runs.
"""
from __future__ import annotations

from typing import Optional

try:
    import httpx
    _httpx_type = "httpx.AsyncClient"
except ImportError:
    _httpx_type = "object"

# Initialized by core.lifespan at app startup.
global_http_client: Optional[object] = None  # type: ignore[assignment]

__all__ = ["global_http_client"]
