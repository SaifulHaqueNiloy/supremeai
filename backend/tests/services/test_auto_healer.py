"""Tests for services/auto_healer.py — Auto-healing service."""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from services.auto_healer import AutoHealer


class TestAutoHealer:
    """Auto-healer: detection, diagnosis, remediation."""

    def test_init(self):
        healer = AutoHealer()
        assert healer is not None

    @pytest.mark.asyncio
    async def test_check_health_returns_dict(self):
        healer = AutoHealer()
        with patch.object(healer, '_get_system_state', return_value={"status": "ok"}):
            result = await healer.check_health()
            assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_diagnose_issue(self):
        healer = AutoHealer()
        with patch.object(healer, '_get_system_state', return_value={"error": "OOM"}):
            result = await healer.diagnose({"error": "OOM"})
            assert result is not None

    @pytest.mark.asyncio
    async def test_remediate_returns_result(self):
        healer = AutoHealer()
        result = await healer.remediate({"issue": "high_memory"})
        assert result is not None
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_no_issue_detected(self):
        healer = AutoHealer()
        with patch.object(healer, '_get_system_state', return_value={"status": "healthy"}):
            result = await healer.check_health()
            assert result.get("healthy") is True or result.get("status") == "ok"
