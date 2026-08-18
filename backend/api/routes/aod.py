"""Agent-Oriented Development (AOD) API Routes for SupremeAI 2.0.

বাংলা মন্তব্য: গোল ভিত্তিক স্বয়ংক্রিয় প্রজেক্ট ক্রিয়েশন, সাব-এজেন্ট মনিটরিং এবং
ডেলিভারেবল রিট্রিভালের এপিআই রাউটস।
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from loguru import logger
from pydantic import BaseModel, Field

from agents.meta_project_manager_agent import (
    SkillAcquisitionManager,
    meta_project_manager,
)

router = APIRouter(
    prefix="/api/aod",
    tags=["aod-engine"],
)


class CreateProjectRequest(BaseModel):
    goal: str = Field(..., min_length=5, max_length=2000, description="High-level user goal or project objective")
    project_name: str | None = Field(default=None, max_length=150)
    tenant_id: str = Field(default="default")


@router.post("/create-project")
async def create_aod_project(req: CreateProjectRequest) -> dict[str, Any]:
    """
    Initiates autonomous Agent-Oriented Development (AOD) workflow for a specified goal.
    Decomposes goal, acquires skills, spawns sub-agents, and produces synthesized deliverables.
    """
    try:
        project = await meta_project_manager.create_and_execute_project(
            goal=req.goal,
            project_name=req.project_name,
            tenant_id=req.tenant_id,
        )
        return {
            "status": "success",
            "project": project.to_dict(),
        }
    except Exception as e:
        logger.error(f"[AOD Route] Failed to execute project: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/projects/{project_id}")
async def get_aod_project_status(project_id: str) -> dict[str, Any]:
    """Returns the full execution status, DAG tasks, and final deliverables of an AOD project."""
    project = meta_project_manager.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found.")
    return {
        "status": "success",
        "project": project.to_dict(),
    }


@router.get("/projects")
async def list_aod_projects(
    tenant_id: str = Query(default="default"),
    limit: int = Query(default=20, ge=1, le=100),
) -> dict[str, Any]:
    """Lists recent AOD projects executed on the platform."""
    projects = meta_project_manager.list_projects(tenant_id=tenant_id, limit=limit)
    return {
        "status": "success",
        "count": len(projects),
        "projects": projects,
    }


@router.get("/skills")
async def list_aod_skills() -> dict[str, Any]:
    """Returns the catalog of discoverable skills for dynamic sub-agent acquisition."""
    skills = SkillAcquisitionManager.AVAILABLE_SKILLS
    return {
        "status": "success",
        "skills_count": len(skills),
        "skills": skills,
    }
