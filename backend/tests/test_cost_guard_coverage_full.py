# tests/test_cost_guard_coverage_full.py
"""Comprehensive unit tests for backend/core/cost_guard.py targeting 80%+ line coverage."""

import time
from unittest.mock import MagicMock, patch

import pytest

from core.cost_guard import CostGuard


@pytest.fixture
def cost_guard_instance():
    return CostGuard(monthly_budget=10.0, alert_threshold=0.8)


def test_init_defaults():
    cg = CostGuard()
    assert cg.monthly_budget == 100.0
    assert cg.alert_threshold == 0.8
    assert cg.current_spend == 0.0


def test_record_cost(cost_guard_instance):
    cost_guard_instance.record_cost(1.5, task_type="coding", provider="openai")
    assert cost_guard_instance.current_spend == 1.5
    assert len(cost_guard_instance.history) == 1
    assert cost_guard_instance.history[0]["cost"] == 1.5
    assert cost_guard_instance.history[0]["task_type"] == "coding"
    assert cost_guard_instance.history[0]["provider"] == "openai"


def test_can_proceed_within_budget(cost_guard_instance):
    cost_guard_instance.record_cost(5.0)
    assert cost_guard_instance.can_proceed(estimated_cost=2.0) is True


def test_can_proceed_exceeds_budget(cost_guard_instance):
    cost_guard_instance.record_cost(9.0)
    # Estimated cost 2.0 would push total spend to 11.0 > 10.0 budget
    assert cost_guard_instance.can_proceed(estimated_cost=2.0) is False


def test_alert_triggered(cost_guard_instance):
    with patch("core.cost_guard.logger") as mock_logger:
        # Spend 8.5 on a 10.0 budget (85% > 80% threshold)
        cost_guard_instance.record_cost(8.5)
        assert cost_guard_instance.current_spend == 8.5
        mock_logger.warning.assert_called()


def test_get_summary(cost_guard_instance):
    cost_guard_instance.record_cost(2.0, provider="groq")
    cost_guard_instance.record_cost(3.0, provider="gemini")
    summary = cost_guard_instance.get_summary()

    assert summary["monthly_budget"] == 10.0
    assert summary["current_spend"] == 5.0
    assert summary["remaining_budget"] == 5.0
    assert summary["total_requests"] == 2
    assert summary["utilization_percentage"] == 50.0


def test_reset_monthly_spend(cost_guard_instance):
    cost_guard_instance.record_cost(7.0)
    assert cost_guard_instance.current_spend == 7.0
    cost_guard_instance.reset_monthly_spend()
    assert cost_guard_instance.current_spend == 0.0
    assert len(cost_guard_instance.history) == 0
