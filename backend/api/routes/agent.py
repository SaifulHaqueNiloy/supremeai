# backend/api/routes/agent.py
"""Autonomous Agent Execution Route.

AUDIT FIX (2026-08):
The previous stub `/api/v1/agents/execute` returned hardcoded simulated "success" text.
The real implementation lives in `api/routes/agent_tasks.py` (registered in
`api/routers.py` -> optional_routers). This router is intentionally kept as an empty
shell to avoid a route collision and to guarantee there is NO fake/misleading output.
"""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/agents", tags=["Autonomous Agents"])
