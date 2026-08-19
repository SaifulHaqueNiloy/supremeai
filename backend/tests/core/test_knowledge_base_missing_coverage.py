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


# ========================== knowledge_base.py ==========================


class TestKnowledgeBaseMissingBranches:
    def test_module_creates_data_dir_and_file(self, monkeypatch, tmp_path):
        import importlib

        # বাংলা মন্তব্য: reloading logic matching এর জন্য environmental variables set করা হলো
        monkeypatch.setenv("SUPREMEAI_BASE_DIR", str(tmp_path))
        monkeypatch.setenv("SUPREMEAI_DATA_DIR", str(tmp_path / "data"))
        monkeypatch.setenv("SUPREMEAI_MEMORY_FILE_PATH", str(tmp_path / "data" / "memory_vault.json"))

        import core.knowledge_base as kb

        importlib.reload(kb)

        assert (tmp_path / "data").exists()
        assert (tmp_path / "data" / "memory_vault.json").exists()


