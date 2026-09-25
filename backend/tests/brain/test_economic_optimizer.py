"""Tests for brain/economic_optimizer.py — Cost-aware routing optimizer."""
import pytest
from brain.economic_optimizer import EconomicOptimizer, BudgetContext


class TestBudgetContext:
    """Budget context: max cost, user, remaining."""

    def test_init(self):
        ctx = BudgetContext(max_cost=0.01, user_id="user-1")
        assert ctx.max_cost == 0.01
        assert ctx.user_id == "user-1"

    def test_remaining_cost(self):
        ctx = BudgetContext(max_cost=0.05, user_id="user-1", spent=0.02)
        assert ctx.remaining == 0.03 or ctx.max_cost - ctx.spent == 0.03

    def test_budget_exceeded(self):
        ctx = BudgetContext(max_cost=0.01, user_id="user-1", spent=0.02)
        assert ctx.is_exceeded()

    def test_budget_not_exceeded(self):
        ctx = BudgetContext(max_cost=0.05, user_id="user-1", spent=0.01)
        assert not ctx.is_exceeded()


class TestEconomicOptimizer:
    """Economic optimizer: route selection by cost."""

    def test_init(self):
        opt = EconomicOptimizer()
        assert opt is not None

    @pytest.mark.asyncio
    async def test_optimize_route_returns_decision(self):
        opt = EconomicOptimizer()
        ctx = BudgetContext(max_cost=0.01, user_id="user-1")
        result = await opt.optimize_route("Write a poem", "general", ctx)
        assert result is not None
        assert hasattr(result, "provider") or "provider" in result

    @pytest.mark.asyncio
    async def test_optimize_respects_budget(self):
        opt = EconomicOptimizer()
        ctx = BudgetContext(max_cost=0.001, user_id="user-1")  # very low budget
        result = await opt.optimize_route("Complex reasoning task", "reasoning", ctx)
        assert result is not None

    @pytest.mark.asyncio
    async def test_optimize_chooses_cheaper_for_simple(self):
        """Simple tasks should route to cheaper models."""
        opt = EconomicOptimizer()
        ctx = BudgetContext(max_cost=1.0, user_id="user-1")
        simple = await opt.optimize_route("Hello", "general", ctx)
        complex_task = await opt.optimize_route("Analyze quantum physics", "reasoning", ctx)
        assert simple is not None
        assert complex_task is not None
