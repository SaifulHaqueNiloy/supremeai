"""Tests for tools/api_gateway.py — API gateway tool."""
import pytest
from tools.api_gateway import ApiGateway


class TestApiGateway:
    def test_init(self):
        gw = ApiGateway()
        assert gw is not None

    @pytest.mark.asyncio
    async def test_call_external_api(self):
        gw = ApiGateway()
        result = await gw.call("GET", "https://httpbin.org/get")
        assert result is not None

    @pytest.mark.asyncio
    async def test_call_with_invalid_url(self):
        gw = ApiGateway()
        result = await gw.call("GET", "not-a-url")
        assert result is not None
        assert "error" in result or result.get("success") is False

    def test_n8n_enabled_flag(self):
        gw = ApiGateway()
        result = gw.is_n8n_enabled()
        assert isinstance(result, bool)
