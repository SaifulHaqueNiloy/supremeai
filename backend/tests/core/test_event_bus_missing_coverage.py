# বাংলা মন্তব্য: core module-এর কম-কভার লাইন কভার করার জন্য অতিরিক্ত টেস্টসমূহ
import asyncio
import contextlib
import json
import os
import sys
import time
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.messaging.event_bus import ErrorContext

# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _isolate_test_env(monkeypatch):
    monkeypatch.setenv("ENV", "test")
    monkeypatch.setenv("SUPREMEAI_JWT_SECRET", "test-secret-placeholder")
    monkeypatch.setenv("SUPREMEAI_ADMIN_PASSWORD_HASH", "")
    monkeypatch.delenv("ENCRYPTION_KEY", raising=False)
    yield
    return


# ========================== event_bus.py ==========================


class TestEventBusMissingBranches:
    def test_register_listener(self):
        from core.messaging.event_bus import ErrorEventBus

        bus = ErrorEventBus()
        listener = MagicMock()
        bus.register_listener(listener)
        assert listener in bus._listeners["*"]

    def test_emit_no_running_loop_runs_directly(self):
        from core.messaging.event_bus import ErrorEvent, ErrorEventBus

        bus = ErrorEventBus()
        listener = AsyncMock()
        bus.register_listener(listener)

        event = ErrorEvent(
            module="test",
            error_type="Err",
            message="msg",
            severity="WARNING",
            structured_context=ErrorContext(module="auto_fixed"),
            context={},
        )

        with patch("asyncio.get_running_loop", side_effect=RuntimeError("no loop")):
            with patch("core.messaging.event_bus.logger.debug") as mock_debug:
                bus.emit(event)
                mock_debug.assert_called()

    @pytest.mark.asyncio
    async def test_emit_async_fires_listeners(self):
        from core.messaging.event_bus import ErrorEvent, ErrorEventBus

        bus = ErrorEventBus()
        listener = AsyncMock()
        bus.register_listener("Err", listener)

        event = ErrorEvent(
            module="test",
            error_type="Err",
            message="msg",
            severity="WARNING",
            structured_context=ErrorContext(module="auto_fixed"),
            context={},
        )

        await bus.emit_async(event)
        await asyncio.sleep(0.05)
        listener.assert_called_once_with(event)

    @pytest.mark.asyncio
    async def test_emit_async_sync_listener(self):
        from core.messaging.event_bus import ErrorEvent, ErrorEventBus

        bus = ErrorEventBus()
        listener = MagicMock()
        bus.register_listener("Err", listener)

        event = ErrorEvent(
            module="test",
            error_type="Err",
            message="msg",
            severity="WARNING",
            structured_context=ErrorContext(module="auto_fixed"),
            context={},
        )
        await bus.emit_async(event)
        await asyncio.sleep(0.05)
        listener.assert_called_once_with(event)

    @pytest.mark.asyncio
    async def test_handler_failure_routes_to_dlq(self):
        from core.messaging.event_bus import (
            DeadLetterQueueItem,
            ErrorEvent,
            ErrorEventBus,
        )

        bus = ErrorEventBus()
        dlq_handler = AsyncMock()
        bus.register_dead_letter_handler(dlq_handler)

        listener = MagicMock(side_effect=RuntimeError("boom"))
        bus.register_listener("Err", listener)

        event = ErrorEvent(
            module="test",
            error_type="Err",
            message="msg",
            severity="ERROR",
            structured_context=ErrorContext(module="auto_fixed"),
            context={},
        )
        await bus.emit_async(event)
        await asyncio.sleep(0.05)
        assert bus.dead_letter_queue_size == 1
        dlq_handler.assert_called_once()
        item = dlq_handler.call_args[0][0]
        assert isinstance(item, DeadLetterQueueItem)

    @pytest.mark.asyncio
    async def test_dlq_full_drops_and_logs_critical(self):
        from core.messaging.event_bus import (
            DeadLetterQueueItem,
            ErrorEvent,
            ErrorEventBus,
        )

        bus = ErrorEventBus()
        # Pre-fill DLQ to maxsize
        for _ in range(1000):
            bus._dlq.put_nowait(
                DeadLetterQueueItem(
                    event_type="x",
                    handler_name="h",
                    error="e",
                    timestamp=datetime.now(UTC),
                )
            )

        listener = MagicMock(side_effect=RuntimeError("boom"))
        bus.register_listener("Err", listener)

        event = ErrorEvent(
            module="test",
            error_type="Err",
            message="msg",
            severity="ERROR",
            structured_context=ErrorContext(module="auto_fixed"),
            context={},
        )
        with patch("core.messaging.event_bus.logger.critical") as mock_critical:
            await bus.emit_async(event)
            await asyncio.sleep(0.05)
            mock_critical.assert_called()

    @pytest.mark.asyncio
    async def test_process_dead_letter_queue_returns_items(self):
        from core.messaging.event_bus import DeadLetterQueueItem, ErrorEventBus

        bus = ErrorEventBus()
        item = DeadLetterQueueItem(event_type="e", handler_name="h", error="err", timestamp=datetime.now(UTC))
        bus._dlq.put_nowait(item)
        processed = await bus.process_dead_letter_queue(max_items=10)
        assert len(processed) == 1
        assert processed[0].retry_count == 1

    def test_stats_property(self):
        from core.messaging.event_bus import ErrorEventBus

        bus = ErrorEventBus()
        stats = bus.stats
        assert "total_emitted" in stats
        assert "dlq_current_size" in stats


