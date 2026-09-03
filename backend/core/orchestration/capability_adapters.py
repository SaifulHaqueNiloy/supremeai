"""Safe adapters for the chat-centered hub-and-spoke control plane.

Adapters intentionally expose bounded operations. They do not call HTTP routes or
bypass the policy gateway; each spoke can later replace its status handler with a
real task-backed implementation without changing the chat contract.
"""
from __future__ import annotations

from typing import Any

from core.orchestration.conversation_orchestrator import ConversationCommand


async def _status(command: ConversationCommand, spoke: str, message: str) -> dict[str, Any]:
    return {
        "spoke": spoke,
        "status": "connected",
        "message": message,
        "tenant_id": command.tenant_id,
        "project_id": command.project_id,
        "conversation_id": command.conversation_id,
        "capability_chain": command.metadata.get("capability_chain", []),
        "handoff_ready": True,
    }


async def task_handler(command: ConversationCommand) -> dict[str, Any]:
    """Submit a durable, tenant-scoped task through the canonical task engine."""
    from ecosystem.task_engine import TaskEngine, TaskOwner, TaskRecord

    record = TaskRecord(
        goal=command.prompt,
        owner=TaskOwner.ADMIN if command.role == "admin" else TaskOwner.USER,
        scope={"project_id": command.project_id, "conversation_id": command.conversation_id},
        correlation={"correlation_id": command.metadata.get("correlation_id")},
        created_by=command.user_id,
        tenant_id=command.tenant_id,
        risk_level="MEDIUM",
    )
    saved = TaskEngine().submit(record)
    return {
        "spoke": "task",
        "status": "queued",
        "task_id": saved.task_id,
        "state": saved.state,
        "tenant_id": command.tenant_id,
        "project_id": command.project_id,
    }


async def realtime_handler(command: ConversationCommand) -> dict[str, Any]:
    """Publish a governed orchestration event for connected realtime clients."""
    from core.messaging.event_bus import ErrorContext, ErrorEvent, error_event_bus

    error_event_bus.emit(ErrorEvent(
        module="conversation_orchestrator",
        error_type="ORCHESTRATION_EVENT",
        message=command.prompt[:200],
        severity="INFO",
        structured_context=ErrorContext(module="conversation_orchestrator", user_id=command.user_id),
        context={"tenant_id": command.tenant_id, "project_id": command.project_id},
    ))
    return await _status(command, "realtime", "Event published to the shared event bus.")


async def admin_handler(command: ConversationCommand) -> dict[str, Any]:
    return await _status(command, "admin", "Administrative control is connected and requires an admin principal.")


async def evolution_handler(command: ConversationCommand) -> dict[str, Any]:
    return await _status(command, "evolution", "Evolution services are connected behind an approval boundary.")



async def artifact_handler(command: ConversationCommand) -> dict[str, Any]:
    """Create a scoped artifact when chat provides content; otherwise expose handoff."""
    content = command.metadata.get("content")
    if not content:
        return await _status(command, "artifact", "Artifact handoff ready; provide content to create an artifact.")
    from uuid import uuid4
    from database.supabase_client import SupabaseDB

    row = {
        "id": str(uuid4()),
        "user_id": command.user_id,
        "title": str(command.metadata.get("title") or "Chat artifact")[:256],
        "artifact_type": str(command.metadata.get("artifact_type") or "code"),
        "content": str(content),
        "conversation_id": command.conversation_id,
    }
    response = await SupabaseDB().client.table("artifacts").insert(row).execute()
    if not response.data:
        raise RuntimeError("Artifact persistence returned no record")
    return {"spoke": "artifact", "status": "created", "artifact": response.data[0],
            "tenant_id": command.tenant_id, "project_id": command.project_id}


async def external_handler(command: ConversationCommand) -> dict[str, Any]:
    return await _status(command, "external", "External tools are connected through governed capability dispatch.")


__all__ = [
    "admin_handler", "artifact_handler", "evolution_handler", "external_handler",
    "realtime_handler", "task_handler",
]
