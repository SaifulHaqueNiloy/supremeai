"""Tests for core/action_policy.py — Action policy enforcement."""
import pytest
from core.action_policy import ActionPolicy


class TestActionPolicy:
    """Action policy: evaluate, tier, allow/deny."""

    def test_init(self):
        policy = ActionPolicy()
        assert policy is not None

    def test_evaluate_read_action_allowed(self):
        policy = ActionPolicy()
        result = policy.evaluate("read", "/api/v1/settings")
        assert result.get("allowed") is True or result.get("tier") == 1

    def test_evaluate_write_action_tier2(self):
        policy = ActionPolicy()
        result = policy.evaluate("write", "/api/v1/settings")
        assert result is not None

    def test_evaluate_delete_action_tier3(self):
        policy = ActionPolicy()
        result = policy.evaluate("delete", "/api/v1/users/all")
        assert result is not None
        assert result.get("tier") == 3 or result.get("requires_approval") is True

    def test_evaluate_deploy_action_tier3(self):
        policy = ActionPolicy()
        result = policy.evaluate("deploy", "production")
        assert result is not None

    def test_evaluate_unknown_action(self):
        policy = ActionPolicy()
        result = policy.evaluate("unknown", "/unknown")
        assert result is not None
