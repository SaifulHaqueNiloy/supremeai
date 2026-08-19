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


# ========================== playwright_manager.py ==========================


class TestPlaywrightManagerMissingBranches:
    def test_imports_without_playwright(self, monkeypatch):
        monkeypatch.setitem(sys.modules, "playwright", None)
        monkeypatch.setitem(sys.modules, "playwright.async_api", None)
        monkeypatch.delitem(sys.modules, "core.playwright_manager", raising=False)
        import core.playwright_manager as pm

        assert pm.async_playwright is None

    @pytest.mark.asyncio
    async def test_get_global_browser_raises_when_not_installed(self, monkeypatch):
        import core.playwright_manager as pm

        monkeypatch.setattr(pm, "_global_browser", None)

        import builtins

        original_callable = builtins.callable

        def mock_callable(obj):
            if getattr(obj, "__name__", "") == "async_playwright":
                return False
            return original_callable(obj)

        monkeypatch.setattr(builtins, "callable", mock_callable)

        with pytest.raises(RuntimeError, match="Playwright is not installed"):
            await pm.get_global_browser()

    @pytest.mark.asyncio
    async def test_shutdown_global_browser_handles_errors(self, monkeypatch):
        from core.playwright_manager import shutdown_global_browser

        mock_browser = MagicMock()
        mock_runner = MagicMock()
        monkeypatch.setattr("core.playwright_manager._global_browser", mock_browser)
        monkeypatch.setattr("core.playwright_manager._playwright_runner", mock_runner)
        monkeypatch.setattr(
            "core.playwright_manager._global_browser.close",
            AsyncMock(side_effect=RuntimeError("close fail")),
        )
        monkeypatch.setattr(
            "core.playwright_manager._playwright_runner.stop",
            AsyncMock(side_effect=RuntimeError("stop fail")),
        )

        # The function should complete without raising, even with errors
        await shutdown_global_browser()
        assert True


