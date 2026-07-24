"""Tests for core.security.origin_validator — TrustedOriginMiddleware."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.responses import JSONResponse
from starlette.types import ASGIApp

from core.security.origin_validator import TrustedOriginMiddleware


class TestTrustedOriginMiddleware:
    """Tests for TrustedOriginMiddleware."""

    async def test_non_http_scope_passes_through(self):
        """Non-HTTP scopes (e.g. websocket) pass through."""
        app = AsyncMock()
        middleware = TrustedOriginMiddleware(app)
        scope = {"type": "websocket"}
        await middleware.dispatch(
            MagicMock(url=MagicMock(path="/ws"), headers={}, method="GET"),
            app,
        )

    async def test_options_preflight_allowed_origin(self):
        """OPTIONS preflight with allowed origin returns 200."""
        app = AsyncMock()
        middleware = TrustedOriginMiddleware(app)
        request = MagicMock()
        request.method = "OPTIONS"
        request.headers = {"Origin": "https://supremeai-admin.web.app", "host": "localhost"}
        request.url.path = "/api/test"

        response = await middleware.dispatch(request, app)
        assert response.status_code == 200

    async def test_options_preflight_no_origin(self):
        """OPTIONS without origin is allowed."""
        app = AsyncMock()
        middleware = TrustedOriginMiddleware(app)
        request = MagicMock()
        request.method = "OPTIONS"
        request.headers = {"host": "localhost"}
        request.url.path = "/api/test"

        response = await middleware.dispatch(request, app)
        assert response.status_code == 200

    async def test_test_environment_bypasses_check(self, monkeypatch):
        """Test environment allows all origins."""
        monkeypatch.setenv("ENV", "test")
        app = AsyncMock()
        middleware = TrustedOriginMiddleware(app)
        request = MagicMock()
        request.method = "GET"
        request.headers = {"host": "testserver", "Origin": "http://evil.com"}
        request.url.path = "/api/test"

        await middleware.dispatch(request, app)

    async def test_public_path_bypasses_origin_check(self, monkeypatch):
        """Public paths bypass origin validation."""
        monkeypatch.setenv("ENV", "production")
        app = AsyncMock()
        middleware = TrustedOriginMiddleware(app)
        request = MagicMock()
        request.method = "GET"
        request.headers = {"host": "localhost", "Origin": "http://evil.com"}
        request.url.path = "/health"

        # /health is a public path
        from core.config import settings

        old_paths = settings.supremeai_public_paths
        settings.supremeai_public_paths = ["/health"]
        try:
            response = await middleware.dispatch(request, app)
            # Should not block public paths
            assert not isinstance(response, JSONResponse) or response.status_code != 403
        finally:
            settings.supremeai_public_paths = old_paths

    async def test_blocked_unauthorized_origin(self, monkeypatch):
        """Unauthorized origin in production returns 403."""
        monkeypatch.setenv("ENV", "production")
        app = AsyncMock()
        middleware = TrustedOriginMiddleware(app)
        request = MagicMock()
        request.method = "GET"
        request.headers = {"host": "localhost", "Origin": "http://evil-hacker.com"}
        request.url.path = "/api/protected"
        request.client.host = "10.0.0.5"

        with patch.object(middleware, "allowed_origins", {"https://trusted.com"}):
            response = await middleware.dispatch(request, app)
            assert response.status_code == 403

    async def test_allowed_origin_passes(self, monkeypatch):
        """Allowed origin passes through."""
        monkeypatch.setenv("ENV", "production")
        app = AsyncMock()
        middleware = TrustedOriginMiddleware(app)
        request = MagicMock()
        request.method = "GET"
        request.headers = {"host": "localhost", "Origin": "https://trusted.com"}
        request.url.path = "/api/protected"

        with patch.object(middleware, "allowed_origins", {"https://trusted.com"}):
            await middleware.dispatch(request, app)

    async def test_missing_origin_passes(self, monkeypatch):
        """Missing Origin header passes through in production."""
        monkeypatch.setenv("ENV", "production")
        app = AsyncMock()
        middleware = TrustedOriginMiddleware(app)
        request = MagicMock()
        request.method = "GET"
        request.headers = {"host": "localhost"}
        request.url.path = "/api/protected"

        await middleware.dispatch(request, app)

    async def test_allowed_origins_property(self):
        """allowed_origins combines configured and defaults."""
        app = AsyncMock()
        middleware = TrustedOriginMiddleware(app)
        origins = middleware.allowed_origins
        assert "https://supremeai-admin.web.app" in origins
        assert "https://supremeai-backend.onrender.com" in origins
