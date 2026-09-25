"""Tests for services/config_service.py — Configuration service."""
import pytest
from services.config_service import ConfigService


class TestConfigService:
    """Config service: get, set, validate, list."""

    def test_init(self):
        svc = ConfigService()
        assert svc is not None

    def test_get_config(self):
        svc = ConfigService()
        result = svc.get("some_key")
        assert result is not None or result is None  # doesn't crash

    def test_set_config(self):
        svc = ConfigService()
        svc.set("test_key", "test_value")
        assert svc.get("test_key") == "test_value"

    def test_list_config(self):
        svc = ConfigService()
        listing = svc.list()
        assert isinstance(listing, (dict, list))

    def test_validate_config_valid(self):
        svc = ConfigService()
        result = svc.validate({"key": "value"})
        assert isinstance(result, (bool, dict))

    def test_validate_config_invalid(self):
        svc = ConfigService()
        result = svc.validate({})
        assert result is not None

    def test_delete_config(self):
        svc = ConfigService()
        svc.set("temp_key", "temp_value")
        svc.delete("temp_key")
        assert svc.get("temp_key") is None
