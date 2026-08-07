from fastapi import APIRouter, Depends

from api.dependencies import get_current_admin

router = APIRouter(
    prefix="/admin-api/commandcenter",
    tags=["Command Center"],
    dependencies=[Depends(get_current_admin)],
)


@router.get("/health")
async def command_health():
    return {"status": "ok"}


@router.get("/metrics")
async def command_metrics():
    return {}


@router.get("/events")
async def command_events():
    return []
