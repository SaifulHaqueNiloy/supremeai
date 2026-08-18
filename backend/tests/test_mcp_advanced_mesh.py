import pytest
from tools.mcp.mcp_mesh_engine import (
    DynamicMCPRegistry,
    SelfHealingToolExecutor,
    SemanticToolRouter,
    _hash_vectorize,
    _cosine_similarity,
)


def test_hash_vectorize_and_cosine():
    v1 = _hash_vectorize("search web browsing internet")
    v2 = _hash_vectorize("browse web and search online")
    v3 = _hash_vectorize("database migration postgres sql")

    sim_related = _cosine_similarity(v1, v2)
    sim_unrelated = _cosine_similarity(v1, v3)

    assert sim_related > sim_unrelated
    assert len(v1) == 64


def test_semantic_tool_router_ranking():
    router = SemanticToolRouter()
    router.register_tool_index(
        "web_browser",
        "Automated browser for opening web pages and taking snapshots",
        ["playwright", "browser", "web"],
        {"type": "object", "properties": {}},
    )
    router.register_tool_index(
        "sql_runner",
        "Executes PostgreSQL queries and database migrations",
        ["sql", "database", "postgres"],
        {"type": "object", "properties": {}},
    )
    router.register_tool_index(
        "linter",
        "Lints and checks python code for syntax errors",
        ["code", "linter", "python"],
        {"type": "object", "properties": {}},
    )

    # Search for browser related query
    results = router.search_relevant_tools("open login website with browser", top_k=1)
    assert len(results) == 1
    assert results[0]["name"] == "web_browser"

    # Search for database query
    db_results = router.search_relevant_tools("run sql migration query", top_k=1)
    assert len(db_results) == 1
    assert db_results[0]["name"] == "sql_runner"


def test_jit_tool_synthesis_safety():
    registry = DynamicMCPRegistry()

    # Dangerous code rejection
    bad_code = "import os.system\ndef run():\n    pass"
    res_bad = registry.synthesize_tool("bad_tool", bad_code, "run", "Should fail")
    assert res_bad["success"] is False
    assert "Disallowed unsafe module import" in res_bad["error"]

    # Safe math code synthesis
    good_code = "def add(a, b):\n    return a + b"
    res_good = registry.synthesize_tool(
        "safe_add",
        good_code,
        "add",
        "Adds two numbers",
        input_schema={
            "type": "object",
            "properties": {
                "a": {"type": "integer"},
                "b": {"type": "integer"},
            },
        },
    )
    assert res_good["success"] is True
    assert registry.get_tool("safe_add") is not None


@pytest.mark.anyio
async def test_self_healing_type_coercion_and_execution():
    registry = DynamicMCPRegistry()
    executor = SelfHealingToolExecutor(registry)

    # Register tool expecting integer
    def multiply(factor: int, times: int):
        return factor * times

    registry.register(
        "multiply",
        multiply,
        description="Multiplies two ints",
        input_schema={
            "type": "object",
            "properties": {
                "factor": {"type": "integer"},
                "times": {"type": "integer"},
            },
        },
    )

    # Pass strings instead of ints -> Self-healing auto coerces
    res = await executor.execute("multiply", {"factor": "5", "times": "3"})
    assert res["success"] is True
    assert res["result"] == 15
    assert res["healed"] is False


@pytest.mark.anyio
async def test_self_healing_fallback_recovery():
    registry = DynamicMCPRegistry()
    executor = SelfHealingToolExecutor(registry)

    # Primary tool fails
    def flaky_tool():
        raise RuntimeError("Primary API network timeout")

    # Fallback tool succeeds
    def backup_tool():
        return "Backup data fetched successfully"

    registry.register("flaky_service", flaky_tool)
    registry.register("backup_service", backup_tool)

    # Configure fallback link
    executor.set_fallback("flaky_service", "backup_service")

    # Execute primary -> should automatically failover to backup
    res = await executor.execute("flaky_service", {})
    assert res["success"] is True
    assert res["healed"] is True
    assert res["tool"] == "backup_service"
    assert res["result"] == "Backup data fetched successfully"


@pytest.mark.anyio
async def test_context_graph_mcp_sync():
    from memory.context_graph_service import context_graph_service

    registry = DynamicMCPRegistry()
    executor = SelfHealingToolExecutor(registry)

    # 1. JIT Synthesize
    synth_res = registry.synthesize_tool(
        "graph_synced_tool",
        "def run(x):\n    return x * 10",
        "run",
        "Tool that syncs to context graph",
    )
    assert synth_res["success"] is True

    # Verify node in Context Graph
    skill_node = context_graph_service.get_node("skill_mcp_graph_synced_tool")
    assert skill_node is not None
    assert skill_node.node_type == "Skill"

    # 2. Execute tool
    exec_res = await executor.execute("graph_synced_tool", {"x": 5})
    assert exec_res["success"] is True
    assert exec_res["result"] == 50

    # Verify execution memory node created and connected
    subgraph = context_graph_service.get_multi_hop_context("skill_mcp_graph_synced_tool", max_depth=1)
    assert len(subgraph.nodes) >= 1

