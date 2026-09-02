# backend/api/deps.py
"""Canonical Dependency Re-export Module (Unified Auth DI - Audit B-006 Fix).

All authentication and infrastructure dependencies are canonically defined in
`api.dependencies`. This module re-exports them so existing callers keep working
with 100% architectural consistency and without duplicate authentication bypass logic.
"""

from __future__ import annotations

from api.dependencies import (
    get_ai_integrator,
    get_current_admin,
    get_current_user_token,
    get_fitness_engine,
    get_rate_limiter,
    get_tenant_db,
    verify_autonomous_agent_token,
)

__all__ = [
    "get_ai_integrator",
    "get_current_admin",
    "get_current_user_token",
    "get_fitness_engine",
    "get_rate_limiter",
    "get_tenant_db",
    "verify_autonomous_agent_token",
]
