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


# ========================== security_utils.py ==========================


class TestSecurityUtilsMissingBranches:
    def test_is_safe_url_rejects_private_ip(self):
        from core.security import is_safe_url

        assert is_safe_url("http://192.168.1.1/test") is False

    def test_is_safe_url_rejects_localhost(self):
        from core.security import is_safe_url

        assert is_safe_url("http://localhost/test") is False

    def test_is_safe_url_rejects_metadata_endpoint(self):
        from core.security import is_safe_url

        assert is_safe_url("http://169.254.169.254/latest/meta-data/") is False

    def test_is_safe_url_accepts_public_url(self):
        from core.security import is_safe_url

        assert is_safe_url("https://example.com/test") is True


