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


# ========================== container_auditor.py ==========================


class TestContainerAuditorMissingBranches:
    def test_get_container_stats_returns_list_on_success(self, monkeypatch):
        from core.container_auditor import ContainerAuditor

        auditor = ContainerAuditor(check_interval_seconds=1)
        fake_stdout = json.dumps({"Name": "c1", "MemPerc": "10.5%"}) + "\n"
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = fake_stdout
        mock_result.stderr = ""

        monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: mock_result)
        stats = auditor.get_container_stats()
        assert isinstance(stats, list)
        assert stats[0]["Name"] == "c1"

    def test_get_container_stats_returns_empty_on_failure(self, monkeypatch):
        from core.container_auditor import ContainerAuditor

        auditor = ContainerAuditor(check_interval_seconds=1)
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "docker error"
        monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: mock_result)
        assert auditor.get_container_stats() == []

    def test_get_container_stats_handles_exception(self, monkeypatch):
        from core.container_auditor import ContainerAuditor

        auditor = ContainerAuditor(check_interval_seconds=1)
        monkeypatch.setattr(
            "subprocess.run",
            lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("boom")),
        )
        assert auditor.get_container_stats() == []

    def test_parse_memory_percent_valid(self):
        from core.container_auditor import ContainerAuditor

        auditor = ContainerAuditor()
        assert auditor.parse_memory_percent("85.3%") == 85.3

    def test_parse_memory_percent_invalid(self):
        from core.container_auditor import ContainerAuditor

        auditor = ContainerAuditor()
        assert auditor.parse_memory_percent("not-a-number") == 0.0

    @pytest.mark.asyncio
    async def test_audit_cycle_warns_below_kill_threshold(self, monkeypatch):
        from core.container_auditor import ContainerAuditor

        auditor = ContainerAuditor(check_interval_seconds=1)
        monkeypatch.setattr(auditor, "get_container_stats", lambda: [{"Name": "c1", "MemPerc": "82.0%"}])
        with patch("core.container_auditor.logger.warning") as mock_warning:
            await auditor.audit_cycle()
            mock_warning.assert_called_once()

    @pytest.mark.asyncio
    async def test_audit_cycle_kills_above_threshold(self, monkeypatch):
        from core.container_auditor import ContainerAuditor

        auditor = ContainerAuditor(check_interval_seconds=1)
        monkeypatch.setattr(auditor, "get_container_stats", lambda: [{"Name": "c1", "MemPerc": "96.0%"}])
        with (
            patch("core.container_auditor.logger.error") as mock_error,
            patch("subprocess.run") as mock_run,
        ):
            await auditor.audit_cycle()
            mock_error.assert_called()
            mock_run.assert_called_once()

    @pytest.mark.asyncio
    async def test_audit_cycle_kill_failure_logs(self, monkeypatch):
        from core.container_auditor import ContainerAuditor

        auditor = ContainerAuditor(check_interval_seconds=1)
        monkeypatch.setattr(auditor, "get_container_stats", lambda: [{"Name": "c1", "MemPerc": "99.0%"}])
        with (
            patch("core.container_auditor.logger.error") as mock_error,
            patch("subprocess.run", side_effect=RuntimeError("kill fail")),
        ):
            await auditor.audit_cycle()
            mock_error.assert_called()

    @pytest.mark.asyncio
    async def test_run_stops_on_exception(self, monkeypatch):
        from core.container_auditor import ContainerAuditor

        auditor = ContainerAuditor(check_interval_seconds=0.01)
        call_count = 0

        async def fake_audit():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RuntimeError("cycle fail")
            auditor.stop()

        monkeypatch.setattr(auditor, "audit_cycle", fake_audit)
        await auditor.run()
        assert auditor.running is False

    def test_stop_sets_running_false(self):
        from core.container_auditor import ContainerAuditor

        auditor = ContainerAuditor()
        auditor.running = True
        auditor.stop()
        assert auditor.running is False


