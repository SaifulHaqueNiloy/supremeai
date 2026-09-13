"""System-learning toggle endpoints (in-memory compat state).

Split out of the former single-module api/routes/browser.py verbatim.
"""

from typing import Any

from fastapi import Depends

from api.routes.admin_dashboard import require_admin_token
from api.routes.browser import router

SYSTEM_LEARNING: dict[str, Any] = {"enabled": True}


@router.get("/system-learning")
def get_system_learning():
    return SYSTEM_LEARNING


@router.post("/system-learning/toggle", dependencies=[Depends(require_admin_token)])
def toggle_learning(body: dict[str, bool]):
    SYSTEM_LEARNING["enabled"] = body.get("enabled", True)
    return {"success": True}
