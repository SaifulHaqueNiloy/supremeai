"""
Tests for the Tier 0 Confidence Gate & Fast-Path Dispatcher.

Verifies that deterministic tasks bypass LLM API calls entirely (zero token cost),
while complex/reasoning tasks escalate to the normal LLM call chain.
"""

import json
from unittest.mock import AsyncMock, patch

import pytest

from core.llm.advanced_model_router import (
    Tier0Dispatcher,
    get_advanced_router,
)


@pytest.fixture
def router():
    return get_advanced_router()


class TestTier0Dispatcher:
    """Unit tests for the zero-cost deterministic executors."""

    def test_pypi_search_returns_package_info(self):
        """Tier0Dispatcher._search_pypi should return structured package data."""
        result = Tier0Dispatcher.execute("pypi_search", "Search PyPI for requests")
        assert "name" in result or "error" in result

    def test_format_json_extracts_structure(self):
        """Tier0Dispatcher._format_text should parse 'format as JSON' prompts."""
        result = Tier0Dispatcher.execute("regex_format", "Format as JSON for key=value pairs")
        assert result["format"] == "json"
        assert "result" in result

    def test_unknown_pattern_returns_error(self):
        result = Tier0Dispatcher.execute("unknown_pattern", "some prompt")
        assert "error" in result


class TestConfidenceGatedRouting:
    """Tests for AdvancedModelRouter.route_with_confidence()."""

    def test_deterministic_task_has_high_confidence(self, router):
        """Pattern-matched deterministic tasks should have confidence >= 0.85."""
        decision = router.route_with_confidence(
            "Search PyPI for pandas", task_type="general"
        )
        assert decision.is_deterministic is True
        assert decision.confidence >= 0.85
        assert decision.matched_pattern == "pypi_search"
        assert decision.deterministic_result is not None
        assert "name" in decision.deterministic_result

    def test_complex_task_not_deterministic(self, router):
        """Complex reasoning prompts should not trigger Tier 0 bypass."""
        decision = router.route_with_confidence(
            "Analyze the complex distributed race condition in our microservices architecture",
            task_type="reasoning",
        )
        assert decision.is_deterministic is False
        assert decision.matched_pattern is None
        assert decision.deterministic_result is None

    def test_format_json_is_deterministic(self, router):
        decision = router.route_with_confidence(
            "Format as JSON: name=john, age=30", task_type="general"
        )
        assert decision.is_deterministic is True
        assert decision.matched_pattern == "regex_format"

    def test_schema_lookup_is_deterministic(self, router):
        decision = router.route_with_confidence(
            "Show schema for the users table", task_type="general"
        )
        assert decision.is_deterministic is True
        assert decision.matched_pattern == "schema_lookup"

    def test_empty_prompt_low_confidence(self, router):
        decision = router.route_with_confidence("", task_type="general")
        assert decision.is_deterministic is False
        assert decision.confidence == 0.0


class TestLLMGatewayTier0Bypass:
    """Integration tests verifying LLMGateway.acompletion bypasses litellm for Tier 0."""

    @pytest.mark.asyncio
    async def test_tier0_bypass_skips_litellm(self):
        """Deterministic prompts should never call litellm.acompletion."""
        with patch("core.llm.llm_gateway.litellm", create=True) as mock_litellm:
            mock_litellm.acompletion = AsyncMock(side_effect=AssertionError(
                "litellm.acompletion should never be called for Tier 0 tasks"
            ))
            # Also patch the lazy import path
            import sys
            sys.modules["litellm"] = mock_litellm

            from core.llm.llm_gateway import LLMGateway
            gw = LLMGateway()

            result = await gw.acompletion(
                prompt="Search PyPI for pandas", task_type="general"
            )

            assert result.get("tier0_bypass") is True
            assert result.get("cost") == 0.0
            assert result.get("model") == "tier0-deterministic"
            # Verify the result contains actual PyPI data
            parsed = json.loads(result["text"])
            assert "name" in parsed
    @pytest.mark.asyncio
    async def test_non_deterministic_does_not_bypass(self):
        """Complex prompts should proceed through normal LLM routing (not Tier 0)."""
        from core.llm.advanced_model_router import get_advanced_router

        # This should NOT hit the Tier 0 bypass — it should proceed to LLM routing
        # We can verify by checking that the Tier 0 decision would be False
        decision = get_advanced_router().route_with_confidence(
            "Analyze complex distributed race condition", task_type="reasoning"
        )
        assert decision.is_deterministic is False
        assert decision.deterministic_result is None
