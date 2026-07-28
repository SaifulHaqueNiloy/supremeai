"""
Coverage tests for tools/self_planner.py.
Target: 100% line coverage.

সেলফ-প্ল্যানার মডিউলের সকল ফাংশন ও ব্রাঞ্চ কভার করা হয়েছে।
"""

import json
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)


class TestSelfPlannerInit:
    """Tests for SelfPlanner.__init__."""

    def test_init_without_llm_client(self):
        """SelfPlanner should initialize without an LLM client."""
        from tools.self_planner import SelfPlanner

        planner = SelfPlanner()
        assert planner.llm_client is None
        assert planner.active_tasks == set()

    def test_init_with_llm_client(self):
        """SelfPlanner should initialize with an LLM client."""
        from tools.self_planner import SelfPlanner

        mock_client = MagicMock()
        planner = SelfPlanner(llm_client=mock_client)
        assert planner.llm_client == mock_client


class TestSelfPlannerGeneratePlan:
    """Tests for SelfPlanner.generate_plan."""

    @pytest.mark.asyncio
    async def test_generate_plan_success(self):
        """generate_plan should return a valid DiGraph for successful LLM response."""
        from tools.self_planner import SelfPlanner

        planner = SelfPlanner()
        plan_data = [
            {"id": "task1", "description": "First task", "depends_on": []},
            {"id": "task2", "description": "Second task", "depends_on": ["task1"]},
        ]

        with patch.object(planner, "llm_client", None), patch("tools.self_planner.ModelRouter") as mock_router:
            mock_router_instance = AsyncMock()
            mock_router.return_value = mock_router_instance
            mock_router_instance.async_route_and_generate.return_value = {"text": json.dumps(plan_data)}

            graph = await planner.generate_plan("Build a feature")
            assert graph is not None
            assert graph.number_of_nodes() == 2
            assert graph.has_edge("task1", "task2")

    @pytest.mark.asyncio
    async def test_generate_plan_llm_error(self):
        """generate_plan should raise RuntimeError on LLM failure."""
        from tools.self_planner import SelfPlanner

        planner = SelfPlanner()

        with patch("tools.self_planner.ModelRouter") as mock_router:
            mock_router_instance = AsyncMock()
            mock_router.return_value = mock_router_instance
            mock_router_instance.async_route_and_generate.side_effect = Exception("LLM down")

            with pytest.raises(RuntimeError, match="Agent planning failed"):
                await planner.generate_plan("Test objective")

    @pytest.mark.asyncio
    async def test_generate_plan_invalid_json(self):
        """generate_plan should raise on invalid JSON response."""
        from tools.self_planner import SelfPlanner

        planner = SelfPlanner()

        with patch("tools.self_planner.ModelRouter") as mock_router:
            mock_router_instance = AsyncMock()
            mock_router.return_value = mock_router_instance
            mock_router_instance.async_route_and_generate.return_value = {"text": "not valid json"}

            with pytest.raises(json.JSONDecodeError):
                await planner.generate_plan("Test")

    @pytest.mark.asyncio
    async def test_generate_plan_non_list_response(self):
        """generate_plan should raise TypeError if response is not a list."""
        from tools.self_planner import SelfPlanner

        planner = SelfPlanner()

        with patch("tools.self_planner.ModelRouter") as mock_router:
            mock_router_instance = AsyncMock()
            mock_router.return_value = mock_router_instance
            mock_router_instance.async_route_and_generate.return_value = {"text": json.dumps({"not": "a list"})}

            with pytest.raises(TypeError, match="not a JSON array"):
                await planner.generate_plan("Test")

    @pytest.mark.asyncio
    async def test_generate_plan_empty_list(self):
        """generate_plan should handle an empty plan list."""
        from tools.self_planner import SelfPlanner

        planner = SelfPlanner()

        with patch("tools.self_planner.ModelRouter") as mock_router:
            mock_router_instance = AsyncMock()
            mock_router.return_value = mock_router_instance
            mock_router_instance.async_route_and_generate.return_value = {"text": json.dumps([])}

            graph = await planner.generate_plan("Test")
            assert graph.number_of_nodes() == 0


class TestSelfPlannerValidatePlan:
    """Tests for SelfPlanner.validate_plan."""

    @pytest.mark.asyncio
    async def test_validate_plan_valid(self):
        """validate_plan should return True for a valid plan."""
        from tools.self_planner import SelfPlanner

        planner = SelfPlanner()

        with patch("tools.self_planner.ModelRouter") as mock_router:
            mock_router_instance = AsyncMock()
            mock_router.return_value = mock_router_instance
            mock_router_instance.async_route_and_generate.return_value = {
                "text": json.dumps({"valid": True, "issues": []})
            }

            import networkx as nx

            graph = nx.DiGraph()
            graph.add_node("task1", description="Test")

            result = await planner.validate_plan(graph)
            assert result is not None


class TestSelfPlannerExecutePlan:
    """Tests for SelfPlanner.execute_plan."""

    @pytest.mark.asyncio
    async def test_execute_plan_empty_graph(self):
        """execute_plan should handle empty graph gracefully."""
        from tools.self_planner import SelfPlanner

        planner = SelfPlanner()
        import networkx as nx

        graph = nx.DiGraph()

        result = await planner.execute_plan(graph)
        assert result == []

    @pytest.mark.asyncio
    async def test_execute_plan_with_tasks(self):
        """execute_plan should execute tasks in order."""
        from tools.self_planner import SelfPlanner

        planner = SelfPlanner()
        import networkx as nx

        graph = nx.DiGraph()
        graph.add_node("task1", description="Task 1")
        graph.add_node("task2", description="Task 2")
        graph.add_edge("task1", "task2")

        result = await planner.execute_plan(graph)
        assert isinstance(result, list)
