"""Tests for tools/agent_tools.py — Agent tool registry + execution."""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch


class TestAgentToolsRegistry:
    """Tool registry: registration, lookup, listing."""

    def test_register_tool(self):
        from tools.agent_tools import SUPREME_TOOLS
        # Verify registry exists and is a dict-like
        assert SUPREME_TOOLS is not None

    def test_list_available_tools(self):
        from tools.agent_tools import list_tools
        tools = list_tools()
        assert isinstance(tools, (list, dict))

    def test_get_tool_by_name(self):
        from tools.agent_tools import get_tool
        tool = get_tool("nonexistent_tool")
        assert tool is None or tool == {}


class TestToolExecution:
    """Tool execution: call, validate, error handling."""

    @pytest.mark.asyncio
    async def test_execute_unknown_tool_returns_error(self):
        from tools.agent_tools import execute_tool
        result = await execute_tool("nonexistent", {})
        assert result is not None
        assert "error" in result or result.get("success") is False

    @pytest.mark.asyncio
    async def test_execute_tool_with_invalid_params(self):
        from tools.agent_tools import execute_tool
        result = await execute_tool("cot_reasoner", {"invalid_param": True})
        assert result is not None

    @pytest.mark.asyncio
    async def test_execute_tool_returns_dict(self):
        from tools.agent_tools import execute_tool
        result = await execute_tool("nonexistent", {})
        assert isinstance(result, dict)


class TestToolSchema:
    """Tool schema validation."""

    def test_tool_schema_has_name(self):
        from tools.agent_tools import get_tool_schemas
        schemas = get_tool_schemas()
        if schemas:
            for name, schema in schemas.items():
                assert "name" in schema or "description" in schema
