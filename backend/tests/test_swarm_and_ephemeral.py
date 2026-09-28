import pytest

from core.intelligence.swarm_consensus import SwarmConsensusEngine


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
