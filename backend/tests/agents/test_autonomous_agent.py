"""Tests for agents/autonomous_agent.py — Autonomous agent execution."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from agents.autonomous_agent import AutonomousAgent


class TestAutonomousAgent:
    """Autonomous agent: plan, execute, verify."""

    def test_init(self):
        agent = AutonomousAgent(goal="test goal")
        assert agent is not None

    @pytest.mark.asyncio
    async def test_plan_returns_steps(self):
        agent = AutonomousAgent(goal="Write hello world")
        plan = await agent.plan()
        assert plan is not None
        assert isinstance(plan, (list, dict))

    @pytest.mark.asyncio
    async def test_execute_step(self):
        agent = AutonomousAgent(goal="test")
        result = await agent.execute_step({"action": "noop"})
        assert result is not None

    @pytest.mark.asyncio
    async def test_verify_result(self):
        agent = AutonomousAgent(goal="test")
        result = await agent.verify({"output": "done"})
        assert isinstance(result, (bool, dict))

    def test_set_goal(self):
        agent = AutonomousAgent(goal="initial")
        agent.set_goal("new goal")
        assert agent.goal == "new goal"

    @pytest.mark.asyncio
    async def test_run_full_cycle(self):
        agent = AutonomousAgent(goal="simple task")
        result = await agent.run()
        assert result is not None
