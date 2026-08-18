"""Tests for feature-flag driven experimentation (shadow + A/B routing)."""

from unittest.mock import MagicMock, patch

import pytest

from core.llm.advanced_model_router import (
    AdvancedModelRouter,
    ShadowMetricsCollector,
)


@pytest.fixture
def router() -> AdvancedModelRouter:
    return AdvancedModelRouter()


@pytest.mark.asyncio
async def test_shadow_disabled_by_default(router: AdvancedModelRouter):
    with patch(
        "core.feature_flags.feature_flags.model_shadow_enabled",
        return_value=False,
    ), patch(
        "core.feature_flags.feature_flags.model_ab_enabled",
        return_value=False,
    ):
        plan = await router.select_experiment("Explain recursion", "reasoning")
    assert plan.run_shadow is False
    assert plan.shadow_model is None
    assert plan.ab_active is False
    assert plan.ab_variant == "primary"
    assert plan.primary is not None


@pytest.mark.asyncio
async def test_shadow_enabled_routes_candidate(router: AdvancedModelRouter):
    with patch(
        "core.feature_flags.feature_flags.model_shadow_enabled",
        return_value=True,
    ), patch(
        "core.feature_flags.feature_flags.model_ab_enabled",
        return_value=False,
    ):
        plan = await router.select_experiment("Analyze this dataset", "analysis")
    assert plan.run_shadow is True
    assert plan.shadow_model == router.shadow_candidate
    assert plan.ab_active is False


@pytest.mark.asyncio
async def test_ab_split_is_stable_per_prompt_user(router: AdvancedModelRouter):
    with patch(
        "core.feature_flags.feature_flags.model_shadow_enabled",
        return_value=False,
    ), patch(
        "core.feature_flags.feature_flags.model_ab_enabled",
        return_value=True,
    ):
        p1 = await router.select_experiment("unique-prompt-A", "general", user_id="u1")
        p2 = await router.select_experiment("unique-prompt-A", "general", user_id="u1")
        p3 = await router.select_experiment("different-prompt-B", "general", user_id="u1")
    # Same (prompt, user) → same variant bucket
    assert p1.ab_variant == p2.ab_variant
    # Different prompt may differ (not guaranteed, but route plan still valid)
    assert p1.ab_active and p3.ab_active


def test_shadow_metrics_aggregation(router: AdvancedModelRouter):
    router.shadow_candidate = "openai/gpt-4o-mini"
    router.record_shadow_result(
        "openai/gpt-4o-mini", cost=0.001, latency=0.4, quality=0.9, success=True
    )
    router.record_shadow_result(
        "openai/gpt-4o-mini", cost=0.002, latency=0.5, quality=0.8, success=True
    )
    router.record_shadow_result(
        "openai/gpt-4o-mini", success=False
    )  # error, not counted in cost/quality

    metrics = router.get_experiment_metrics()
    snap = metrics["shadow_metrics"]["openai/gpt-4o-mini"]
    assert snap["runs"] == 3
    assert snap["errors"] == 1
    assert snap["error_rate"] == pytest.approx(1 / 3, abs=1e-3)
    assert snap["avg_cost"] == pytest.approx(0.001, abs=1e-6)
    assert snap["avg_quality"] == pytest.approx(0.85, abs=1e-3)


def test_collector_thread_safe_reset():
    c = ShadowMetricsCollector()
    c.record("m1", cost=0.1, latency=0.2, quality=0.7, success=True)
    assert c.snapshot()["m1"]["runs"] == 1
    c.reset()
    assert c.snapshot() == {}
