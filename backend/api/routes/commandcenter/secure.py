from fastapi import APIRouter, Depends

from api.dependencies import get_current_admin

router = APIRouter(
    prefix="",
    tags=["Command Center"],
    dependencies=[Depends(get_current_admin)],
)


@router.get("/secure/threats")
# Issue #1665: these handlers return static/aggregated data with no
# await — plain `def` routes (FastAPI runs them in the threadpool)
# instead of `async def` coroutines that never await. HTTP contract
# unchanged; only the event-loop scheduling semantics are corrected.

def get_threats():
    return {"scan_time": "", "findings": [], "total_findings": 0}


@router.get("/secure/audit")
def get_audit():
    return []


@router.get("/secure/approvals")
def get_approvals():
    return []


@router.get("/secure/rules")
def get_rules():
    return {}


@router.post("/secure/rules")
def update_rules(payload: dict):
    return {"message": "updated"}


@router.get("/secure/secrets")
def get_secrets():
    return {"status": "unknown", "secrets": []}


@router.get("/secure/ratelimits")
def get_rate_limits():
    return {"current_429_events": 0, "per_ip": {}, "per_tenant": {}}
