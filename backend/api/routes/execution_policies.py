from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from database.session import get_db_session
from models.execution_policy import ExecutionPolicy

router = APIRouter(prefix="/api/admin/execution-policies", tags=["Guardrails"])


class ExecutionPolicyModel(BaseModel):
    id: str
    scope: str
    target_name: str
    max_timeout_ms: int
    max_compute_usd: float
    max_retries: int
    cb_failure_threshold: int
    cooldown_window_sec: int


@router.get("/")
async def get_policies(session: AsyncSession = Depends(get_db_session)):
    result = await session.execute(select(ExecutionPolicy))
    policies = result.scalars().all()

    formatted = []
    for pol in policies:
        formatted.append({
            "id": str(pol.id),
            "scope": pol.scope.value,
            "target_name": "*",  # Add a DB field for this if needed, mocking for now as per previous struct
            "max_timeout_ms": pol.max_timeout_seconds * 1000,
            "max_compute_usd": float(pol.max_serverless_compute_budget_usd),
            "max_retries": pol.max_retries,
            "cb_failure_threshold": pol.circuit_breaker_failure_threshold,
            "cooldown_window_sec": pol.circuit_breaker_cooldown_seconds,
        })
    return {"items": formatted}


@router.put("/{policy_id}")
async def update_policy(policy_id: str, updates: dict, session: AsyncSession = Depends(get_db_session)):
    import uuid
    try:
        pid = uuid.UUID(policy_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid policy UUID")

    result = await session.execute(select(ExecutionPolicy).where(ExecutionPolicy.id == pid))
    pol = result.scalars().first()
    if not pol:
        raise HTTPException(status_code=404, detail="not found")

    if "max_timeout_ms" in updates:
        pol.max_timeout_seconds = updates["max_timeout_ms"] // 1000
    if "max_retries" in updates:
        pol.max_retries = updates["max_retries"]

    await session.commit()

    return {
        "id": str(pol.id),
        "scope": pol.scope.value,
        "target_name": "*",
        "max_timeout_ms": pol.max_timeout_seconds * 1000,
        "max_compute_usd": float(pol.max_serverless_compute_budget_usd),
        "max_retries": pol.max_retries,
        "cb_failure_threshold": pol.circuit_breaker_failure_threshold,
        "cooldown_window_sec": pol.circuit_breaker_cooldown_seconds,
    }
