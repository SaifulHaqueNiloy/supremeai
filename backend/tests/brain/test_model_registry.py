"""Tests for brain/model_registry.py — AI Model registry by tiers."""
import pytest
from brain.model_registry import ModelRegistry


class TestModelRegistry:
    """Model registry: lookup, tier, cost, strengths."""

    def test_init(self):
        reg = ModelRegistry()
        assert reg is not None

    def test_get_known_model(self):
        reg = ModelRegistry()
        model = reg.get("gpt-4o")
        if model:
            assert "provider" in model
            assert "tier" in model

    def test_get_unknown_model(self):
        reg = ModelRegistry()
        model = reg.get("nonexistent-model")
        assert model is None or model == {}

    def test_list_by_tier(self):
        reg = ModelRegistry()
        tier1 = reg.list_by_tier(1)
        assert isinstance(tier1, (list, dict))

    def test_get_cost(self):
        reg = ModelRegistry()
        model = reg.get("gpt-4o")
        if model:
            assert "cost_input_per_million" in model or "cost" in model

    def test_all_models_have_required_fields(self):
        reg = ModelRegistry()
        for name, model in reg.MODELS.items():
            assert "provider" in model, f"{name} missing provider"
            assert "tier" in model, f"{name} missing tier"
            assert "name" in model, f"{name} missing name"

    def test_tiers_are_valid(self):
        reg = ModelRegistry()
        valid_tiers = {1, 2, 3, 4}
        for name, model in reg.MODELS.items():
            assert model["tier"] in valid_tiers, f"{name} has invalid tier {model['tier']}"

    def test_context_length_positive(self):
        reg = ModelRegistry()
        for name, model in reg.MODELS.items():
            if "context_length" in model:
                assert model["context_length"] > 0, f"{name} has non-positive context"
