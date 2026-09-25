"""Tests for services/memory_service.py — Memory service (CascadeMemoryService)."""
import pytest
from services.memory_service import CascadeMemoryService


class TestCascadeMemoryService:
    def test_init(self):
        svc = CascadeMemoryService()
        assert svc is not None

    @pytest.mark.asyncio
    async def test_store_memory(self):
        svc = CascadeMemoryService()
        result = await svc.store("user-1", {"content": "test memory", "type": "fact"})
        assert result is not None

    @pytest.mark.asyncio
    async def test_retrieve_memory(self):
        svc = CascadeMemoryService()
        await svc.store("user-1", {"content": "hello", "type": "fact"})
        results = await svc.retrieve("user-1", "hello")
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_retrieve_empty(self):
        svc = CascadeMemoryService()
        results = await svc.retrieve("user-nonexistent", "nothing")
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_consolidate(self):
        svc = CascadeMemoryService()
        result = await svc.consolidate("user-1")
        assert result is not None
