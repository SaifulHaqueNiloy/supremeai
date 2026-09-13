"""Task lifecycle endpoints: Neon-backed canonical versions first, then the
legacy in-memory (TASKS/FINDINGS) duplicates that follow them in the original
file — preserved verbatim INCLUDING their duplicate route registrations, since
route registration order determines which handler wins at match time.

Split out of the former single-module api/routes/browser.py verbatim.
``TASKS``/``FINDINGS`` live in THIS module; they are only ever mutated in
place (item assignment / append / del), never rebound.
"""

import uuid
from typing import Any

from fastapi import Depends, HTTPException
from pydantic import BaseModel, Field

from api.deps import get_current_tenant, get_current_user_token
from api.routes.browser import router
from core.neon_repository import (
    create_task as create_neon_task,
)
from core.neon_repository import (
    delete_task as delete_neon_task,
)
from core.neon_repository import (
    update_task_status as update_neon_task_status,
)
from core.task_policy import evaluate_goal

TASKS: dict[str, dict[str, Any]] = {}
FINDINGS: list[dict[str, Any]] = []

# বাংলা মন্তব্য: সার্কিট ব্রেকার থ্রেশোল্ড — টাস্ক এক্সিকিউশন ক্যাপ (৪৫ সেকেন্ড)
EXECUTION_CAP_MS = 45000


class GoalRequest(BaseModel):
    goal: str


class TaskPreviewRequest(BaseModel):
    url: str | None = Field(default=None, max_length=2048)
    goal: str = Field(min_length=1, max_length=10_000)
    approved: bool = False


@router.post("/tasks/preview")
async def preview_task(
    req: TaskPreviewRequest,
    user: dict = Depends(get_current_user_token),
    tenant_id: str = Depends(get_current_tenant),
):
    actor_id = str(user.get("sub") or "")
    decision = evaluate_goal(req.goal, actor_id)
    if not actor_id:
        raise HTTPException(status_code=401, detail="Authenticated user required")
    if not decision.allowed:
        return {"status": "manual", "risk": decision.risk, "message": decision.message}
    if decision.risk == "approval" and not req.approved:
        return {"status": "approval_required", "risk": decision.risk, "message": decision.message}
    task_id = uuid.uuid4()
    task = await create_neon_task(
        task_id=task_id,
        tenant_id=tenant_id,
        user_id=actor_id,
        url=req.url,
        goal=req.goal,
        status="ACTIVE",
        plan=[{"risk": decision.risk, "message": decision.message}],
    )
    return {
        "status": "started",
        "message": "Your safe task has started. SupremeAI will pause if it needs your approval.",
        "task": task,
    }


@router.post("/tasks")
async def create_task(
    req: GoalRequest,
    user: dict = Depends(get_current_user_token),
    tenant_id: str = Depends(get_current_tenant),
):
    owner_id = str(user.get("sub") or "")
    if not owner_id:
        raise HTTPException(status_code=401, detail="Authenticated user required")
    return await create_neon_task(
        task_id=uuid.uuid4(),
        tenant_id=tenant_id,
        user_id=owner_id,
        url=None,
        goal=req.goal,
        status="ACTIVE",
    )


async def _set_task_status(
    task_id: str,
    status: str,
    user: dict = Depends(get_current_user_token),
    tenant_id: str = Depends(get_current_tenant),
):
    owner_id = str(user.get("sub") or "")
    try:
        task_uuid = uuid.UUID(task_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Task not found") from exc
    updated = await update_neon_task_status(
        task_id=task_uuid, tenant_id=tenant_id, user_id=owner_id, status=status
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"success": True, "status": status}


@router.post("/tasks/{id}/circuit-open")
async def set_task_circuit_open(
    task_id: str,
    user: dict = Depends(get_current_user_token),
    tenant_id: str = Depends(get_current_tenant),
):
    return await _set_task_status(task_id, "CIRCUIT_OPEN", user, tenant_id)


@router.post("/tasks/{id}/complete")
async def set_task_complete(
    task_id: str,
    user: dict = Depends(get_current_user_token),
    tenant_id: str = Depends(get_current_tenant),
):
    return await _set_task_status(task_id, "SUCCESS", user, tenant_id)


@router.post("/tasks/{id}/fail")
async def set_task_failed(
    task_id: str,
    user: dict = Depends(get_current_user_token),
    tenant_id: str = Depends(get_current_tenant),
):
    return await _set_task_status(task_id, "FAILED", user, tenant_id)


@router.delete("/tasks/{id}")
async def delete_task(
    task_id: str,
    user: dict = Depends(get_current_user_token),
    tenant_id: str = Depends(get_current_tenant),
):
    owner_id = str(user.get("sub") or "")
    try:
        deleted = await delete_neon_task(
            task_id=uuid.UUID(task_id), tenant_id=tenant_id, user_id=owner_id
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Task not found") from exc
    if not deleted:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"success": True}
    TASKS[task_id]["status"] = "CIRCUIT_OPEN"
    TASKS[task_id]["durationMs"] = EXECUTION_CAP_MS
    return {"success": True, "status": "CIRCUIT_OPEN"}


@router.post("/tasks/{id}/complete")
def set_task_complete(task_id: str):
    """বাংলা মন্তব্য: টাস্ক সফলভাবে সম্পন্ন হলে কল করুন"""
    if task_id not in TASKS:
        raise HTTPException(status_code=404, detail="Task not found")
    TASKS[task_id]["status"] = "SUCCESS"
    return {"success": True, "status": "SUCCESS"}


@router.post("/tasks/{id}/fail")
def set_task_failed(task_id: str):
    """বাংলা মন্তব্য: টাস্ক ব্যর্থ হলে কল করুন"""
    if task_id not in TASKS:
        raise HTTPException(status_code=404, detail="Task not found")
    TASKS[task_id]["status"] = "FAILED"
    return {"success": True, "status": "FAILED"}


@router.delete("/tasks/{id}")
def delete_task(task_id: str):
    if task_id in TASKS:
        del TASKS[task_id]
        return {"success": True}
    raise HTTPException(status_code=404, detail="Task not found")


@router.get("/tasks/{id}/findings")
def get_findings(task_id: str):
    task_findings = [f for f in FINDINGS if f.get("taskId") == task_id]
    return {"findings": task_findings}


@router.post("/findings")
def add_finding(finding: dict[str, Any]):
    FINDINGS.append(finding)
    return finding
