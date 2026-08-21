"""Admin API v1 aliases.

বাংলা মন্তব্য: লাইভ (deployed) অ্যাডমিন ফ্রন্টএন্ড /api/v1/agents কল করে, কিন্তু ব্যাকএন্ডে
সেই পাথটি ছিল না → 404। Command Center-এর Agents/Tasks tab গুলো এর জন্য error দেখাত।
এখানে /api/v1/agents alias যোগ করা হলো যাতে লাইভ সাইটেও tab গুলো সঠিকভাবে render করে।
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

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
