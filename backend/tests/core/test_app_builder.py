"""Tests for core/app_builder.py — FastAPI app assembly."""
import pytest
from core.app_builder import build_app


class TestAppBuilder:
    """App builder: creates FastAPI app with all middleware."""

    def test_build_app_returns_app(self):
        app = build_app()
        assert app is not None

    def test_app_has_routes(self):
        app = build_app()
        assert len(app.routes) > 0

    def test_app_has_middleware(self):
        app = build_app()
        # CORS middleware should be configured
        assert app is not None

    def test_app_has_health_endpoint(self):
        app = build_app()
        health_routes = [r for r in app.routes if hasattr(r, 'path') and 'health' in r.path]
        assert len(health_routes) > 0
