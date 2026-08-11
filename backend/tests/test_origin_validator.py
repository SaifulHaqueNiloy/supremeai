"""Tests for TrustedOriginMiddleware - CORS and trusted origin validation.

This module tests:
- Test environment bypass
- Localhost / 127.0.0.1 bypass
- Public paths bypass
- Origin header validation
- Host header validation
- CORS headers injection on response
"""

from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.responses import PlainTextResponse

from core.security.origin_validator import TrustedOriginMiddleware


class TestTrustedOriginMiddleware:
    """Tests for TrustedOriginMiddleware class."""

    def test_bypass_test_environment(self):
        """Test that test environment bypasses origin checks."""
        app = FastAPI()

        @app.get("/api/test")
        def test_endpoint():
            return PlainTextResponse("ok")

        app.add_middleware(TrustedOriginMiddleware)
        client = TestClient(app)

        # Mock ENV=test - patch at module level since middleware imports os locally
        with patch(
            "core.security.origin_validator.os.getenv", side_effect=lambda k, d=None: "test" if k == "ENV" else d
        ):
            resp = client.get("/api/test")

        assert resp.status_code == 200

    def test_bypass_localhost(self):
        """Test that localhost bypasses origin checks."""
        app = FastAPI()

        @app.get("/api/test")
        def test_endpoint():
            return PlainTextResponse("ok")

        app.add_middleware(TrustedOriginMiddleware)
        client = TestClient(app)

        # testserver is used by FastAPI's TestClient
        with patch(
            "core.security.origin_validator.os.getenv", side_effect=lambda k, d=None: "development" if k == "ENV" else d
        ):
            resp = client.get("/api/test")

        assert resp.status_code == 200

    def test_bypass_public_paths(self):
        """Test that public paths bypass origin checks."""
        app = FastAPI()

        @app.get("/api/v1/health")
        def health_endpoint():
            return PlainTextResponse("healthy")

        with patch("core.security.origin_validator.settings") as mock_settings:
            mock_settings.cors_origins = []
            mock_settings.supremeai_public_paths = ["/api/v1/health"]
            mock_settings.allowed_hosts = []

            app.add_middleware(TrustedOriginMiddleware)
            client = TestClient(app)

            resp = client.get("/api/v1/health")

        assert resp.status_code == 200

    def test_blocks_unauthorized_origin(self):
        """Test that unauthorized origin is blocked."""
        app = FastAPI()

        @app.get("/api/test")
        def test_endpoint():
            return PlainTextResponse("ok")

        with (
            patch("core.security.origin_validator.settings") as mock_settings,
            patch(
                "core.security.origin_validator.os.getenv",
                side_effect=lambda k, d=None: "production" if k == "ENV" else d,
            ),
        ):
            mock_settings.cors_origins = ["https://trusted.example.com"]
            mock_settings.supremeai_public_paths = []
            mock_settings.allowed_hosts = ["trusted.example.com"]

            app.add_middleware(TrustedOriginMiddleware)
            client = TestClient(app)

            resp = client.get(
                "/api/test",
                headers={
                    "Origin": "https://malicious.example.com",
                    "Host": "malicious.example.com",
                },
            )

        assert resp.status_code == 403

    def test_allows_authorized_origin(self):
        """Test that authorized origin is allowed."""
        app = FastAPI()

        @app.get("/api/test")
        def test_endpoint():
            return PlainTextResponse("ok")

        with (
            patch("core.security.origin_validator.settings") as mock_settings,
            patch(
                "core.security.origin_validator.os.getenv",
                side_effect=lambda k, d=None: "production" if k == "ENV" else d,
            ),
        ):
            mock_settings.cors_origins = ["https://trusted.example.com"]
            mock_settings.supremeai_public_paths = []
            mock_settings.allowed_hosts = ["trusted.example.com"]

            app.add_middleware(TrustedOriginMiddleware)
            client = TestClient(app)

            resp = client.get(
                "/api/test",
                headers={
                    "Origin": "https://trusted.example.com",
                    "Host": "trusted.example.com",
                },
            )

        assert resp.status_code == 200

    def test_allowed_origin_passes_through_without_duplicate_cors_headers(self):
        """Test an allowed origin's request passes through successfully.

        বাংলা মন্তব্য: TrustedOriginMiddleware আর নিজে Access-Control-Allow-Origin
        header যোগ করে না -- এটা এখন শুধুমাত্র app_user.py/app_admin.py-এর প্রকৃত
        CORSMiddleware (outer)-এর দায়িত্ব। এই মিডলওয়্যারকে একা টেস্ট করার সময়
        সেই outer CORSMiddleware উপস্থিত থাকে না, তাই এখানে header assert করা
        ঠিক না -- বরং allowed origin-এর request block না হওয়া (200 status)
        যাচাই করাই এই টেস্টের উদ্দেশ্য। Header-level CORS coverage
        test_app_isolation.py-তে পুরো app স্ট্যাক দিয়ে করা হয়।
        """
        app = FastAPI()

        @app.get("/api/test")
        def test_endpoint():
            return PlainTextResponse("ok")

        with (
            patch("core.security.origin_validator.settings") as mock_settings,
            patch(
                "core.security.origin_validator.os.getenv",
                side_effect=lambda k, d=None: "production" if k == "ENV" else d,
            ),
        ):
            mock_settings.cors_origins = ["https://trusted.example.com"]
            mock_settings.supremeai_public_paths = []
            mock_settings.allowed_hosts = ["trusted.example.com"]

            app.add_middleware(TrustedOriginMiddleware)
            client = TestClient(app)

            resp = client.get(
                "/api/test",
                headers={
                    "Origin": "https://trusted.example.com",
                    "Host": "trusted.example.com",
                },
            )

            assert resp.status_code == 200
            assert resp.text == "ok"

    def test_blocks_malicious_host(self):
        """Test that malicious host header is blocked."""
        app = FastAPI()

        @app.get("/api/test")
        def test_endpoint():
            return PlainTextResponse("ok")

        with (
            patch("core.security.origin_validator.settings") as mock_settings,
            patch(
                "core.security.origin_validator.os.getenv",
                side_effect=lambda k, d=None: "production" if k == "ENV" else d,
            ),
        ):
            mock_settings.cors_origins = []
            mock_settings.supremeai_public_paths = []
            mock_settings.allowed_hosts = ["trusted.example.com"]

            app.add_middleware(TrustedOriginMiddleware)
            client = TestClient(app)

            resp = client.get(
                "/api/test",
                headers={
                    "Host": "malicious.example.com",
                },
            )

        assert resp.status_code == 403

    def test_allows_subdomain_host(self):
        """Test that subdomain hosts are allowed if main domain is in allowed_hosts."""
        app = FastAPI()

        @app.get("/api/test")
        def test_endpoint():
            return PlainTextResponse("ok")

        with (
            patch("core.security.origin_validator.settings") as mock_settings,
            patch(
                "core.security.origin_validator.os.getenv",
                side_effect=lambda k, d=None: "production" if k == "ENV" else d,
            ),
        ):
            mock_settings.cors_origins = []
            mock_settings.supremeai_public_paths = []
            mock_settings.allowed_hosts = ["example.com"]

            app.add_middleware(TrustedOriginMiddleware)
            client = TestClient(app)

            resp = client.get(
                "/api/test",
                headers={
                    "Host": "api.example.com",
                },
            )

        assert resp.status_code == 200

    def test_no_origin_header(self):
        """Test that requests without Origin header pass through."""
        app = FastAPI()

        @app.get("/api/test")
        def test_endpoint():
            return PlainTextResponse("ok")

        with (
            patch("core.security.origin_validator.settings") as mock_settings,
            patch(
                "core.security.origin_validator.os.getenv",
                side_effect=lambda k, d=None: "production" if k == "ENV" else d,
            ),
        ):
            mock_settings.cors_origins = ["https://trusted.example.com"]
            mock_settings.supremeai_public_paths = []
            mock_settings.allowed_hosts = ["example.com"]

            app.add_middleware(TrustedOriginMiddleware)
            client = TestClient(app)

            resp = client.get("/api/test", headers={"Host": "example.com"})

        assert resp.status_code == 200
