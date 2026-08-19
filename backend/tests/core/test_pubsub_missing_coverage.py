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


# ========================== pubsub.py ==========================


class TestPubSubMissingBranches:
    @pytest.mark.asyncio
    async def test_subscribe_creates_channel(self):
        from core.messaging.pubsub import PubSub

        pubsub = PubSub()
        q = await pubsub.subscribe("ch1")
        assert "ch1" in pubsub.subscribers
        assert q in pubsub.subscribers["ch1"]

    @pytest.mark.asyncio
    async def test_unsubscribe_removes_channel_when_empty(self):
        from core.messaging.pubsub import PubSub

        pubsub = PubSub()
        q = await pubsub.subscribe("ch1")
        await pubsub.unsubscribe("ch1", q)
        assert "ch1" not in pubsub.subscribers

    @pytest.mark.asyncio
    async def test_unsubscribe_nonexistent_channel(self):
        from core.messaging.pubsub import PubSub

        pubsub = PubSub()
        q = MagicMock()
        await pubsub.unsubscribe("missing", q)

    @pytest.mark.asyncio
    async def test_publish_no_subscribers(self):
        from core.messaging.pubsub import PubSub

        pubsub = PubSub()
        await pubsub.publish("missing", {"msg": 1})

    @pytest.mark.asyncio
    async def test_publish_delivers_to_subscribers(self):
        from core.messaging.pubsub import PubSub

        pubsub = PubSub()
        q = await pubsub.subscribe("ch1")
        msg = {"msg": 1}
        await pubsub.publish("ch1", msg)
        received = await q.get()
        assert received == msg


