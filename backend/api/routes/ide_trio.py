"""
FastAPI Router — IDE Trio Pipeline
==================================

Exposes the reusable Agent Review Workflow as REST endpoints. The canonical
paths use ``/api/v1/agent_review_workflow``; the legacy ``/api/v1/ide-trio``
paths remain as thin aliases during migration.

    POST /api/v1/agent_review_workflow/execute — canonical execution path
    GET  /api/v1/agent_review_workflow/status  — canonical status path
    POST /api/v1/ide-trio/execute             — legacy execution alias
    GET  /api/v1/ide-trio/status              — legacy status alias
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="", tags=["agent_review_workflow"])

_CANONICAL_PREFIX = "/api/v1/agent_review_workflow"
_LEGACY_PREFIX = "/api/v1/ide-trio"


class TrioExecuteRequest(BaseModel):
    """Request body for executing the IDE trio pipeline."""

    prompt: str = Field(..., description="Natural-language description of the coding task")
    language: str = Field("python", description="Target programming language")
    filePath: str | None = Field(None, description="Optional file path for context")
    existingCode: str | None = Field(None, description="Existing code snippet")
    projectContext: str | None = Field(None, description="Optional project-level context")


@router.post(f"{_CANONICAL_PREFIX}/execute")
@router.post(f"{_LEGACY_PREFIX}/execute", include_in_schema=False)
async def execute_trio(request: TrioExecuteRequest) -> dict[str, Any]:
    """Run the Gemini → Kilo → Cline pipeline and return the full result."""
    try:
        from core.agent_review_workflow import AgentReviewWorkflow

        pipeline = AgentReviewWorkflow()
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


@router.get(f"{_CANONICAL_PREFIX}/status")
@router.get(f"{_LEGACY_PREFIX}/status", include_in_schema=False)
async def trio_status() -> dict[str, Any]:
    """Return the availability status of the three IDE agents."""
    try:
        from agents.ide.trio_adapters import ClineChecker, GeminiWriter, KiloReviewer

        import os

        # Availability describes importable workflow stages. Provider/model selection
        # remains delegated to the runtime gateway and is never encoded here.
        gateway_configured = any(
            os.getenv(name)
            for name in (
                "GEMINI_API_KEY",
                "OPENROUTER_API_KEY",
                "GROQ_API_KEY",
                "MISTRAL_API_KEY",
                "GITHUB_MODELS_API_KEY",
            )
        )
        return {
            "workflow": "agent_review_workflow",
            "agents": [
                {"role": "writer", "available": True, "class": GeminiWriter.__name__},
                {"role": "reviewer", "available": True, "class": KiloReviewer.__name__},
                {"role": "checker", "available": True, "class": ClineChecker.__name__},
            ],
            "runtime_model_selection": True,
            "provider_configured": gateway_configured,
            "status": "ready" if gateway_configured else "degraded",
        }
    except ImportError as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Trio pipeline agents not importable: {exc}",
        ) from exc
