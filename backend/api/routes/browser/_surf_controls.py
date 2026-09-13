"""Legacy manual-pause surf controls (admin-guarded).

Split out of the former single-module api/routes/browser.py verbatim.
"""

from typing import Any

from fastapi import Depends

from api.routes.admin_dashboard import require_admin_token
from api.routes.browser import router

PAUSED_STATE: dict[str, Any] = {"paused": False}


@router.post("/surf/resume", dependencies=[Depends(require_admin_token)])
def resume_surf(body: dict[str, str]):
    PAUSED_STATE["paused"] = False
    return {"status": "resumed"}


@router.post("/surf/skip-auth", dependencies=[Depends(require_admin_token)])
def skip_auth(body: dict[str, str]):
    PAUSED_STATE["paused"] = False
    return {"status": "auth_skipped"}


@router.post("/surf/pause-manual", dependencies=[Depends(require_admin_token)])
def pause_manual(body: dict[str, str]):
    PAUSED_STATE["paused"] = True
    return {"status": "paused_for_manual"}


@router.get("/surf/paused-state")
def get_paused_state():
    return PAUSED_STATE
