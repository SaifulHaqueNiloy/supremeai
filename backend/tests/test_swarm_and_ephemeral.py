import pytest

from core.security.codegen_gate import ALLOW_INPROCESS_CODEGEN_ENV
from core.intelligence.swarm_consensus import SwarmConsensusEngine
from tools.ephemeral_synthesizer import (
    EphemeralToolSynthesizer,
    validate_ephemeral_code_ast,
)


@pytest.mark.asyncio
async def test_swarm_consensus_execution():
    engine = SwarmConsensusEngine()
    result = await engine.execute_consensus(
        prompt="Design a resilient retry mechanism for an async redis queue",
        context={"service": "queue"},
    )
    assert result.verified is True
    assert len(result.perspectives) == 3
    roles = [p.agent_role for p in result.perspectives]
    assert "architect" in roles
    assert "critic" in roles
    assert "synthesizer" in roles
    assert result.final_output is not None


@pytest.mark.asyncio
async def test_ephemeral_synthesizer_safe_execution(monkeypatch):
    # Issue #704: in-process exec is fail-closed by default; this coverage
    # test exercises the explicitly-enabled (local dev) path.
    monkeypatch.setenv(ALLOW_INPROCESS_CODEGEN_ENV, "true")
    synthesizer = EphemeralToolSynthesizer()
    safe_code = """
def run(x: int, y: int) -> int:
    return x * y + 10
"""
    res = await synthesizer.execute_ephemeral_script(
        tool_name="multiply_add",
        script_code=safe_code,
        input_args={"x": 5, "y": 6},
    )
    assert res.status == "succeeded"
    assert res.ast_safe is True
    assert res.result == 40


@pytest.mark.asyncio
async def test_ephemeral_synthesizer_blocks_dangerous_code(monkeypatch):
    # Reach the AST gate (not the #704 codegen gate) for this coverage test.
    monkeypatch.setenv(ALLOW_INPROCESS_CODEGEN_ENV, "true")
    synthesizer = EphemeralToolSynthesizer()
    dangerous_code = """
import os

def run():
    return os.listdir('.')
"""
    res = await synthesizer.execute_ephemeral_script(
        tool_name="malicious_tool",
        script_code=dangerous_code,
    )
    assert res.status == "rejected"
    assert res.ast_safe is False
    assert "Illegal import" in (res.error or "")
