from __future__ import annotations

import json
import os
from collections.abc import Mapping
from typing import Any
from uuid import UUID

import asyncpg


_pool: asyncpg.Pool | None = None


async def get_neon_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise RuntimeError("DATABASE_URL is required for Neon persistence")
        _pool = await asyncpg.create_pool(dsn=database_url, min_size=1, max_size=10)
    return _pool


async def close_neon_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


def _json(value: Mapping[str, Any] | None) -> str:
    return json.dumps(dict(value or {}), separators=(",", ":"))


async def load_policy(tenant_id: str, user_id: str | None = None) -> dict[str, Any] | None:
    pool = await get_neon_pool()
    row = await pool.fetchrow(
        """
        SELECT tenant_id, user_id, rules, features, actions, limits, version, updated_by,
               created_at, updated_at
        FROM supremeai_policy_configs
        WHERE tenant_id = $1 AND user_id IS NOT DISTINCT FROM $2
        ORDER BY user_id NULLS FIRST, version DESC
        LIMIT 1
        """,
        tenant_id,
        user_id,
    )
    return dict(row) if row else None


async def save_policy(
    tenant_id: str,
    updated_by: str,
    *,
    user_id: str | None = None,
    rules: Mapping[str, Any] | None = None,
    features: Mapping[str, Any] | None = None,
    actions: Mapping[str, Any] | None = None,
    limits: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    pool = await get_neon_pool()
    row = await pool.fetchrow(
        """
        INSERT INTO supremeai_policy_configs
          (tenant_id, user_id, rules, features, actions, limits, version, updated_by)
        VALUES ($1, $2, $3::jsonb, $4::jsonb, $5::jsonb, $6::jsonb, 1, $7)
        ON CONFLICT DO UPDATE SET
          rules = supremeai_policy_configs.rules || EXCLUDED.rules,
          features = supremeai_policy_configs.features || EXCLUDED.features,
          actions = supremeai_policy_configs.actions || EXCLUDED.actions,
          limits = supremeai_policy_configs.limits || EXCLUDED.limits,
          version = supremeai_policy_configs.version + 1,
          updated_by = EXCLUDED.updated_by,
          updated_at = NOW()
        RETURNING tenant_id, user_id, rules, features, actions, limits, version, updated_by,
                  created_at, updated_at
        """,
        tenant_id,
        user_id,
        _json(rules),
        _json(features),
        _json(actions),
        _json(limits),
        updated_by,
    )
    return dict(row)


async def create_task(
    *,
    task_id: UUID,
    tenant_id: str,
    user_id: str,
    url: str | None,
    goal: str,
    status: str,
    plan: Any = None,
    idempotency_key: str | None = None,
) -> dict[str, Any]:
    pool = await get_neon_pool()
    row = await pool.fetchrow(
        """
        INSERT INTO supremeai_browser_tasks
          (id, tenant_id, user_id, url, goal, status, plan, idempotency_key)
        VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb, $8)
        ON CONFLICT DO UPDATE SET updated_at = NOW()
        RETURNING id, tenant_id, user_id, url, goal, status, plan, approval, evidence,
                  idempotency_key, error, created_at, updated_at
        """,
        task_id,
        tenant_id,
        user_id,
        url,
        goal,
        status,
        json.dumps(plan or []),
        idempotency_key,
    )
    return dict(row)


async def list_tasks(tenant_id: str, user_id: str) -> list[dict[str, Any]]:
    pool = await get_neon_pool()
    rows = await pool.fetch(
        """
        SELECT id, tenant_id, user_id, url, goal, status, plan, approval, evidence,
               idempotency_key, error, created_at, updated_at
        FROM supremeai_browser_tasks
        WHERE tenant_id = $1 AND user_id = $2
        ORDER BY created_at DESC
        """,
        tenant_id,
        user_id,
    )
    return [dict(row) for row in rows]


async def append_audit_event(
    *,
    tenant_id: str,
    user_id: str | None,
    event_type: str,
    resource_type: str,
    resource_id: str | None,
    metadata: Mapping[str, Any] | None = None,
) -> None:
    pool = await get_neon_pool()
    await pool.execute(
        """
        INSERT INTO supremeai_audit_events
          (tenant_id, user_id, event_type, resource_type, resource_id, metadata)
        VALUES ($1, $2, $3, $4, $5, $6::jsonb)
        """,
        tenant_id,
        user_id,
        event_type,
        resource_type,
        resource_id,
        _json(metadata),
    )


__all__ = [
    "get_neon_pool",
    "close_neon_pool",
    "load_policy",
    "save_policy",
    "create_task",
    "list_tasks",
    "append_audit_event",
]
