"""Intelligence ReAct wiring tests (Issue #2705 Gap-F).

বাংলা সারসংক্ষেপ:
------------------
cognitive_router-এর ReAct routing mode, cognitive_pipeline_dispatcher-এর
stub-মুক্ত বাস্তব wiring (decide_and_execute production invoke), এবং
living_engine-এর SelfReflectionLoop production hook — তিনটিরই regression lock।
"""

import json
from unittest.mock import AsyncMock

import pytest

from brain.cognitive_router import CognitiveRouter
from core.orchestration.cognitive_pipeline_dispatcher import (
    CognitiveIntent,
    MasterCognitiveOrchestrator,
)

# বাংলা মন্তব্য: complex-prompt — reasoning/strategy কীওয়ার্ড আছে কিন্তু
# "analyze"+"implement" জুটি নেই (ওটা decomposed কনট্রাক্ট), budget-context নেই।
REACT_PROMPT = (
    "Plan a multi-step strategy to optimize our deployment pipeline and prove the tradeoff"
)


# ── 1. CognitiveRouter — ReAct mode ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_router_returns_react_mode_for_complex_prompt():
    """বাংলা মন্তব্য: complex task-এ routing_mode 'react' + executor তথ্য ফেরত দেয়।"""
    result = await CognitiveRouter().route(REACT_PROMPT, user_id="react-test-user")

    assert result["routing_mode"] == "react"
    assert "provider" in result and "model" in result
    react = result["react"]
    assert react["enabled"] is True
    assert react["complexity"] == "complex"
    assert react["max_iterations"] == 3
    assert "decide_and_execute" in react["executor"]


@pytest.mark.asyncio
async def test_router_react_never_fires_with_budget_context():
    """বাংলা মন্তব্য: budget-context থাকলে economic-optimizer direct পথই চলে (চুক্তি)।"""

    class Decision:
        provider = "budget-provider"
        model = "budget-model"

    class Optimizer:
        async def optimize_route(self, prompt, task_type, budget_context):
            return Decision()

    result = await CognitiveRouter(Optimizer()).route(
        REACT_PROMPT, user_id="react-test-user", budget_context={"monthly_limit": 10}
    )
    assert result == {"routing_mode": "direct", "provider": "budget-provider", "model": "budget-model"}


@pytest.mark.asyncio
async def test_router_contracts_preserved(monkeypatch):
    """বাংলা মন্তব্য: বিদ্যমান direct/decomposed কনট্রাক্ট exact-shape অক্ষত থাকবে।"""
    from backend.brain import cognitive_router as cr_module

    # বাংলা মন্তব্য: direct — সাধারণ প্রম্পট, কোনো অতিরিক্ত কী নয় (exact equality)
    monkeypatch.setattr(cr_module.settings, "model_general", "test-provider/test-model")
    direct = await CognitiveRouter().route("Summarize this request", user_id="contract-user")
    assert direct == {"routing_mode": "direct", "provider": "test-provider", "model": "test-model"}

    # বাংলা মন্তব্য: decomposed — analyze+implement জুটি আগের মতোই ২-নোড গ্রাফ
    decomposed = await CognitiveRouter().route(
        "Analyze the requirements and implement the change", user_id="contract-user"
    )
    assert decomposed["routing_mode"] == "decomposed"
    assert decomposed["task_graph"]["task_count"] == 2


# ── 2. Dispatcher — stub-মুক্ত বাস্তব wiring ──────────────────────────────────


@pytest.fixture
def orchestrator():
    return MasterCognitiveOrchestrator()


@pytest.fixture
def patched_react(monkeypatch):
    """বাংলা মন্তব্য: ReasoningOrchestrator.decide_and_execute-কে নিয়ন্ত্রিত mock-এ
    প্রতিস্থাপন — production invoke-পথটি প্রমাণ করত (ক্লাস-লেভেল patch)।"""
    from brain.reasoning_orchestrator import ReasoningOrchestrator

    mock = AsyncMock(
        return_value={
            "task": "diagnose",
            "decision": {
                "tool": "check_system_health",
                "args": {"target": "x"},
                "thought": "assess health",
                "source": "deterministic_fallback",
            },
            "outcome": {
                "tool": "check_system_health",
                "executed": True,
                "status": "ok",
                "observation": "cpu=12% ram=40%",
            },
        }
    )
    monkeypatch.setattr(ReasoningOrchestrator, "decide_and_execute", mock)
    return mock


