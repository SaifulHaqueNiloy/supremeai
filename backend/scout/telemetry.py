"""Telemetry and event publishing for policy-driven web crawler."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from core.logging_config import logger
from core.messaging.event_bus import ErrorEvent, error_event_bus
from scout.models import CrawlEventType


class CrawlerTelemetry:
    """Dispatches lifecycle events and metrics for crawl tasks."""

    def __init__(self, tenant_id: str, task_id: str) -> None:
        self.tenant_id = tenant_id
        self.task_id = task_id

    def emit_event(
        self,
        event_type: CrawlEventType,
        message: str,
        severity: str = "INFO",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Publishes a structured crawl lifecycle event to the central event bus."""
        event_metadata = {
            "tenant_id": self.tenant_id,
            "task_id": self.task_id,
            "crawl_event": event_type.value,
            **(metadata or {}),
        }

        # Log locally for fast observability
        logger.info(f"[Crawler:{self.tenant_id}:{self.task_id}] {event_type.value}: {message}")

        # If warning or error, forward to error event pipeline
        if severity in ["WARNING", "ERROR", "CRITICAL"]:
            error_event = ErrorEvent(
                module="scout.crawler",
                error_type=f"CRAWLER_{event_type.value.upper()}",
                message=message,
                severity=severity,
                context=event_metadata,
            )
            try:
                error_event_bus.emit(error_event)
            except Exception as exc:
                logger.warning(f"Failed to emit crawler telemetry event: {exc}")
