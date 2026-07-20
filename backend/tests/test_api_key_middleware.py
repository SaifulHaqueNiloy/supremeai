"""Tests for API Key Authentication Middleware.

This module tests:
- API key validation
- Rate limiting enforcement
- Key expiration checks
- Revoked key handling
"""

import pytest
from unittest.mock import AsyncMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.responses import PlainTextResponse

from core.security.api_key_middleware import APIKeyAuthMiddleware
from core.security import hash_api_key, mask_api_key


# --- Helper Fixtures ---


@pytest.fixture
def mock_db_pool():
    """Mock database pool for API key lookups."""
    pool = AsyncMock()
    return pool


# --- Middleware Tests ---


class TestAPIKeyAuthMiddleware:
    """Tests for APIKeyAuthMiddleware class."""

    def test_allows_request_without_api_key(self):
        """Test that requests without x-api-key header pass through."""
        app = FastAPI()

        @app.get("/api/test")
        def test_endpoint():
            return PlainTextResponse("ok")

        app.add_middleware(APIKeyAuthMiddleware)
        client = TestClient(app)

        resp = client.get("/api/test")
        assert resp.status_code == 200
        assert resp.text == "ok"

    def test_allows_request_with_wrong_prefix(self):
        """Test that requests with wrong prefix pass through."""
        app = FastAPI()

        @app.get("/api/test")
        def test_endpoint():
            return PlainTextResponse("ok")

        app.add_middleware(APIKeyAuthMiddleware)
        client = TestClient(app)

        resp = client.get("/api/test", headers={"x-api-key": "wrong_prefix_key"})
        assert resp.status_code == 200

    def test_allows_test_environment(self):
        """Test that test environment is allowed with test key prefix."""
        app = FastAPI()

        @app.get("/api/test")
        def test_endpoint():
            return PlainTextResponse("ok")

        app.add_middleware(APIKeyAuthMiddleware)
        client = TestClient(app)

        # Mock is_test_environment to return True
        with patch("core.security.api_key_middleware.is_test_environment", return_value=True):
            resp = client.get("/api/test", headers={"x-api-key": "sk-test_1234567890abcdef"})

        assert resp.status_code == 200

    def test_validates_valid_api_key(self):
        """Test that valid API key is accepted."""
        app = FastAPI()

        @app.get("/api/test")
        def test_endpoint(request):
            return PlainTextResponse(f"user: {getattr(request.state, 'api_key', {}).get('id', 'none')}")

        app.add_middleware(APIKeyAuthMiddleware)
        client = TestClient(app)

        mock_row = {
            "id": "key-123",
            "key_hash": "hashed_key",
            "revoked": False,
            "rate_limit_rps": 10,
            "expires_at": None,
        }

        with (
            patch("core.security.api_key_middleware.is_test_environment", return_value=False),
            patch("core.security.api_key_middleware.get_db_pool") as mock_pool,
            patch("core.security.api_key_middleware.hash_api_key", return_value="hashed_key"),
        ):
            mock_pool.return_value.fetchrow = AsyncMock(return_value=mock_row)

            resp = client.get(
                "/api/test",
                headers={"x-api-key": "sk-live_1234567890abcdef"},
            )

        assert resp.status_code == 200

    def test_rejects_invalid_api_key(self):
        """Test that invalid API key is rejected."""
        app = FastAPI()

        @app.get("/api/test")
        def test_endpoint():
            return PlainTextResponse("ok")

        app.add_middleware(APIKeyAuthMiddleware)
        client = TestClient(app)

        with (
            patch("core.security.api_key_middleware.is_test_environment", return_value=False),
            patch("core.security.api_key_middleware.get_db_pool") as mock_pool,
            patch("core.security.api_key_middleware.hash_api_key", return_value="hashed_key"),
        ):
            mock_pool.return_value.fetchrow = AsyncMock(return_value=None)

            resp = client.get(
                "/api/test",
                headers={"x-api-key": "sk-live_1234567890abcdef"},
            )

        assert resp.status_code == 401

    def test_rejects_revoked_api_key(self):
        """Test that revoked API key is rejected."""
        app = FastAPI()

        @app.get("/api/test")
        def test_endpoint():
            return PlainTextResponse("ok")

        app.add_middleware(APIKeyAuthMiddleware)
        client = TestClient(app)

        mock_row = {
            "id": "key-123",
            "key_hash": "hashed_key",
            "revoked": True,
            "rate_limit_rps": 10,
            "expires_at": None,
        }

        with (
            patch("core.security.api_key_middleware.is_test_environment", return_value=False),
            patch("core.security.api_key_middleware.get_db_pool") as mock_pool,
            patch("core.security.api_key_middleware.hash_api_key", return_value="hashed_key"),
        ):
            mock_pool.return_value.fetchrow = AsyncMock(return_value=mock_row)

            resp = client.get(
                "/api/test",
                headers={"x-api-key": "sk-live_1234567890abcdef"},
            )

        assert resp.status_code == 403

    def test_rejects_expired_api_key(self):
        """Test that expired API key is rejected."""
        import time

        app = FastAPI()

        @app.get("/api/test")
        def test_endpoint():
            return PlainTextResponse("ok")

        app.add_middleware(APIKeyAuthMiddleware)
        client = TestClient(app)

        mock_row = {
            "id": "key-123",
            "key_hash": "hashed_key",
            "revoked": False,
            "rate_limit_rps": 10,
            "expires_at": time.time() - 3600,  # Expired 1 hour ago
        }

        with (
            patch("core.security.api_key_middleware.is_test_environment", return_value=False),
            patch("core.security.api_key_middleware.get_db_pool") as mock_pool,
            patch("core.security.api_key_middleware.hash_api_key", return_value="hashed_key"),
        ):
            mock_pool.return_value.fetchrow = AsyncMock(return_value=mock_row)

            resp = client.get(
                "/api/test",
                headers={"x-api-key": "sk-live_1234567890abcdef"},
            )

        assert resp.status_code == 403

    def test_rate_limit_exceeded(self):
        """Test that rate-limited request is rejected."""
        app = FastAPI()

        @app.get("/api/test")
        def test_endpoint():
            return PlainTextResponse("ok")

        app.add_middleware(APIKeyAuthMiddleware)
        client = TestClient(app)

        mock_row = {
            "id": "key-123",
            "key_hash": "hashed_key",
            "revoked": False,
            "rate_limit_rps": 1,
            "expires_at": None,
        }

        with (
            patch("core.security.api_key_middleware.is_test_environment", return_value=False),
            patch("core.security.api_key_middleware.get_db_pool") as mock_pool,
            patch("core.security.api_key_middleware.hash_api_key", return_value="hashed_key"),
            patch("core.security.api_key_middleware.AsyncRateLimiter.acquire", return_value=False),
        ):
            mock_pool.return_value.fetchrow = AsyncMock(return_value=mock_row)

            resp = client.get(
                "/api/test",
                headers={"x-api-key": "sk-live_1234567890abcdef"},
            )

        assert resp.status_code == 429


# --- Hash and Mask Utilities Tests ---


def test_mask_api_key():
    """Test API key masking hides sensitive parts."""
    full_key = "sk-live_1234567890abcdef1234567890abcdef"
    masked = mask_api_key(full_key)

    # Should show only first 12 chars
    assert masked.startswith("sk-live_123")
    assert len(masked) == 12


def test_hash_api_key():
    """Test API key hashing returns consistent hash."""
    key = "sk-live_1234567890abcdef"
    hash1 = hash_api_key(key)
    hash2 = hash_api_key(key)

    # Should be consistent
    assert hash1 == hash2
    # Should not contain original key
    assert key not in hash1
