import pytest
from engine.self_assembling_orchestrator import SelfAssemblingOrchestrator
from memory.knowledge_distiller import KnowledgeDistiller
from tools.sandbox.micro_runtime_sandbox import MicroRuntimeSandbox
from api.routes.brain_visualizer_bridge import VisualizerConnectionManager


@pytest.mark.anyio
async def test_self_assembling_orchestrator_pipeline():
    orchestrator = SelfAssemblingOrchestrator()
    events = []

    def on_progress(evt):
        events.append(evt.phase)

    report = await orchestrator.self_assemble_project(
        user_prompt="Build a real-time notification badge counter",
        tenant_id="test-tenant",
        progress_callback=on_progress,
    )

    assert report["status"] == "completed"
    assert report["task_count"] > 0
    assert len(report["agents_involved"]) > 0
    assert "PLANNING" in events
    assert "SWARM_SPAWNING" in events
    assert "CODE_SYNTHESIS" in events


def test_knowledge_distiller():
    distiller = KnowledgeDistiller()

    # Distill a solution with specific variable names
    code_a = """
def calculate_metrics(values):
    \"\"\"Docstring to be stripped.\"\"\"
    total = sum(values)
    avg = total / len(values)
    return avg
"""
    item = distiller.distill_solution(
        task_intent="Calculate average metric",
        solution_code=code_a,
        reasoning_summary="Calculated mean of list using sum and len.",
        tenant_id="test-tenant",
    )

    assert item["distilled_id"].startswith("distilled_knowledge_")
    assert "ast_fingerprint" in item

    # 1. Text lookup match
    match_text = distiller.find_distilled_match("Calculate average metric", tenant_id="test-tenant")
    assert match_text is not None
    assert match_text["distilled_id"] == item["distilled_id"]

    # 2. Structural AST lookup with completely different variable names!
    code_b = """
def compute_scores(items):
    s = sum(items)
    result = s / len(items)
    return result
"""
    match_ast = distiller.find_structural_ast_match(code_b, tenant_id="test-tenant")
    assert match_ast is not None
    assert match_ast["distilled_id"] == item["distilled_id"]


def test_micro_runtime_sandbox_safety_and_exec():
    sandbox = MicroRuntimeSandbox()

    # 1. Safe execution
    safe_code = """
nums = [1, 2, 3, 4, 5]
result = sum(nums) * 2
print(f"Calculated: {result}")
"""
    res = sandbox.run_sandboxed_python(safe_code)
    assert res.status == "success"
    assert res.return_value == 30
    assert "Calculated: 30" in res.output
    assert res.execution_time_ms < 50.0  # sub-50ms execution

    # 2. Blocked malicious imports
    evil_code = """
import os
os.system("echo hacked")
"""
    res_evil = sandbox.run_sandboxed_python(evil_code)
    assert res_evil.status == "rejected"
    assert "Forbidden module import" in str(res_evil.error)

    # 3. Blocked builtins
    eval_code = """
fn = eval("1 + 1")
"""
    res_eval = sandbox.run_sandboxed_python(eval_code)
    assert res_eval.status == "rejected"
    assert "Forbidden builtin" in str(res_eval.error)


@pytest.mark.anyio
async def test_brain_visualizer_manager():
    manager = VisualizerConnectionManager()
    assert len(manager.active_connections) == 0
