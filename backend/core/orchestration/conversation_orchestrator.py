"""Governed chat-centered hub-and-spoke orchestration runtime."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable

from core.security.tool_gateway import ToolPolicyGateway, tool_policy_gateway


@dataclass(frozen=True)
class ConversationCommand:
    prompt: str
    user_id: str
    tenant_id: str
    role: str = "user"
    project_id: str | None = None
    conversation_id: str | None = None
    confirmation: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class OrchestrationResult:
    correlation_id: str
    status: str
    capability: str
    response: Any = None
    requires_confirmation: bool = False
    task_id: str | None = None
    error: str | None = None
    events: list[dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class Capability:
    name: str
    risk: str
    handler: Callable[[ConversationCommand], Awaitable[Any]]
    admin_only: bool = False
    destructive: bool = False


class ConversationOrchestrator:
    """Single governed dispatch point; unknown capabilities fail closed."""

    def __init__(self, policy: ToolPolicyGateway | None = None) -> None:
        self.policy = policy or tool_policy_gateway
        self._capabilities: dict[str, Capability] = {}

    def register(self, capability: Capability) -> None:
        self._capabilities[capability.name] = capability
        self.policy.register_tool(capability.name, capability.risk)

    def capabilities(self) -> list[dict[str, str]]:
        return [{"name": c.name, "risk": c.risk} for c in self._capabilities.values()]

    @staticmethod
    def classify(prompt: str) -> str:
        text = prompt.lower()
        if any(word in text for word in ("browser", "website", "navigate", "url")):
            return "browser"
        if any(word in text for word in ("memory", "remember", "knowledge")):
            return "memory"
        return "chat"

    async def dispatch(self, command: ConversationCommand) -> OrchestrationResult:
        correlation_id = f"corr_{uuid.uuid4().hex}"
        capability_name = self.classify(command.prompt)
        capability = self._capabilities.get(capability_name)
        event = {"type": "orchestration.started", "correlation_id": correlation_id,
                 "conversation_id": command.conversation_id, "tenant_id": command.tenant_id,
                 "user_id": command.user_id, "capability": capability_name}
        if not capability:
            return OrchestrationResult(correlation_id, "failed", capability_name,
                                       error="Capability unavailable", events=[event])
        if (capability.admin_only or capability.destructive) and command.role != "admin":
            return OrchestrationResult(correlation_id, "denied", capability_name,
                                       error="Admin permission required", events=[event])
        if capability.destructive and not command.confirmation:
            return OrchestrationResult(correlation_id, "confirmation_required", capability_name,
                                       requires_confirmation=True, events=[event])
        decision = await self.policy.evaluate(capability.name,
            {"sub": command.user_id, "tenant_id": command.tenant_id, "role": command.role},
            risk=capability.risk, action="conversation.dispatch")
        if not decision.allowed:
            return OrchestrationResult(correlation_id, "denied", capability_name,
                                       error=decision.reason, events=[event])
        try:
            response = await capability.handler(command)
            event.update(type="orchestration.completed", status="completed")
            return OrchestrationResult(correlation_id, "completed", capability_name,
                                       response=response, events=[event])
        except Exception:
            event.update(type="orchestration.failed", status="failed")
            return OrchestrationResult(correlation_id, "failed", capability_name,
                                       error="Capability execution failed", events=[event])


async def _chat_handler(command: ConversationCommand) -> Any:
    from core.llm.llm_gateway import llm_gateway
    result = await llm_gateway.acompletion(prompt=command.prompt, task_type="chat", stream=False)
    return result.get("text", "") if isinstance(result, dict) else str(result)


async def _memory_handler(command: ConversationCommand) -> Any:
    from services.memory_service import recall_memories
    return await recall_memories(task_description=command.prompt, limit=3,
                                 threshold=0.55, user_id=command.user_id)


_orchestrator: ConversationOrchestrator | None = None


async def _browser_handler(command: ConversationCommand) -> Any:
    """Browser spoke: create or reuse an owner-scoped session and navigate."""
    from core.browser_session_manager import session_manager

    session_id = command.metadata.get("session_id")
    url = command.metadata.get("url")
    if not url:
        return {"status": "ready", "message": "Browser capability connected; provide a URL to navigate."}
    from core.security import is_safe_url
    if not is_safe_url(str(url)):
        raise ValueError("Unsafe URL")
    session = await session_manager.get(session_id, command.user_id) if session_id else await session_manager.create(command.user_id)
    await session.page.goto(str(url), wait_until="domcontentloaded")
    return {"session_id": session.id, "status": "navigated", "url": session.page.url}


def get_conversation_orchestrator() -> ConversationOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = ConversationOrchestrator()
        _orchestrator.register(Capability("chat", "low", _chat_handler))
        _orchestrator.register(Capability("memory", "low", _memory_handler))
        _orchestrator.register(Capability("browser", "medium", _browser_handler))
    return _orchestrator


__all__ = ["Capability", "ConversationCommand", "ConversationOrchestrator", "OrchestrationResult", "get_conversation_orchestrator"]
