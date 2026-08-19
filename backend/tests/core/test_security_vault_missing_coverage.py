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


# ========================== security_vault.py ==========================


class TestSecurityVaultModuleInit:
    def test_module_raises_without_encryption_key(self, monkeypatch):
        # বাংলা মন্তব্য: নতুন STRICT_ENCRYPTION_CHECK ফ্ল্যাগ সেট করে এক্সেপশন রেইজ পাথটি টেস্ট করা হচ্ছে।
        monkeypatch.setenv("STRICT_ENCRYPTION_CHECK", "true")
        monkeypatch.delenv("ENCRYPTION_KEY", raising=False)
        monkeypatch.delenv("ENCRYPTION_KEY", raising=False)

        monkeypatch.delitem(sys.modules, "core.security_vault", raising=False)
        monkeypatch.delitem(sys.modules, "core.security.security_vault", raising=False)

        with pytest.raises(ValueError, match="CRITICAL: ENCRYPTION_KEY"):
            import core.security.security_vault  # noqa: F401 -- import নিজেই side-effect হিসেবে ValueError raise করে, এটাই টেস্ট করা হচ্ছে


