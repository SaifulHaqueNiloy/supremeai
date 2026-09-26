from fastapi import APIRouter, Depends

from api.dependencies import get_current_admin

router = APIRouter(
    prefix="",
    tags=["Command Center"],
    dependencies=[Depends(get_current_admin)],
)


@router.get("/system/config")
# Issue #1665: these handlers return static/aggregated data with no
# await — plain `def` routes (FastAPI runs them in the threadpool)
# instead of `async def` coroutines that never await. HTTP contract
# unchanged; only the event-loop scheduling semantics are corrected.

def get_config():
    return []


@router.post("/system/config")
def update_config(payload: dict):
    return {"message": "updated"}


@router.get("/system/flags")
def get_flags():
    return []


@router.post("/system/flags")
def update_flags(payload: dict):
    return {"message": "updated"}


@router.get("/system/workspaces")
def get_workspaces():
    return []


@router.get("/system/backups")
def get_backups():
    return []


@router.post("/system/backups")
def create_backup():
    return {"message": "backup created"}


@router.post("/system/backups/{backup_id}/restore")
def restore_backup(backup_id: str):
    return {"message": "restore initiated"}


@router.get("/system/deploy-gate")
def get_deploy_gate():
    return {"status": "UNLOCKED"}


@router.post("/system/deploy-gate")
def toggle_deploy_gate(payload: dict):
    return {"message": "updated"}
