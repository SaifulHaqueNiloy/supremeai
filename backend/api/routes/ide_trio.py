"""
FastAPI Router — IDE Trio Pipeline
==================================

Exposes the Gemini → Kilo → Cline pipeline as REST endpoints:

    POST /api/v1/ide-trio/execute  — run the full pipeline
    GET  /api/v1/ide-trio/agents   — list the three IDE agents
    GET  /api/v1/ide-trio/health   — pipeline health check
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1/ide-trio", tags=["ide-trio"])


class TrioExecuteRequest(BaseModel):
    """Request body for executing the IDE trio pipeline."""

    prompt: str = Field(..., description="Natural-language description of the coding task")
    language: str = Field("python", description="Target programming language")
    filePath: str | None = Field(None, description="Optional file path for context")
    existingCode: str | None = Field(None, description="Existing code snippet")
    projectContext: str | None = Field(None, description="Optional project-level context")


@router.post("/execute")
async def execute_trio(request: TrioExecuteRequest) -> dict[str, Any]:
    """Run the Gemini → Kilo → Cline pipeline and return the full result."""
    try:
        from core.orchestration.trio_pipeline import TrioPipeline

        pipeline = TrioPipeline()
        context: dict[str, str] = {}
        if request.filePath:
            context["filePath"] = request.filePath
        if request.existingCode:
            context["existingCode"] = request.existingCode
        if request.projectContext:
            context["projectContext"] = request.projectContext

        result = await pipeline.execute(
            prompt=request.prompt,
            language=request.language,
            context=context,
        )
        return result

    except Exception as exc:  # BLE001 - route boundaries must not crash the server
        raise HTTPException(status_code=500, detail=f"Trio pipeline failed: {exc}") from exc


@router.get("/status")
async def trio_status() -> dict[str, Any]:
    """Return the availability status of the three IDE agents."""
    try:
        from agents.ide.trio_adapters import ClineChecker, GeminiWriter, KiloReviewer

        return {
            "pipeline": "ide-trio",
            "agents": [
                {"role": "writer", "agent": "gemini", "available": True, "class": GeminiWriter.__name__},
                {"role": "reviewer", "agent": "kilo", "available": True, "class": KiloReviewer.__name__},
                {"role": "checker", "agent": "cline", "available": True, "class": ClineChecker.__name__},
            ],
            "status": "ready",
        }
    except ImportError as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Trio pipeline agents not importable: {exc}",
        ) from exc
