"""Tests for services/render_account_service.py — Render account management."""
import pytest
from unittest.mock import patch, MagicMock
from services.render_account_service import RenderAccountService


class TestRenderAccountService:
    def test_init(self):
        svc = RenderAccountService()
        assert svc is not None

    @pytest.mark.asyncio
    async def test_list_services(self):
        svc = RenderAccountService()
        with patch.object(svc, '_api_call', return_value=[{"id": "srv-1", "name": "core"}]):
            services = await svc.list_services()
            assert isinstance(services, list)

    @pytest.mark.asyncio
    async def test_deploy_service(self):
        svc = RenderAccountService()
        with patch.object(svc, '_api_call', return_value={"id": "dep-1", "status": "created"}):
            result = await svc.deploy("srv-1", clear_cache=True)
            assert result is not None

    @pytest.mark.asyncio
    async def test_get_service_status(self):
        svc = RenderAccountService()
        with patch.object(svc, '_api_call', return_value={"status": "live"}):
            status = await svc.get_status("srv-1")
            assert status is not None

    def test_rotate_account(self):
        svc = RenderAccountService()
        result = svc.rotate_account()
        assert result is not None
