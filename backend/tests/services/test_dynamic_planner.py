"""Tests for services/dynamic_planner.py — Dynamic planning service."""
import pytest
from services.dynamic_planner import DynamicPlanner


class TestDynamicPlanner:
    """Dynamic planner: decompose, plan, execute."""

    def test_init(self):
        planner = DynamicPlanner()
        assert planner is not None

    def test_decompose_simple_task(self):
        planner = DynamicPlanner()
        result = planner.decompose("Write a hello world function")
        assert result is not None
        assert isinstance(result, (list, dict))

    def test_decompose_complex_task(self):
        planner = DynamicPlanner()
        result = planner.decompose("Build a REST API with authentication and database")
        assert result is not None
        if isinstance(result, list):
            assert len(result) >= 1

    def test_decompose_empty_task(self):
        planner = DynamicPlanner()
        result = planner.decompose("")
        assert result is not None

    def test_plan_returns_steps(self):
        planner = DynamicPlanner()
        result = planner.plan("Fix the bug in auth module")
        assert result is not None
        assert "steps" in result or isinstance(result, list)
