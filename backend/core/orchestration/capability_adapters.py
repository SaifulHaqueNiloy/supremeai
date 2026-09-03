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
    }


async def task_handler(command: ConversationCommand) -> dict[str, Any]:
    return await _status(command, "task", "Task orchestration is connected; long-running work is policy-gated.")


async def admin_handler(command: ConversationCommand) -> dict[str, Any]:
    return await _status(command, "admin", "Administrative control is connected and requires an admin principal.")


async def evolution_handler(command: ConversationCommand) -> dict[str, Any]:
    return await _status(command, "evolution", "Evolution services are connected behind an approval boundary.")


async def realtime_handler(command: ConversationCommand) -> dict[str, Any]:
    return await _status(command, "realtime", "Realtime event fan-out is connected to the orchestration envelope.")


async def artifact_handler(command: ConversationCommand) -> dict[str, Any]:
    return await _status(command, "artifact", "Artifact and file operations are connected and remain scope-bound.")


async def external_handler(command: ConversationCommand) -> dict[str, Any]:
    return await _status(command, "external", "External tools are connected through governed capability dispatch.")


__all__ = [
    "admin_handler", "artifact_handler", "evolution_handler", "external_handler",
    "realtime_handler", "task_handler",
]
