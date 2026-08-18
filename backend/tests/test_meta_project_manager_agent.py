"""Unit and API integration tests for AOD Meta-Project Manager Engine.

Verifies goal decomposition, skill acquisition, sub-agent spawning, synthesis, and API routes.
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from agents.meta_project_manager_agent import (
    GoalDecomposer,
    MetaProjectManager,
    ProjectStatus,
    SkillAcquisitionManager,
    TaskStatus,
)
from api.routes.aod import router as aod_router


@pytest.fixture
def aod_manager():
    return MetaProjectManager()


def test_goal_decomposer_creates_dag_tasks():
    goal = "Build a high-performance payment gateway webhook microservice with HMAC verification"
    tasks = GoalDecomposer.decompose(goal=goal, project_id="proj-test-101")

    assert len(tasks) >= 4
    agent_types = [t.agent_type for t in tasks]
    assert "Architect" in agent_types
    assert "Coder" in agent_types
    assert "Sentinel" in agent_types
    assert "QATester" in agent_types

    # Verify dependency structure: Coder depends on Architect
    arch_task = [t for t in tasks if t.agent_type == "Architect"][0]
    coder_task = [t for t in tasks if t.agent_type == "Coder"][0]
    assert arch_task.task_id in coder_task.dependencies


def test_skill_acquisition_catalog():
    skills = SkillAcquisitionManager.acquire_skills(["api_design", "secret_hunter", "unknown_custom_skill"])
    assert len(skills) == 3
    assert skills[0]["name"] == "api_design"
    assert skills[0]["category"] == "Architecture"
    assert skills[1]["name"] == "secret_hunter"
    assert skills[1]["category"] == "Security"
    assert skills[2]["name"] == "unknown_custom_skill"
    assert skills[2]["category"] == "General"


@pytest.mark.asyncio
async def test_meta_project_manager_end_to_end(aod_manager: MetaProjectManager):
    goal = "Create a scalable token bucket rate limiter for FastAPI endpoints"
    project = await aod_manager.create_and_execute_project(
        goal=goal,
        project_name="RateLimiterMicroservice",
        tenant_id="tenant-omega",
    )

    assert project.status == ProjectStatus.COMPLETED
    assert len(project.tasks) >= 4
    assert all(t.status == TaskStatus.COMPLETED for t in project.tasks)
    assert project.final_deliverables is not None
    assert "deliverables" in project.final_deliverables
    assert project.final_deliverables["ready_for_production"] is True

    # Check project fetch from manager
    fetched = aod_manager.get_project(project.project_id)
    assert fetched is not None
    assert fetched.project_name == "RateLimiterMicroservice"

    # Check listing
    projects_list = aod_manager.list_projects(tenant_id="tenant-omega")
    assert len(projects_list) >= 1
    assert projects_list[0]["project_id"] == project.project_id


def test_aod_api_routes():
    app = FastAPI()
    app.include_router(aod_router)
    client = TestClient(app)

    # 1. Skills catalog
    res_skills = client.get("/api/aod/skills")
    assert res_skills.status_code == 200
    skills_data = res_skills.json()
    assert skills_data["status"] == "success"
    assert skills_data["skills_count"] > 0
    assert "api_design" in skills_data["skills"]

    # 2. Create Project
    res_create = client.post(
        "/api/aod/create-project",
        json={
            "goal": "Build an async event bus with Redis pub/sub and WebSocket streaming",
            "project_name": "EventBusStreamer",
            "tenant_id": "test-tenant",
        },
    )
    assert res_create.status_code == 200
    create_data = res_create.json()
    assert create_data["status"] == "success"
    project_id = create_data["project"]["project_id"]
    assert create_data["project"]["status"] == "completed"

    # 3. Get Project Status
    res_get = client.get(f"/api/aod/projects/{project_id}")
    assert res_get.status_code == 200
    get_data = res_get.json()
    assert get_data["project"]["project_id"] == project_id
    assert len(get_data["project"]["tasks"]) >= 4

    # 4. List Projects
    res_list = client.get("/api/aod/projects?tenant_id=test-tenant")
    assert res_list.status_code == 200
    list_data = res_list.json()
    assert list_data["count"] >= 1

    # 5. Non-existent Project returns 404
    res_404 = client.get("/api/aod/projects/non-existent-id")
    assert res_404.status_code == 404
