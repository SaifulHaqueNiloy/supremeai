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


# ========================== nats_messaging.py ==========================


class TestNATSMessagingMissingBranches:
    def test_init_defaults(self):
        try:
            from core.messaging.nats_messaging import NATSClient
        except ImportError:
            pytest.skip("nats module not installed")
        client = NATSClient()
        assert client.url == "nats://localhost:4222"
        # বাংলা মন্তব্য: token এখন NATS_TOKEN env var থেকে ডিফল্ট হিসেবে আসে
        assert client.token == os.getenv("NATS_TOKEN")
        assert client.nc is None
        assert client.js is None
        assert client.kv_store is None

    @pytest.mark.asyncio
    async def test_connect_creates_kv_store(self, monkeypatch):
        from core.messaging.nats_messaging import NATSClient
        from core.messaging.nats_messaging import nats as nats_module

        if nats_module is None:
            pytest.skip("nats module not installed")
        client = NATSClient()
        mock_nc = MagicMock()
        mock_js = MagicMock()
        mock_kv = MagicMock()
        mock_nc.jetstream.return_value = mock_js
        mock_js.key_value.side_effect = Exception("not found")
        mock_js.create_key_value = AsyncMock(return_value=mock_kv)

        with patch(
            "core.messaging.nats_messaging.nats.connect",
            new_callable=AsyncMock,
            return_value=mock_nc,
        ):
            await client.connect()

        assert client.nc is mock_nc
        assert client.js is mock_js
        assert client.kv_store is mock_kv

    @pytest.mark.asyncio
    async def test_publish_event_skips_when_not_connected(self, caplog):
        try:
            from core.messaging.nats_messaging import NATSClient
        except ImportError:
            pytest.skip("nats module not installed")
        client = NATSClient()
        await client.publish_event("subj", {"a": 1})
        assert "NATS client is not connected" in caplog.text

    @pytest.mark.asyncio
    async def test_publish_event_publishes_payload(self):
        try:
            from core.messaging.nats_messaging import NATSClient
        except ImportError:
            pytest.skip("nats module not installed")
        from pydantic import BaseModel

        client = NATSClient()
        client.nc = MagicMock()
        client.nc.publish = AsyncMock()

        class Dummy(BaseModel):
            a: int

        await client.publish_event("subj", Dummy(a=1))
        client.nc.publish.assert_called_once()
        args = client.nc.publish.call_args
        assert args[0][0] == "subj"
        assert json.loads(args[0][1].decode()) == {"a": 1}

    @pytest.mark.asyncio
    async def test_subscribe_skips_when_not_connected(self, caplog):
        try:
            from core.messaging.nats_messaging import NATSClient
        except ImportError:
            pytest.skip("nats module not installed")
        client = NATSClient()
        cb = MagicMock()
        await client.subscribe("subj", cb)
        assert "NATS client is not connected" in caplog.text

    @pytest.mark.asyncio
    async def test_register_and_get_worker(self):
        try:
            from core.messaging.nats_messaging import NATSClient
        except ImportError:
            pytest.skip("nats module not installed")
        client = NATSClient()
        client.kv_store = MagicMock()
        client.kv_store.put = AsyncMock()
        client.kv_store.get = AsyncMock(return_value=MagicMock(value=json.dumps({"id": "w1"}).encode()))

        await client.register_worker("w1", {"id": "w1"})
        worker = await client.get_worker("w1")
        assert worker == {"id": "w1"}

    @pytest.mark.asyncio
    async def test_get_worker_returns_none_on_missing(self):
        from core.messaging.nats_messaging import KeyValueError, NATSClient

        client = NATSClient()
        client.kv_store = MagicMock()
        client.kv_store.get = AsyncMock(side_effect=KeyValueError("missing"))
        assert await client.get_worker("missing") is None

    @pytest.mark.asyncio
    async def test_get_all_workers_returns_empty_when_no_kv(self):
        try:
            from core.messaging.nats_messaging import NATSClient
        except ImportError:
            pytest.skip("nats module not installed")
        client = NATSClient()
        assert await client.get_all_workers() == {}

    @pytest.mark.asyncio
    async def test_get_all_workers_lists_keys(self):
        try:
            from core.messaging.nats_messaging import NATSClient
        except ImportError:
            pytest.skip("nats module not installed")
        client = NATSClient()
        client.kv_store = MagicMock()
        client.kv_store.keys = AsyncMock(return_value=["w1"])
        entry = MagicMock()
        entry.value = json.dumps({"id": "w1"}).encode()
        client.kv_store.get = AsyncMock(return_value=entry)

        workers = await client.get_all_workers()
        assert workers == {"w1": {"id": "w1"}}


