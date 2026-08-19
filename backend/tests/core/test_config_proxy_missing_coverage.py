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


# ========================== config_proxy.py ==========================


class TestConfigProxyMissingBranches:
    @pytest.mark.asyncio
    async def test_get_refreshes_after_expiry(self):
        from core.config_proxy import DynamicConfigProxy

        proxy = DynamicConfigProxy("t1", MagicMock())
        proxy._cache = {"k": "old"}
        proxy._expiry = datetime.min.replace(tzinfo=UTC)

        doc_ref = MagicMock()
        snapshot = MagicMock()
        snapshot.exists = True
        snapshot.to_dict.return_value = {"k": "new"}
        doc_ref.get.return_value = snapshot
        proxy._db.collection.return_value.document.return_value = doc_ref

        # বাংলা মন্তব্য: async event loop runtime error এড়াতে async def এবং await ব্যবহার করা হলো
        result = await proxy.get("k")
        assert result == "new"

    @pytest.mark.asyncio
    async def test_get_uses_sync_get_when_not_coroutine(self):
        from core.config_proxy import DynamicConfigProxy

        proxy = DynamicConfigProxy("t1", MagicMock())
        proxy._cache = {"k": "val"}
        proxy._expiry = datetime.min.replace(tzinfo=UTC)

        doc_ref = MagicMock()
        snapshot = MagicMock()
        snapshot.exists = True
        snapshot.to_dict.return_value = {"k": "new"}
        doc_ref.get = MagicMock(return_value=snapshot)
        proxy._db.collection.return_value.document.return_value = doc_ref

        # বাংলা মন্তব্য: async event loop runtime error এড়াতে async def এবং await ব্যবহার করা হলো
        result = await proxy.get("k")
        assert result == "new"


