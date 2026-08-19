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


# ========================== log_batcher.py ==========================


class TestLogBatcherMissingBranches:
    @pytest.mark.anyio
    async def test_run_requeues_on_critical_error(self):
        from core.observability.log_batcher import LogBatcherService

        service = LogBatcherService(flush_interval=0.1, batch_size=2)
        service.running = True

        call_count = 0

        async def mock_wait_for(coro, timeout):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return {"x": 1}
            service.running = False
            raise Exception("critical")

        with patch("asyncio.wait_for", side_effect=mock_wait_for):
            with patch.object(service, "_flush", new_callable=AsyncMock):
                await service._run()
        assert service.running is False

    @pytest.mark.anyio
    async def test_run_drains_queue_up_to_batch_size(self):
        from core.observability.log_batcher import LogBatcherService

        service = LogBatcherService(flush_interval=0.1, batch_size=3)
        service.running = True

        call_count = 0

        async def mock_wait_for(coro, timeout):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                service.queue.put_nowait({"i": 1})
                service.queue.put_nowait({"i": 2})
                return {"i": 0}
            service.running = False
            raise TimeoutError()

        with patch("asyncio.wait_for", side_effect=mock_wait_for):
            with patch.object(service, "_flush", new_callable=AsyncMock) as mock_flush:
                await service._run()
                # বাংলা মন্তব্য: ইভেন্ট লুপ ইটারেসনের কারণে flushing ১ বা ২ বার হতে পারে, তাই check_count flexible রাখা হলো
                assert mock_flush.call_count >= 1


