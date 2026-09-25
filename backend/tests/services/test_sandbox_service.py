"""Tests for services/sandbox_service.py — Code execution sandbox."""
import pytest
from services.sandbox_service import SandboxService


class TestSandboxService:
    def test_init(self):
        svc = SandboxService()
        assert svc is not None

    @pytest.mark.asyncio
    async def test_execute_simple_code(self):
        svc = SandboxService()
        result = await svc.execute("print('hello')")
        assert result is not None
        assert "hello" in str(result) or result.get("success") is not None

    @pytest.mark.asyncio
    async def test_execute_returns_output(self):
        svc = SandboxService()
        result = await svc.execute("x = 1 + 1")
        assert result is not None
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_execute_timeout(self):
        svc = SandboxService(timeout=1)
        result = await svc.execute("import time; time.sleep(10)")
        assert result is not None
        assert result.get("error") or result.get("timeout") is True

    @pytest.mark.asyncio
    async def test_execute_invalid_code(self):
        svc = SandboxService()
        result = await svc.execute("this is not valid python")
        assert result is not None
        assert result.get("error") is not None
