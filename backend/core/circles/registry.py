from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from .contracts import (
    CapabilityRequest,
    CircleManifest,
    EventEnvelope,
    ExecutionResult,
    ExecutionStatus,
)
from .event_journal import circle_event_journal

CapabilityHandler = Callable[[CapabilityRequest], Awaitable[Any] | Any]
PolicyEvaluator = Callable[[CapabilityRequest], Awaitable[bool] | bool]


class CircleRegistry:
    """In-process circle registry for the zero-infrastructure hot path."""

    def __init__(self) -> None:
        self._manifests: dict[str, CircleManifest] = {}
        self._handlers: dict[str, CapabilityHandler] = {}
        self._events: list[EventEnvelope] = []
        self._policy_evaluator: PolicyEvaluator | None = None

    def set_policy_evaluator(self, evaluator: PolicyEvaluator | None) -> None:
        """Attach the central policy boundary used by every Circle dispatch."""
        self._policy_evaluator = evaluator

    def register(self, manifest: CircleManifest) -> None:
        key = manifest.name.value
        if key in self._manifests:
            raise ValueError(f"Circle already registered: {key}")
        self._manifests[key] = manifest
        for capability in manifest.capabilities:
            if capability.name in self._handlers:
                raise ValueError(f"Capability already registered: {capability.name}")

    def register_handler(self, capability: str, handler: CapabilityHandler) -> None:
        if capability in self._handlers:
            raise ValueError(f"Capability already registered: {capability}")
        self._handlers[capability] = handler

    def manifests(self) -> tuple[CircleManifest, ...]:
        return tuple(self._manifests.values())

    def capabilities(self) -> tuple[str, ...]:
        return tuple(sorted(self._handlers))

    def events(self) -> tuple[EventEnvelope, ...]:
        return tuple(self._events)

    async def dispatch(self, request: CapabilityRequest) -> ExecutionResult:
        handler = self._handlers.get(request.capability.name)
        if handler is None:
            return ExecutionResult(
                execution_id=request.context.execution_id,
                status=ExecutionStatus.UNAVAILABLE,
                error_code="capability_not_registered",
                error_message=request.capability.name,
                circle=request.capability.owner_circle,
                capability=request.capability.name,
            )

        if not request.context.tenant_id or not request.context.actor_id:
            return ExecutionResult(
                execution_id=request.context.execution_id,
                status=ExecutionStatus.REJECTED,
                error_code="execution_context_incomplete",
                error_message="actor_id and tenant_id are required",
                circle=request.capability.owner_circle,
                capability=request.capability.name,
            )

        if request.capability.approval_required:
            return ExecutionResult(
                execution_id=request.context.execution_id,
                status=ExecutionStatus.APPROVAL_REQUIRED,
                error_code="human_approval_required",
                error_message="This capability must be approved before execution",
                circle=request.capability.owner_circle,
                capability=request.capability.name,
            )

        if self._policy_evaluator is not None:
            allowed = self._policy_evaluator(request)
            if hasattr(allowed, "__await__"):
                allowed = await allowed
            if not allowed:
                return ExecutionResult(
                    execution_id=request.context.execution_id,
                    status=ExecutionStatus.REJECTED,
                    error_code="central_policy_denied",
                    error_message="Central policy denied this capability",
                    circle=request.capability.owner_circle,
                    capability=request.capability.name,
                )

        try:
            value = handler(request)
            if hasattr(value, "__await__"):
                value = await value
            result = ExecutionResult(
                execution_id=request.context.execution_id,
                status=ExecutionStatus.SUCCEEDED,
                data=value,
                circle=request.capability.owner_circle,
                capability=request.capability.name,
            )
        except Exception as exc:
            result = ExecutionResult(
                execution_id=request.context.execution_id,
                status=ExecutionStatus.FAILED,
                error_code="circle_handler_failed",
                error_message=str(exc),
                circle=request.capability.owner_circle,
                capability=request.capability.name,
            )

        event = EventEnvelope(
            event_type=f"execution.{result.status.value}",
            execution_id=request.context.execution_id,
            correlation_id=request.context.correlation_id,
            actor_id=request.context.actor_id,
            tenant_id=request.context.tenant_id,
            circle=request.capability.owner_circle,
            payload={"capability": request.capability.name},
        )
        self._events.append(event)
        circle_event_journal.append(event)
        return result


circle_registry = CircleRegistry()
