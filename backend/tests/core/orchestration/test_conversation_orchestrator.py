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


@pytest.mark.asyncio
async def test_destructive_capability_requires_confirmation():
    async def handler(_):
        return "done"

    runtime = ConversationOrchestrator()
    runtime.register(Capability("chat", "low", handler, destructive=True))
    result = await runtime.dispatch(ConversationCommand("hello", "u1", "t1"))
    assert result.status == "confirmation_required"
    assert result.requires_confirmation is True


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
