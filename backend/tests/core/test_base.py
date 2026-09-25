"""Tests for core/base.py — Base classes."""
import pytest
from core.base import BaseConfig, BaseService


class TestBaseConfig:
    """Base config: get, set, validate."""

    def test_config_init(self):
        config = BaseConfig()
        assert config is not None

    def test_config_get(self):
        config = BaseConfig()
        result = config.get("nonexistent_key", "default")
        assert result == "default"

    def test_config_set_and_get(self):
        config = BaseConfig()
        config.set("key", "value")
        assert config.get("key") == "value"


class TestBaseService:
    """Base service: lifecycle."""

    def test_service_init(self):
        svc = BaseService()
        assert svc is not None

    @pytest.mark.asyncio
    async def test_service_start(self):
        svc = BaseService()
        await svc.start()
        assert svc.is_running() is True or svc._started is True

    @pytest.mark.asyncio
    async def test_service_stop(self):
        svc = BaseService()
        await svc.start()
        await svc.stop()
        assert svc.is_running() is False or svc._started is False
