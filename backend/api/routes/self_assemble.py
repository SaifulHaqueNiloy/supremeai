"""
Self-Assemble API Route
=======================
REST & WebSocket endpoints for trigger-driven autonomous software assembly.
"""

from typing import Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from engine.self_assembling_orchestrator import self_assembling_orchestrator

router = APIRouter(prefix="/self-assemble", tags=["Autonomous Self-Assembly"])


class SelfAssembleRequest(BaseModel):
    prompt: str = Field(..., description="High-level project or feature description")
    tenant_id: str = Field(default="default", description="Tenant ID")


class SelfAssembleResponse(BaseModel):
    session_id: str
    prompt: str
    status: str
    task_count: int
    agents_involved: list[str]
    execution_results: list[dict[str, Any]]
    graph_synced: bool


@router.post("", response_model=SelfAssembleResponse)
async def trigger_self_assemble(req: SelfAssembleRequest):
    """
    Trigger end-to-end autonomous software assembly pipeline.
    """
    if not req.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt must not be empty")

    try:
        report = await self_assembling_orchestrator.self_assemble_project(
            user_prompt=req.prompt,
            tenant_id=req.tenant_id,
        )
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Self-assembly failed: {e!s}")
