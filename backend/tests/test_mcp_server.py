# backend/tests/test_mcp_server.py
import pytest
from mcp import types

from tools.mcp.mcp_server import handle_call_tool, handle_list_tools


@pytest.mark.anyio
async def test_mcp_list_tools():
    # বাংলা মন্তব্য: MCP সার্ভার তার এভেইলেবল টুলসের স্কিমা ঠিকমতো লিস্ট করছে কিনা তা যাচাইয়ের টেস্ট।
    tools = await handle_list_tools()
    tool_names = [t.name for t in tools]
    assert "get_skill_dependencies" in tool_names
    assert "find_optimal_learning_path" in tool_names
    assert "semantic_tool_search" in tool_names
    assert "synthesize_custom_tool" in tool_names
    assert "execute_smart_tool" in tool_names


@pytest.mark.anyio
async def test_mcp_call_tool_dependencies():
    # বাংলা মন্তব্য: MCP টুল কল করার পর রেসপন্স ফরম্যাট টেক্সট কনটেন্ট আকারে আসছে কিনা তা যাচাই করা।
    res = await handle_call_tool("get_skill_dependencies", {})
    assert len(res) == 1
    assert isinstance(res[0], types.TextContent)
    assert "SupremeAI Skills Graph Context" in res[0].text


@pytest.mark.anyio
async def test_mcp_call_tool_path():
    # বাংলা মন্তব্য: পাথ ফাইন্ডিং MCP টুলের মক ডাটা রেসপন্স ভ্যালিডেশন।
    arguments = {"start_skill": "Python", "end_skill": "FastAPI"}
    res = await handle_call_tool("find_optimal_learning_path", arguments)
    assert len(res) == 1
    assert "Optimal execution path" in res[0].text


@pytest.mark.anyio
async def test_mcp_dynamic_synthesis_and_execution():
    # বাংলা মন্তব্য: অন-দ্য-ফ্লাই JIT কোড জেনারেশন ও স্মার্ট এক্সিকিউশন টেস্ট
    synth_args = {
        "name": "calculate_compound_interest",
        "code": "def run(principal, rate, years):\n    return principal * ((1 + rate) ** years)",
        "entrypoint": "run",
        "description": "Calculates compound interest dynamically",
    }
    synth_res = await handle_call_tool("synthesize_custom_tool", synth_args)
    assert len(synth_res) == 1
    assert '"success": true' in synth_res[0].text

    # স্মার্ট এক্সিকিউশন টেস্ট
    exec_args = {
        "tool_name": "calculate_compound_interest",
        "arguments": {"principal": 1000, "rate": 0.05, "years": 2},
    }
    exec_res = await handle_call_tool("execute_smart_tool", exec_args)
    assert len(exec_res) == 1
    assert '"success": true' in exec_res[0].text
    assert "1102.5" in exec_res[0].text


@pytest.mark.anyio
async def test_mcp_semantic_tool_search():
    # বাংলা মন্তব্য: ভেক্টর সিমিলারিটি টুল সার্চ টেস্ট
    res = await handle_call_tool("semantic_tool_search", {"query": "calculate interest investment", "top_k": 2})
    assert len(res) == 1
    assert "calculate_compound_interest" in res[0].text

