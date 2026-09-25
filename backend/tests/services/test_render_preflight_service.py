"""Tests for services/render_preflight_service.py — Render pre-flight checks."""
import pytest
from services.render_preflight_service import RenderPreflightService


class TestRenderPreflightService:
    def test_init(self):
        svc = RenderPreflightService()
        assert svc is not None

    @pytest.mark.asyncio
    async def test_run_preflight(self):
        svc = RenderPreflightService()
        result = await svc.run_checks()
        assert result is not None
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_check_env_vars(self):
        svc = RenderPreflightService()
        result = await svc.check_env_vars()
        assert result is not None

    @pytest.mark.asyncio
    async def test_check_health_endpoints(self):
        svc = RenderPreflightService()
        result = await svc.check_health()
        assert result is not None
