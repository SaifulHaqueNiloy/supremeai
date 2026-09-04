"""
SupremeAI Automation Execution Recorder
========================================
বাংলা: Plan Section 7 — automation execution lifecycle persistence।
AutomationExecution DB model-এ dispatch lifecycle রেকর্ড করে:
  - dispatch শুরু হলে PENDING record তৈরি
  - সম্পন্ন হলে status update (DELIVERED/FAILED/SKIPPED)
  - duration, http_status, external_execution_id, error সংরক্ষণ

নীতি (Plan Section 10 — core-operation isolation):
  DB write কখনো dispatch-কে block করে না। DB unavailable হলে
  recorder শুধু warning log করে এবং dispatch স্বাভাবিকভাবে চলে।
  এটা "best-effort persistence" — audit trail থাকলে ভালো, না থাকলেও
  core functionality unaffected।
"""

from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, Optional
from uuid import uuid4

from core.logging_config import logger

from .models import AutomationEvent, AutomationResult, AutomationStatus

if TYPE_CHECKING:
    from core.orchestration.conversation_orchestrator import ExecutionRecord


class ExecutionRecorder:
    """
    Plan Section 7: AutomationExecution lifecycle DB persistence।

    বাংলা: প্রতিটি dispatch-এর জন্য একটি AutomationExecution row তৈরি/আপডেট
    করে। DB unavailable হলে graceful degradation — dispatch কখনো block হয় না।
    """

    async def record_start(self, event: AutomationEvent) -> str | None:
        """
        dispatch শুরু হলে PENDING record তৈরি করে।
        রিটার্ন: execution_id (DB row id) অথবা None (DB unavailable)।
        """
        execution_id = str(uuid4())
        try:
            from database.session import get_db_session_context
            from models.automation_execution import AutomationExecution

            async with get_db_session_context() as session:
                record = AutomationExecution(
                    id=execution_id,
                    event_id=event.event_id,
                    workflow_key=event.workflow_key,
                    idempotency_key=event.idempotency_key,
                    provider="pending",  # provider পরে record_completion-এ update হবে
                    status="PENDING",
                    attempt=1,
                    trace_id=event.trace_id,
                    started_at=datetime.now(UTC),
                )
                session.add(record)
                await session.commit()
                logger.debug(
                    f"📋 ExecutionRecorder: PENDING record created for event {event.event_id} "
                    f"(execution_id={execution_id[:8]})"
                )
                return execution_id
        except Exception as e:
            # Plan Section 10: DB failure কখনো dispatch-কে block করে না
            logger.warning(
                f"⚠️ ExecutionRecorder.record_start failed (DB unavailable?): {e!r} — "
                f"dispatch will continue without DB persistence"
            )
            return None

    async def record_completion(
        self,
        execution_id: str | None,
        event: AutomationEvent,
        result: AutomationResult,
        provider_name: str,
        started_at: float | None = None,
    ) -> None:
        """
        dispatch সম্পন্ন হলে record update করে।
        execution_id None হলে (record_start fail করেছিল) কিছু করে না।
        """
        if execution_id is None:
            return  # record_start fail করেছিল — কিছু করার নেই

        try:
            from sqlalchemy import select

            from database.session import get_db_session_context
            from models.automation_execution import AutomationExecution, AutomationExecutionAttempt

            duration_ms = None
            if started_at is not None:
                duration_ms = int((time.time() - started_at) * 1000)

            async with get_db_session_context() as session:
                # fetch existing record
                stmt = select(AutomationExecution).where(AutomationExecution.id == execution_id)
                db_result = await session.execute(stmt)
                record = db_result.scalar_one_or_none()
                if record is None:
                    logger.warning(
                        f"⚠️ ExecutionRecorder: record {execution_id[:8]} not found — "
                        f"cannot update completion"
                    )
                    return

                # update fields
                record.status = result.status.value.upper()
                record.provider = provider_name
                record.attempt = result.attempt
                record.completed_at = datetime.now(UTC)
                record.duration_ms = duration_ms
                record.external_execution_id = result.execution_id

                # error fields (শুধু FAILED হলে)
                if result.status == AutomationStatus.FAILED:
                    record.error_message = result.message[:1024] if result.message else None
                else:
                    record.error_message = None

                # Create the attempt record (Plan Section 8: retry attempt history)
                attempt_record = AutomationExecutionAttempt(
                    execution_id=execution_id,
                    attempt=result.attempt,
                    status=result.status.value.upper(),
                    started_at=datetime.fromtimestamp(started_at, tz=UTC)
                    if started_at
                    else record.started_at,
                    completed_at=record.completed_at,
                    duration_ms=duration_ms,
                    http_status=None,  # This could be parsed from result if needed
                    error_message=record.error_message,
                )
                session.add(attempt_record)

                await session.commit()
                logger.debug(
                    f"📋 ExecutionRecorder: record updated for event {event.event_id} "
                    f"(status={result.status.value}, duration={duration_ms}ms)"
                )
        except Exception as e:
            # Plan Section 10: DB failure কখনো dispatch-কে block করে না
            logger.warning(
                f"⚠️ ExecutionRecorder.record_completion failed: {e!r} — dispatch result unaffected"
            )

    async def persist_execution(
        self,
        record: ExecutionRecord,
        policy: dict[str, Any] | None = None,
    ) -> str | None:
        """
        Durable bridge for the canonical orchestration `ExecutionRecord`.

        বাংলা: orchestration dispatch-এর ExecutionRecord কে automation_executions
        টেবিলে লেখে — correlation/tenant/project/conversation লিংক + evidence +
        policy decision সহ। Best-effort: DB unavailable হলে dispatch কখনো block হয়
        না (শুধু warning log) — core-operation isolation নীতি (Plan Section 10)।
        """
        if record is None:
            return None
        execution_id = str(uuid4())
        try:
            from database.session import get_db_session_context
            from models.automation_execution import AutomationExecution

            now = datetime.now(UTC)
            async with get_db_session_context() as session:
                db_record = AutomationExecution(
                    id=execution_id,
                    event_id=record.execution_id,
                    workflow_key=f"orchestrator:{record.capability}",
                    idempotency_key=record.correlation_id,
                    provider="orchestrator",
                    status=record.status.upper(),
                    attempt=1,
                    trace_id=record.correlation_id,
                    started_at=now,
                    completed_at=now,
                    correlation_id=record.correlation_id,
                    tenant_id=record.tenant_id,
                    project_id=record.project_id,
                    conversation_id=record.conversation_id,
                    capability=record.capability,
                    evidence=record.evidence or None,
                    policy=policy,
                )
                session.add(db_record)
                await session.commit()
                logger.debug(
                    f"📋 ExecutionRecorder: orchestration ExecutionRecord persisted "
                    f"(execution_id={execution_id[:8]}, capability={record.capability}, "
                    f"status={record.status})"
                )
                return execution_id
        except Exception as e:
            # Plan Section 10: DB failure কখনো orchestration dispatch-কে block করে না
            logger.warning(
                f"⚠️ ExecutionRecorder.persist_execution failed (DB unavailable?): {e!r} — "
                f"orchestration continues without durable persistence"
            )
            return None


# Singleton instance
execution_recorder = ExecutionRecorder()
