"""Tests for core.security.audit_logger — log_security_event."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.security.audit_logger import (
    AUDIT_LIST_PREFIX,
    AUDIT_PREFIX,
    log_security_event,
)


class TestLogSecurityEvent:
    """Tests for log_security_event function."""

    async def test_log_event_returns_event_id(self):
        """log_security_event returns a string event_id."""
        event_id = await log_security_event(
            event_type="LOGIN_SUCCESS",
            user_id="user-123",
            details={"ip": "127.0.0.1"},
            severity="INFO",
        )
        assert isinstance(event_id, str)
        assert event_id.startswith("sec-")

    async def test_log_event_without_redis(self, monkeypatch):
        """Event logging works without Redis."""
        monkeypatch.setenv("REDIS_URL", "")
        from core.cache.redis_manager import redis_manager

        redis_manager._initialized = False
        redis_manager._client = None

        event_id = await log_security_event(
            event_type="TEST_EVENT",
            user_id="user-456",
            details={"action": "test"},
            severity="DEBUG",
        )
        assert event_id.startswith("sec-")

    async def test_log_event_critical_severity(self):
        """Critical severity events are logged."""
        event_id = await log_security_event(
            event_type="SECURITY_BREACH",
            user_id="admin-1",
            details={"ip": "10.0.0.5"},
            severity="CRITICAL",
        )
        assert event_id.startswith("sec-")

    async def test_log_event_with_none_user(self):
        """Events with None user_id are handled."""
        event_id = await log_security_event(
            event_type="ANONYMOUS_ACCESS",
            user_id=None,
            details={"path": "/public"},
        )
        assert event_id.startswith("sec-")

    async def test_log_event_high_severity(self):
        """High severity events are logged."""
        event_id = await log_security_event(
            event_type="RATE_LIMIT_EXCEEDED",
            user_id="user-789",
            details={"rate": "100/min"},
            severity="HIGH",
        )
        assert event_id.startswith("sec-")

    async def test_log_event_with_redis_mock(self):
        """Event is persisted to Redis when client available."""
        mock_redis = MagicMock()
        mock_redis.client = MagicMock()
        mock_pipe = MagicMock()
        mock_redis.client.pipeline.return_value = mock_pipe

        with patch("core.security.audit_logger.redis_manager", mock_redis):
            event_id = await log_security_event(
                event_type="API_KEY_CREATED",
                user_id="admin-2",
                details={"key_name": "test-key"},
            )
            assert event_id.startswith("sec-")
            mock_redis.client.pipeline.assert_called_once()
            mock_pipe.setex.assert_called_once()
            mock_pipe.lpush.assert_called_once()
            mock_pipe.ltrim.assert_called_once()
            mock_pipe.execute.assert_called_once()

    async def test_log_event_redis_failure_graceful(self):
        """Redis failure does not crash the event logging."""
        mock_redis = MagicMock()
        mock_redis.client = MagicMock()
        mock_redis.client.pipeline.side_effect = Exception("Redis connection failed")

        with patch("core.security.audit_logger.redis_manager", mock_redis):
            event_id = await log_security_event(
                event_type="TEST",
                user_id="user",
                details={},
            )
            assert event_id.startswith("sec-")
