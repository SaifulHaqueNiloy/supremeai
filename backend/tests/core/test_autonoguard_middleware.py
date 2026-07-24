"""Tests for core.security.autonoguard_middleware — AutonoGuardMiddleware."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import Request
from starlette.types import ASGIApp

from core.security.autonoguard_middleware import AutonoGuardMiddleware


class TestAutonoGuardMiddleware:
    """Tests for AutonoGuardMiddleware."""

    async def test_non_sensitive_path_passes(self, monkeypatch):
        """Non-sensitive path passes through without checks."""
        monkeypatch.setenv("ENV", "test")
        app = AsyncMock(return_value=None)
        middleware = AutonoGuardMiddleware(app)
        middleware._initialized = True

        request = MagicMock(spec=Request)
        request.url.path = "/api/chat"
        request.method = "GET"
        request.state.user = {"sub": "admin-1", "role": "admin"}
        request.client.host = "127.0.0.1"

        await middleware.dispatch(request, app)
        app.assert_called_once()

    async def test_public_path_skips_check(self, monkeypatch):
        """Public path skips AutonoGuard check."""
        monkeypatch.setenv("ENV", "test")
        app = AsyncMock(return_value=None)
        middleware = AutonoGuardMiddleware(app)
        middleware._initialized = True

        request = MagicMock(spec=Request)
        request.url.path = "/health"
        request.method = "GET"

        await middleware.dispatch(request, app)
        app.assert_called_once()

    async def test_sensitive_path_calls_enforce(self):
        """Sensitive path calls enforce_operation."""
        app = AsyncMock(return_value=None)
        middleware = AutonoGuardMiddleware(app)
        middleware._initialized = True

        request = MagicMock(spec=Request)
        request.url.path = "/api/admin/users"
        request.method = "POST"
        request.state.user = {"sub": "admin-1", "role": "admin"}
        request.client.host = "127.0.0.1"
        request.headers = {"X-JIT-OTP": "123456"}

        with patch("core.security.autonoguard_middleware.autonoguard_engine") as mock_engine:
            mock_engine.enforce_operation.return_value = (True, None)
            await middleware.dispatch(request, app)
            mock_engine.enforce_operation.assert_called_once()

    async def test_sensitive_path_denied_returns_401(self):
        """Sensitive path denied returns 401."""
        app = AsyncMock()
        middleware = AutonoGuardMiddleware(app)
        middleware._initialized = True

        request = MagicMock(spec=Request)
        request.url.path = "/api/admin/billing"
        request.method = "POST"
        request.state.user = {"sub": "admin-1", "role": "admin"}
        request.client.host = "10.0.0.5"
        request.headers = {}
        request.url = MagicMock()
        request.url.path = "/api/admin/billing"

        with patch("core.security.autonoguard_middleware.autonoguard_engine") as mock_engine:
            mock_engine.enforce_operation.return_value = (False, "OTP required")
            response = await middleware.dispatch(request, app)
            assert response.status_code == 401
            app.assert_not_called()

    async def test_no_user_in_state(self):
        """No user in state defaults to 'unknown'."""
        app = AsyncMock(return_value=None)
        middleware = AutonoGuardMiddleware(app)
        middleware._initialized = True

        request = MagicMock(spec=Request)
        request.url.path = "/api/admin/settings"
        request.method = "PUT"
        del request.state.user
        request.client.host = "127.0.0.1"
        request.headers = {}

        with patch("core.security.autonoguard_middleware.autonoguard_engine") as mock_engine:
            mock_engine.enforce_operation.return_value = (True, None)
            await middleware.dispatch(request, app)
            _, kwargs = mock_engine.enforce_operation.call_args
            assert kwargs["admin_id"] == "unknown"

    async def test_otp_from_headers(self):
        """OTP is extracted from X-JIT-OTP header."""
        app = AsyncMock(return_value=None)
        middleware = AutonoGuardMiddleware(app)
        middleware._initialized = True

        request = MagicMock(spec=Request)
        request.url.path = "/api/admin/deploy"
        request.method = "POST"
        request.state.user = {"sub": "admin-1"}
        request.client.host = "127.0.0.1"
        request.headers = {"X-JIT-OTP": "654321"}

        with patch("core.security.autonoguard_middleware.autonoguard_engine") as mock_engine:
            mock_engine.enforce_operation.return_value = (True, None)
            await middleware.dispatch(request, app)
            _, kwargs = mock_engine.enforce_operation.call_args
            assert kwargs["otp_code"] == "654321"

    async def test_otp_from_x_otp_header(self):
        """OTP is extracted from X-OTP header fallback."""
        app = AsyncMock(return_value=None)
        middleware = AutonoGuardMiddleware(app)
        middleware._initialized = True

        request = MagicMock(spec=Request)
        request.url.path = "/api/admin/config"
        request.method = "POST"
        request.state.user = {"sub": "admin-1"}
        request.client.host = "127.0.0.1"
        request.headers = {"X-OTP": "111222"}

        with patch("core.security.autonoguard_middleware.autonoguard_engine") as mock_engine:
            mock_engine.enforce_operation.return_value = (True, None)
            await middleware.dispatch(request, app)
            _, kwargs = mock_engine.enforce_operation.call_args
            assert kwargs["otp_code"] == "111222"