@pytest.mark.asyncio
async def test_self_healing_invokes_decide_and_execute_and_reports_honestly(orchestrator, patched_react):
    """বাংলা মন্তব্য: self-healing পাইপলাইন বাস্তব ReAct নির্বাহ করে ও সৎ প্রতিবেদন দেয়।"""
    result = await orchestrator.dispatch(
        CognitiveIntent.REPAIR,
        {"error": "TimeoutError in step execution", "target_file": "adapters/task_executor.py"},
    )

    # বাংলা মন্তব্য: production path থেকে decide_and_execute() সত্যিই invoke হয়েছে
    patched_react.assert_awaited_once()

    assert result.status == "SUCCESS"
    assert "01_diagnostic_incident_replay" in result.stages_completed
    assert "04_solution_synthesis_sandbox" in result.stages_completed
    assert "05_governance_policy_authorization" in result.stages_completed
    assert result.confidence >= 0.90

    candidates = result.artifacts["candidate_solutions"]
    assert candidates and candidates[0]["source"] == "react_orchestrator"
    assert candidates[0]["execution_status"] == "ok"
    assert result.artifacts["patch_candidate"]["verification"] == "governed_tool_executed"
    # বাংলা মন্তব্য: মিথ্যা sandbox-দাবি আর নেই
    assert "verified_in_sandbox" not in json.dumps(result.artifacts)


@pytest.mark.asyncio
async def test_self_healing_honest_when_react_unavailable(orchestrator, monkeypatch):
    """বাংলা মন্তব্য: orchestrator অনুপস্থিত হলে সৎ unavailable-মার্কার — কোনো ভান নয়।"""
    from brain.reasoning_orchestrator import ReasoningOrchestrator

    monkeypatch.setattr(
        ReasoningOrchestrator,
        "decide_and_execute",
        AsyncMock(side_effect=RuntimeError("orchestrator down")),
    )
    result = await orchestrator.dispatch(
        CognitiveIntent.REPAIR,
        {"error": "boom", "target_file": "adapters/task_executor.py"},
    )
    assert result.status == "SUCCESS"
    assert result.artifacts["candidate_solutions"] == []
    assert "unreachable" in result.artifacts["react_unavailable"]
    assert result.artifacts["patch_candidate"]["verification"] == "pending_governed_execution"


@pytest.mark.asyncio
async def test_self_healing_governance_block_preserved(orchestrator, patched_react):
    """বাংলা মন্তব্য: governance ব্লক আগের মতোই fail-closed।"""
    result = await orchestrator.dispatch(
        CognitiveIntent.REPAIR,
        {"error": "Auth token bypass attempt", "target_file": "core/security/auth_guard.py"},
    )
    assert result.status == "BLOCKED"
    assert "Governance policy blocked repair" in result.summary
    assert result.confidence == 0.0


@pytest.mark.asyncio
async def test_deep_synthesis_has_no_fabricated_data(orchestrator):
    """বাংলা মন্তব্য: ভুয়া mem_vector_9f83a / ভুয়া 48-services / ভুয়া principles — কিছুই নেই।"""
    result = await orchestrator.dispatch(
        CognitiveIntent.FEATURE_SYNTHESIS,
        {"demand": "Design high-performance distributed token bucket rate limiter"},
    )

    assert result.status == "SUCCESS"
    assert "01_project_dna_fingerprint" in result.stages_completed
    assert "05_eternal_memory_ingestion" in result.stages_completed
    assert result.confidence >= 0.90

    raw = json.dumps(result.artifacts)
    assert "mem_vector_9f83a" not in raw
    assert "Principle 1" not in raw

    dna = result.artifacts["project_dna"]
    assert dna["source"] == "live_repo_scan"
    assert isinstance(dna["ecosystems"], list) and dna["ecosystems"]
    assert dna["api_route_modules"] >= 0

    consensus = result.artifacts["multi_model_consensus"]
    assert consensus["consensus_reached"] is False  # বাংলা: সৎ — multi-model নেই

    # বাংলা মন্তব্য: memory_id বাস্তব episodic id (ep_*) অথবা সৎ None — ভুয়া নয়
    memory_id = result.artifacts["memory_id"]
    assert memory_id is None or str(memory_id).startswith("ep_")


