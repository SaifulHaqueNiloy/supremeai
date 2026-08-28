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
from typing import Any, Optional
from uuid import uuid4

from loguru import logger

from .models import AutomationEvent, AutomationResult, AutomationStatus


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
            from models.automation_execution import AutomationExecution

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


# Singleton instance
execution_recorder = ExecutionRecorder()
