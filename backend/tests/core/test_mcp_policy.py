"""Tests for the MCP Policy Engine (backend/core/mcp_policy.py).

বাংলা মন্তব্য: Python mirror এর জন্য টেস্ট — TS risk.engine.ts এবং policy.engine.ts
এর সাথে consistency নিশ্চিত করে।

Constitution Compliance:
  - Law #16 (Verify Before Trust): policy engine logic verified before deployment
"""

import importlib.util
import sys
from pathlib import Path

# ── Fixtures ──────────────────────────────────────────────────────────

# Resolve project root from this test file location (works regardless of cwd)
# tests/core/test_mcp_policy.py → tests/core/ → tests/ → backend/ → project root
TEST_FILE = Path(__file__).resolve()
PROJECT_ROOT = TEST_FILE.parents[3]
POLICY_PATH = PROJECT_ROOT / "backend" / "core" / "mcp_policy.py"
AUDIT_PATH = PROJECT_ROOT / "backend" / "core" / "mcp_audit.py"


def _load_policy_module():
    """Load mcp_policy without triggering full backend init."""
    spec = importlib.util.spec_from_file_location("core.mcp_policy", str(POLICY_PATH))
    mod = importlib.util.module_from_spec(spec)
    # Prevent full backend init by stubbing logging_config
    sys.modules.setdefault("core.logging_config", type(sys)("core.logging_config"))
    spec.loader.exec_module(mod)
    return mod


# ── Risk Level Tests ──────────────────────────────────────────────────


def test_read_only_tools_are_r0():
    mod = _load_policy_module()
    read_only_tools = [
        "read_graph",
        "search_nodes",
        "open_nodes",
        "search_semantic",
        "get_similar_tasks",
        "get_recent_episodes",
        "build_context",
        "get_session_stats",
        "recall_facts",
        "search_learned_facts",
        "get_skill_dependencies",
        "find_optimal_learning_path",
        "get_render_deploy_preflight",
        "get_render_account_status",
    ]
    for tool in read_only_tools:
        decision, risk = mod.evaluate_tool(tool)
        assert risk == "R0", f"{tool} should be R0, got {risk}"
        assert decision == "ALLOW", f"{tool} should be ALLOW, got {decision}"


def test_safe_writes_are_r1():
    mod = _load_policy_module()
    safe_write_tools = [
        "create_entities",
        "create_relations",
        "add_observations",
        "store_document",
        "ingest_document_rag",
        "record_task",
        "remember_fact",
        "save_learned_fact",
    ]
    for tool in safe_write_tools:
        decision, risk = mod.evaluate_tool(tool)
        assert risk == "R1", f"{tool} should be R1, got {risk}"
        assert decision == "ALLOW", f"{tool} should be ALLOW, got {decision}"


def test_destructive_tools_require_approval():
    mod = _load_policy_module()
    destructive_tools = [
        "delete_entities",
        "delete_observations",
        "delete_relations",
        "clear_session",
        "refresh_render_account_status",
    ]
    for tool in destructive_tools:
        decision, risk = mod.evaluate_tool(tool)
        assert risk == "R2", f"{tool} should be R2, got {risk}"
        assert decision == "REQUIRE_APPROVAL", f"{tool} should require approval, got {decision}"


def test_unknown_tool_falls_back_to_r3():
    mod = _load_policy_module()
    decision, risk = mod.evaluate_tool("totally_unknown_tool")
    assert risk == "R3"
    assert decision == "REQUIRE_APPROVAL"


def test_is_tool_allowed_helper():
    mod = _load_policy_module()
    assert mod.is_tool_allowed("read_graph") is True
    assert mod.is_tool_allowed("create_entities") is True
    assert mod.is_tool_allowed("delete_entities") is False
    assert mod.is_tool_allowed("unknown_tool") is False


# ── Policy Engine Direct Tests ────────────────────────────────────────


def test_risk_engine_render_rules():
    mod = _load_policy_module()
    engine = mod.RiskEngine()
    assert engine.evaluate("render", "deploy") == "R2"
    assert engine.evaluate("render", "restart") == "R2"
    assert engine.evaluate("render", "suspend") == "R4"
    assert engine.evaluate("render", "delete") == "R6"


def test_risk_engine_supabase_rules():
    mod = _load_policy_module()
    engine = mod.RiskEngine()
    assert engine.evaluate("supabase", "restart") == "R3"
    assert engine.evaluate("supabase", "drop_db") == "R6"
    assert engine.evaluate("supabase", "insert") == "R2"


def test_risk_engine_redis_rules():
    mod = _load_policy_module()
    engine = mod.RiskEngine()
    assert engine.evaluate("redis", "flushall") == "R5"
    assert engine.evaluate("redis", "set") == "R1"
    assert engine.evaluate("redis", "del") == "R2"


def test_risk_engine_github_rules():
    mod = _load_policy_module()
    engine = mod.RiskEngine()
    assert engine.evaluate("github", "push") == "R2"
    assert engine.evaluate("github", "delete_repo") == "R6"


def test_policy_engine_decision_boundaries():
    mod = _load_policy_module()
    engine = mod.PolicyEngine()
    # R0, R1 → ALLOW
    assert engine.decide("R0") == "ALLOW"
    assert engine.decide("R1") == "ALLOW"
    # R2-R5 → REQUIRE_APPROVAL
    assert engine.decide("R2") == "REQUIRE_APPROVAL"
    assert engine.decide("R3") == "REQUIRE_APPROVAL"
    assert engine.decide("R4") == "REQUIRE_APPROVAL"
    assert engine.decide("R5") == "REQUIRE_APPROVAL"
    # R6 → REQUIRE_APPROVAL (strict HITL)
    assert engine.decide("R6") == "REQUIRE_APPROVAL"


def test_singleton_engine():
    mod = _load_policy_module()
    engine1 = mod.get_policy_engine()
    engine2 = mod.get_policy_engine()
    assert engine1 is engine2
