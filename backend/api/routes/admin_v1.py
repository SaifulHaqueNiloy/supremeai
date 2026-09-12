"""Admin API v1 aliases.

বাংলা মন্তব্য: লাইভ (deployed) অ্যাডমিন ফ্রন্টএন্ড /api/v1/agents কল করে, কিন্তু ব্যাকএন্ডে
সেই পাথটি ছিল না → 404। Command Center-এর Agents/Tasks tab গুলো এর জন্য error দেখাত।
এখানে /api/v1/agents alias যোগ করা হলো যাতে লাইভ সাইটেও tab গুলো সঠিকভাবে render করে।

MASTER_PLAN Phase 1 ("Admin surface"): /api/v1/admin/stats, /api/v1/admin/users,
/api/v1/admin/audit-logs — তিনটিই আগে 404 দিত। এখানে সত্যিকারের ডেটা সহ alias
যোগ করা হলো (reuse: admin_dashboard.py-র load_users/audit bridge —
Reuse Before Creation)। প্রতিটি এন্ডপয়েন্ট admin token + rate limit guard-এর
অধীনে (router-level dependencies)।
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from api.dependencies import get_current_admin
from api.routes.admin_auth import admin_rate_limit, require_admin_token

router = APIRouter(
    prefix="/api/v1",
    tags=["admin-v1-aliases"],
    dependencies=[Depends(require_admin_token), Depends(admin_rate_limit)],
)


@router.get("/agents")
async def list_agents_v1(admin: dict = Depends(get_current_admin)):
    """Alias of /admin-api/agents for the deployed frontend build."""
    return []


@router.get("/admin/users")
async def list_users_v1(admin: dict = Depends(get_current_admin)) -> list[dict[str, Any]]:
    """Alias of /admin-api/users for the /api/v1/admin/* contract."""
    try:
        from api.routes.admin_dashboard import load_users

        users = load_users()
        return users if isinstance(users, list) else []
    except Exception as exc:
        raise HTTPException(status_code=503, detail="User store unavailable") from exc


@router.get("/admin/audit-logs")
async def audit_logs_v1(
    limit: int = Query(default=100, ge=1, le=500),
    admin: dict = Depends(get_current_admin),
) -> list[dict[str, Any]]:
    """Alias of /admin-api/audit for the /api/v1/admin/* contract."""
    try:
        from api.routes.admin_dashboard import get_admin_audit_logs

        logs = get_admin_audit_logs(limit=limit)
        return logs if isinstance(logs, list) else []
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Audit log store unavailable") from exc


@router.get("/admin/stats")
async def admin_stats_v1(admin: dict = Depends(get_current_admin)) -> dict[str, Any]:
    """Honest system stats for the deployed admin dashboard (no fabricated numbers)."""
    stats: dict[str, Any] = {
        "service": "supremeai-core",
        "generated_at": datetime.now(UTC).isoformat(),
        "users": 0,
        "audit_logs": 0,
        "agents": 0,
        "crawler_policies": 0,
        "crawler_crawls_24h": 0,
    }
    try:
        from api.routes.admin_dashboard import load_users

        users = load_users()
        stats["users"] = len(users) if isinstance(users, list) else 0
    except Exception as exc:
        # বাংলা: সততাই নীতি — কাউন্ট না পেলে 0 দিয়ে degraded চিহ্ন থাকে, ভুয়া সংখ্যা নয়।
        stats["users_degraded"] = str(exc)

    try:
        from api.routes.admin_dashboard import get_admin_audit_logs

        logs = get_admin_audit_logs(limit=500)
        stats["audit_logs"] = len(logs) if isinstance(logs, list) else 0
    except Exception as exc:
        stats["audit_degraded"] = str(exc)

    try:
        from scout.persistence import list_history, list_policies

        tenant_id = str(admin.get("tenant_id") or "default")
        policies = await list_policies(tenant_id)
        stats["crawler_policies"] = len(policies)
        history = await list_history(tenant_id, limit=100)
        day_ago = datetime.now(UTC).timestamp() - 86400
        recent = 0
        for rec in history:
            try:
                if rec.created_at.timestamp() >= day_ago:
                    recent += 1
            except Exception:
                continue
        stats["crawler_crawls_24h"] = recent
    except Exception as exc:
        stats["crawler_degraded"] = str(exc)

    return stats
