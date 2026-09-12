"""backend/core/kernel/dispatcher.py — SupremeKernel Central Dispatcher.

Governed Single-Door Entry Facade:
- Authenticates actor and verifies tenant boundaries
- Resolves target circle (Governance, Execution, Evolution, Infrastructure)
- Applies policy and circuit breakers
- Emits distributed trace and audit journal events
"""

from __future__ import annotations

import time
from typing import Any

from core.circles.contracts import (
    CapabilityRef,
    CapabilityRequest,
    CircleName,
    ExecutionContext,
    ExecutionStatus,
    RiskLevel,
)
from core.circles.registry import circle_registry
from core.kernel.interface import CircleScope, KernelRequest, KernelResponse
from core.logging_config import logger

_CIRCLE_SCOPE_MAPPING: dict[CircleScope, CircleName] = {
    CircleScope.GOVERNANCE: CircleName.ADMIN,
    CircleScope.EXECUTION: CircleName.TASK,
    CircleScope.EVOLUTION: CircleName.EVOLUTION,
    CircleScope.INFRASTRUCTURE: CircleName.GATEWAY,
}


class SupremeKernel:
    """The central single-door facade for SupremeAI capabilities."""

    def __init__(self) -> None:
        self.registry = circle_registry

    async def dispatch(self, request: KernelRequest) -> KernelResponse:
        start_time = time.perf_counter()
        logger.info(
            f"[SupremeKernel] Inbound dispatch request: {request.capability} "
            f"circle={request.target_circle.value} tenant={request.tenant_id}"
        )

        # 1. Map CircleScope to underlying CircleName
        target_circle_name = _CIRCLE_SCOPE_MAPPING.get(request.target_circle, CircleName.GATEWAY)

        # 2. Build ExecutionContext and CapabilityRequest
        exec_ctx = ExecutionContext(
            execution_id=request.request_id,
            correlation_id=request.correlation_id,
            actor_id=request.actor_id,
            tenant_id=request.tenant_id,
            workspace_id=request.workspace_id,
            deadline_ms=request.deadline_ms,
            idempotency_key=request.idempotency_key,
            trace_id=request.trace_id,
        )

        cap_ref = CapabilityRef(
            name=request.capability,
            owner_circle=target_circle_name,
            risk_level=RiskLevel.LOW,
            timeout_ms=request.deadline_ms,
        )

        cap_request = CapabilityRequest(
            capability=cap_ref,
            context=exec_ctx,
            source="kernel_dispatch",
            payload=request.payload,
        )

        # 3. Route through CircleRegistry with policy, circuit breakers, and audit
        try:
            exec_result = await self.registry.dispatch(cap_request)
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0

            return KernelResponse(
                request_id=request.request_id,
                correlation_id=request.correlation_id,
                trace_id=request.trace_id,
                target_circle=request.target_circle,
                capability=request.capability,
                status=exec_result.status.value,
                data=exec_result.data,
                error_code=exec_result.error_code,
                error_message=exec_result.error_message,
                execution_time_ms=elapsed_ms,
                verified=exec_result.verification.verified if exec_result.verification else True,
            )
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            logger.error(f"[SupremeKernel] Dispatch execution failure: {exc}", exc_info=True)
            return KernelResponse(
                request_id=request.request_id,
                correlation_id=request.correlation_id,
                trace_id=request.trace_id,
                target_circle=request.target_circle,
                capability=request.capability,
                status="failed",
                error_code="kernel_dispatch_error",
                error_message=str(exc),
                execution_time_ms=elapsed_ms,
                verified=False,
            )


# Global Singleton Facade
supreme_kernel = SupremeKernel()
