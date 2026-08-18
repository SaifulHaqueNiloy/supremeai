"""Tests for backend/core/queue/task_router.py (closes AUDIT-015: 0% coverage)."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.queue.task_router import TaskRouter


@pytest.fixture
def router() -> TaskRouter:
    return TaskRouter()


# ── process_requirement: pure routing/metadata classification ──────────────
def test_classifies_coding_task(router: TaskRouter):
    out = router.process_requirement("Write a python script to parse csv")
    assert out["task_type"] == "coding"
    assert out["cost_limit"] == 0.01


def test_classifies_image_generation_and_modality(router: TaskRouter):
    out = router.process_requirement("generate an image of a cat")
    assert out["task_type"] == "image_generation"
    assert out["modality"] == "image"


def test_classifies_voice_as_multimodal(router: TaskRouter):
    out = router.process_requirement("transcribe this voice recording")
    assert out["modality"] == "multimodal"
    assert out["reasoning_depth"] == "medium"


def test_classifies_scrape_and_system(router: TaskRouter):
    assert router.process_requirement("scrape the news site")["task_type"] == "web_scraping_local"
    assert router.process_requirement("open a terminal")["task_type"] == "system_control"
    assert router.process_requirement("just say hello")["task_type"] == "general"


def test_token_budget_by_length(router: TaskRouter):
    assert router.process_requirement("x" * 10)["token_budget"] == "small"
    assert router.process_requirement("x" * 1000)["token_budget"] == "medium"
    assert router.process_requirement("x" * 3000)["token_budget"] == "large"


def test_reasoning_depth_high_for_math(router: TaskRouter):
    assert router.process_requirement("solve this math problem")["reasoning_depth"] == "high"


def test_analyze_and_route_delegates(router: TaskRouter):
    out = router.analyze_and_route("write code", max_cost=0.05)
    assert out["task_type"] == "coding"
    assert out["cost_limit"] == 0.05


# ── route_and_dispatch: async dispatch with mocked collaborators ───────────
@pytest.mark.asyncio
async def test_dispatch_routes_to_local_executor(router: TaskRouter):
    router.local_executor = MagicMock()
    router.local_executor.execute_local_code = AsyncMock(return_value={"output": "ok"})
    with patch("core.queue.task_router.cost_guard") as cg:
        cg.validate_budget = AsyncMock(return_value=True)
        result = await router.route_and_dispatch(
            {"task_type": "coding", "code": "print(1)", "cost_limit": 0.01}
        )
    assert result["output"] == "ok"
    assert result["cost"] == 0.01


@pytest.mark.asyncio
async def test_dispatch_rejected_when_budget_exceeded(router: TaskRouter):
    with patch("core.queue.task_router.cost_guard") as cg:
        cg.validate_budget = AsyncMock(return_value=False)
        result = await router.route_and_dispatch(
            {"task_type": "coding", "cost_limit": 1.0}
        )
    assert result["status"] == "rejected"
    assert result["reason"] == "budget_exceeded"
    assert result["tier"] == "premium"


@pytest.mark.asyncio
async def test_dispatch_continues_when_costguard_errors(router: TaskRouter):
    router.local_executor = MagicMock()
    router.local_executor.execute_local_code = AsyncMock(return_value={"output": "ran"})
    with patch("core.queue.task_router.cost_guard") as cg:
        cg.validate_budget = AsyncMock(side_effect=RuntimeError("redis down"))
        result = await router.route_and_dispatch(
            {"task_type": "local", "code": "x", "cost_limit": 0.01}
        )
    assert result["output"] == "ran"


@pytest.mark.asyncio
async def test_dispatch_routes_to_cloud_sandbox(router: TaskRouter):
    router.cloud_orchestrator = MagicMock()
    router.cloud_orchestrator.create_sandbox = AsyncMock(return_value={"id": "sb-1"})
    with patch("core.queue.task_router.cost_guard") as cg:
        cg.validate_budget = AsyncMock(return_value=True)
        result = await router.route_and_dispatch(
            {"task_type": "heavy_cloud_sandbox", "config": {}, "cost_limit": 0.1}
        )
    assert result["status"] == "success"
    assert result["data"] == {"id": "sb-1"}


@pytest.mark.asyncio
async def test_dispatch_unknown_route_raises(router: TaskRouter):
    with patch("core.queue.task_router.cost_guard") as cg:
        cg.validate_budget = AsyncMock(return_value=True)
        with pytest.raises(ValueError):
            await router.route_and_dispatch({"task_type": "bogus", "cost_limit": 0.01})
