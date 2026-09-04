import asyncio

import pytest

from core.orchestration.conversation_orchestrator import (
    Capability,
    ConversationCommand,
    ConversationOrchestrator,
)


@pytest.mark.asyncio
async def test_unknown_capability_fails_closed():
    runtime = ConversationOrchestrator()
    result = await runtime.dispatch(ConversationCommand("hello", "u1", "t1"))
    assert result.status == "failed"
    assert result.error == "Capability unavailable"
    assert result.execution is not None
    assert result.execution.status == "unavailable"
    assert result.execution.tenant_id == "t1"
    assert result.execution.evidence[0]["type"] == "orchestration.unavailable"


@pytest.mark.asyncio
async def test_destructive_capability_requires_confirmation():
    async def handler(_):
        return "done"

    runtime = ConversationOrchestrator()
    runtime.register(Capability("chat", "low", handler, destructive=True))
    result = await runtime.dispatch(ConversationCommand("hello", "u1", "t1"))
    assert result.status == "confirmation_required"
    assert result.requires_confirmation is True
    assert result.execution is not None
    assert result.execution.status == "confirmation_required"
    assert result.execution.evidence[0]["type"] == "orchestration.approval_required"


@pytest.mark.asyncio
async def test_timeout_is_explicit_and_evidenced():
    async def handler(_):
        await asyncio.sleep(0.05)
        return "late"

    runtime = ConversationOrchestrator()
    runtime.register(Capability("chat", "low", handler))
    result = await runtime.dispatch(
        ConversationCommand("hello", "u1", "tenant-1", metadata={"timeout_seconds": 0.01})
    )
    assert result.status == "failed"
    assert result.execution is not None
    assert result.execution.status == "timed_out"
    assert result.execution.evidence[0]["type"] == "orchestration.timed_out"


@pytest.mark.asyncio
async def test_capability_dispatch_is_scoped_to_principal():
    seen = {}

    async def handler(command):
        seen["tenant"] = command.tenant_id
        return "ok"

    runtime = ConversationOrchestrator()
    runtime.register(Capability("chat", "low", handler))
    result = await runtime.dispatch(ConversationCommand("hello", "u1", "tenant-1"))
    assert result.status == "completed"
    assert seen["tenant"] == "tenant-1"