@pytest.mark.asyncio
async def test_audit_pipeline_reports_honest_metrics(orchestrator):
    """বাংলা মন্তব্য: ভুয়া 'critical: 0 / HEALTHY' ও ভুয়া revalued=12 বাদ — সৎ গণনা।"""
    result = await orchestrator.dispatch(CognitiveIntent.AUDIT_RADAR, {})

    assert result.status == "SUCCESS"
    assert "01_universal_gap_finder_scan" in result.stages_completed
    assert "03_memory_revaluation" in result.stages_completed

    gap = result.artifacts["gap_metrics"]
    assert gap["status"] == "MEASURED_LOCAL"
    assert gap["critical"] is None
    assert isinstance(gap["todo_fixme_markers"], int) and gap["todo_fixme_markers"] >= 0
    assert result.artifacts["memory_revalued_count"] == 0
    assert "not wired" in result.artifacts["documentation_drift"]["reason"]


@pytest.mark.asyncio
async def test_evolution_pipeline_success_and_rejection_preserved(orchestrator):
    """বাংলা মন্তব্য: evolution-এর governance চুক্তি অক্ষত; কিন্তু promoted মিথ্যা নয়।"""
    ok_res = await orchestrator.dispatch(
        CognitiveIntent.EVOLUTION, {"target_module": "skills/custom_math.py"}
    )
    assert ok_res.status == "SUCCESS"
    assert ok_res.artifacts["promoted"] is False  # বাংলা: সৎ — canary চলেনি

    blocked_res = await orchestrator.dispatch(
        CognitiveIntent.EVOLUTION, {"target_module": "billing/stripe_sync.py"}
    )
    assert blocked_res.status == "REJECTED"
    assert "blocked by governance policy" in blocked_res.summary


# ── 3. LivingEngine — SelfReflectionLoop production hook ─────────────────────


def _bare_living_engine():
    """বাংলা মন্তব্য: __init__-এর ভারী সার্ভিস-গ্রাফ এড়িয়ে ন্যূনতম ইনস্ট্যান্স।"""
    from services.living_engine import LivingEngineOrchestrator

    orch = LivingEngineOrchestrator.__new__(LivingEngineOrchestrator)
    orch._pending_reflections = set()
    return orch


@pytest.mark.asyncio
async def test_reflection_hook_invokes_self_reflection_loop(monkeypatch):
    """বাংলা মন্তব্য: hook-টিই SelfReflectionLoop.reflect()-এর production কলার।"""
    from engine.self_reflection import SelfReflectionLoop

    mock_reflect = AsyncMock(return_value={"is_correct": True})
    monkeypatch.setattr(SelfReflectionLoop, "reflect", mock_reflect)

    orch = _bare_living_engine()
    await orch._reflect_on_solution(
        prompt="Build me a rate limiter",
        execution_output='{"success": true}',
        is_success=True,
        duration_ms=12.5,
    )

    mock_reflect.assert_awaited_once()
    kwargs = mock_reflect.await_args.kwargs
    assert kwargs["task_prompt"].startswith("Build me a rate limiter")
    assert kwargs["is_success"] is True


@pytest.mark.asyncio
async def test_reflection_hook_never_breaks_main_path(monkeypatch):
    """বাংলা মন্তব্য: reflection ব্যর্থ হলেও hook কখনো exception ছুঁড়বে না (graceful)।"""
    from engine.self_reflection import SelfReflectionLoop

    monkeypatch.setattr(
        SelfReflectionLoop, "reflect", AsyncMock(side_effect=RuntimeError("llm down"))
    )
    orch = _bare_living_engine()
    # বাংলা মন্তব্য: raise হলে টেস্ট ব্যর্থ হবে — না হলে graceful প্রমাণিত
    await orch._reflect_on_solution(
        prompt="x", execution_output="y", is_success=False, error_details="z"
    )


@pytest.mark.asyncio
async def test_schedule_reflection_creates_tracked_task(monkeypatch):
    """বাংলা মন্তব্য: fire-and-forget টাস্ক রেফারেন্স-সেটে ট্র্যাক হয় (GC-সুরক্ষা)।"""
    from engine.self_reflection import SelfReflectionLoop

    mock_reflect = AsyncMock(return_value={})
    monkeypatch.setattr(SelfReflectionLoop, "reflect", mock_reflect)

    orch = _bare_living_engine()
    orch._schedule_reflection(prompt="p", execution_output="o", is_success=True)
    assert len(orch._pending_reflections) == 1
    # বাংলা মন্তব্য: টাস্ক শেষ হলে সেট থেকে স্বয়ংক্রিয় বাদ পড়া যাচাই
    (task,) = list(orch._pending_reflections)
    await task
    assert len(orch._pending_reflections) == 0
