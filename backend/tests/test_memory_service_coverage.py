"""
Coverage tests for services/memory_service.py.
Target: 100% line coverage.

মেমোরি সার্ভিস মডিউলের সকল ফাংশন ও শাখা কভার করা হয়েছে।
"""

import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)


class TestMemoryService:
    """Tests for MemoryService."""

    def test_init(self):
        """MemoryService should initialize."""
        from services.memory_service import MemoryService

        with patch("services.memory_service.get_db_session") as mock_session:
            service = MemoryService()
            assert service is not None

    @pytest.mark.asyncio
    async def test_store_memory(self):
        """store should save a memory entry."""
        from services.memory_service import MemoryService

        with (
            patch("services.memory_service.get_db_session") as mock_session,
            patch("services.memory_service.MemoryService._get_session") as mock_get,
        ):
            mock_db = AsyncMock()
            mock_get.return_value.__aenter__.return_value = mock_db
            service = MemoryService()

            result = await service.store("user1", "agent1", "Test memory content", {"type": "test"})
            assert result is not None

    @pytest.mark.asyncio
    async def test_get_memories(self):
        """get_memories should retrieve stored memories."""
        from services.memory_service import MemoryService

        with patch("services.memory_service.get_db_session"):
            service = MemoryService()
            result = await service.get_memories("user1")
            assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_search_memories(self):
        """search_memories should perform semantic search."""
        from services.memory_service import MemoryService

        with patch("services.memory_service.get_db_session"):
            service = MemoryService()
            result = await service.search_memories("user1", "test query")
            assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_delete_memory(self):
        """delete should remove a memory entry."""
        from services.memory_service import MemoryService

        with patch("services.memory_service.get_db_session"):
            service = MemoryService()
            result = await service.delete("memory_id_123")
            assert result is not None

    @pytest.mark.asyncio
    async def test_clear_user_memories(self):
        """clear_user_memories should remove all user memories."""
        from services.memory_service import MemoryService

        with patch("services.memory_service.get_db_session"):
            service = MemoryService()
            result = await service.clear_user_memories("user1")
            assert result is not None


class TestContextWindow:
    """Tests for ContextWindow management."""

    @pytest.mark.asyncio
    async def test_get_context_window(self):
        """get_context_window should return context for a user."""
        from services.memory_service import MemoryService

        with patch("services.memory_service.get_db_session"):
            service = MemoryService()
            result = await service.get_context_window("user1", "agent1", 10)
            assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_update_context_window(self):
        """update_context_window should update sliding window."""
        from services.memory_service import MemoryService

        with patch("services.memory_service.get_db_session"):
            service = MemoryService()
            result = await service.update_context_window("user1", [{"role": "user", "content": "hi"}])
            assert result is not None


class TestSemanticSearch:
    """Tests for semantic search functionality."""

    @pytest.mark.asyncio
    async def test_semantic_search(self):
        """semantic_search should find related memories."""
        from services.memory_service import MemoryService

        with patch("services.memory_service.get_db_session"):
            service = MemoryService()
            result = await service.semantic_search("test query", limit=5)
            assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_get_recent_interactions(self):
        """get_recent_interactions should return recent entries."""
        from services.memory_service import MemoryService

        with patch("services.memory_service.get_db_session"):
            service = MemoryService()
            result = await service.get_recent_interactions("user1", limit=20)
            assert isinstance(result, list)
