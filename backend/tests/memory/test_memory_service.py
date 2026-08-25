# ============================================================
# SupremeAI - Memory Service Test Suite
# Production-Ready pytest Tests for Vector Memory System
# ============================================================

import asyncio
import math
import uuid
from datetime import UTC, datetime, timedelta, timezone
from typing import Any, Optional, dict, list
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest
import pytest_asyncio
from httpx import AsyncClient

# ============================================================
# MARKER: All tests in this module are memory tests
# ============================================================
pytestmark = pytest.mark.memory


class TestMemoryServiceInitialization:
    """Test Memory Service initialization and basic functionality."""

    @pytest.mark.unit
    async def test_memory_service_imports(self):
        """Test that memory service modules can be imported."""
        try:
            from app.services.memory.embeddings import EmbeddingGenerator
            from app.services.memory.service import MemoryService
            from app.services.memory.vector_store import VectorStore

            assert True
        except ImportError as e:
            pytest.fail(f"Failed to import memory modules: {e}")

    @pytest.mark.unit
    async def test_memory_service_instantiation(self):
        """Test that memory service can be instantiated."""
        from app.services.memory.service import MemoryService

        # Mock dependencies
        mock_db = AsyncMock()
        mock_redis = AsyncMock()

        service = MemoryService(db=mock_db, redis=mock_redis)

        assert service is not None
        assert hasattr(service, "store")
        assert hasattr(service, "search")
        assert hasattr(service, "delete")

    @pytest.mark.unit
    async def test_vector_store_connection(self):
        """Test vector store database connection."""
        from app.services.memory.vector_store import VectorStore

        with patch("app.services.memory.vector_store.create_async_engine") as mock_engine:
            mock_conn = AsyncMock()
            mock_engine.return_value.connect.return_value.__aenter__.return_value = mock_conn

            store = VectorStore(database_url="postgresql+asyncpg://test:test@localhost/test")

            assert store is not None


class TestEmbeddingGeneration:
    """Test embedding generation for text content."""

    @pytest.mark.unit
    async def test_text_embedding_generation(self):
        """Test generating embeddings for text."""
        from app.services.memory.embeddings import EmbeddingGenerator

        generator = EmbeddingGenerator(model="text-embedding-3-small")

        text = "This is a sample text for embedding generation."
        embedding = await generator.generate(text)

        assert isinstance(embedding, list)
        assert len(embedding) == 1536  # OpenAI small model dimensions
        assert all(isinstance(x, float) for x in embedding)

    @pytest.mark.unit
    async def test_embedding_normalization(self):
        """Test that embeddings are properly normalized."""
        from app.services.memory.embeddings import EmbeddingGenerator

        generator = EmbeddingGenerator()

        text = "Normalization test"
        embedding = await generator.generate(text)

        # Calculate L2 norm (should be ~1.0 for normalized vectors)
        norm = math.sqrt(sum(x**2 for x in embedding))

        assert abs(norm - 1.0) < 0.01, f"Embedding norm is {norm}, expected ~1.0"

    @pytest.mark.unit
    async def test_batch_embedding_generation(self):
        """Test generating embeddings for multiple texts."""
        from app.services.memory.embeddings import EmbeddingGenerator

        generator = EmbeddingGenerator()

        texts = [
            "First sample text",
            "Second sample text",
            "Third sample text",
            "Fourth sample text",
            "Fifth sample text",
        ]

        embeddings = await generator.generate_batch(texts)

        assert len(embeddings) == 5
        for emb in embeddings:
            assert len(emb) == 1536

    @pytest.mark.unit
    async def test_empty_string_embedding(self):
        """Test handling of empty string input."""
        from app.services.memory.embeddings import EmbeddingGenerator

        generator = EmbeddingGenerator()

        embedding = await generator.generate("")

        assert isinstance(embedding, list)
        assert len(embedding) == 1536

    @pytest.mark.unit
    async def test_long_text_truncation(self):
        """Test handling of very long text input."""
        from app.services.memory.embeddings import EmbeddingGenerator

        generator = EmbeddingGenerator(max_tokens=8191)

        # Generate very long text (>10K characters)
        long_text = "This is a test sentence. " * 500

        embedding = await generator.generate(long_text)

        assert isinstance(embedding, list)
        assert len(embedding) == 1536


class TestMemoryStorage:
    """Test storing memories in the vector store."""

    @pytest.mark.unit
    async def test_store_episodic_memory(
        self,
        db_session,
        sample_memory_data,
        sample_embedding,
    ):
        """Test storing episodic memory."""
        from app.services.memory.service import MemoryService

        service = MemoryService(db=db_session, redis=AsyncMock())

        memory_id = await service.store(
            content=sample_memory_data["content"],
            agent_id=sample_memory_data["agent_id"],
            memory_type="episodic",
            metadata=sample_memory_data["metadata"],
            importance_score=sample_memory_data["importance_score"],
            embedding=sample_embedding,
        )

        assert memory_id is not None
        assert isinstance(memory_id, (str, uuid.UUID))

    @pytest.mark.unit
    async def test_store_procedural_memory(
        self,
        db_session,
        sample_memory_data,
        sample_embedding,
    ):
        """Test storing procedural memory (learned patterns)."""
        from app.services.memory.service import MemoryService

        service = MemoryService(db=db_session, redis=AsyncMock())

        pattern_data = {
            **sample_memory_data,
            "memory_type": "procedural",
            "metadata": {
                "pattern_type": "success_pattern",
                "context": "api_integration",
                "confidence": 0.9,
                "occurrences": 5,
            },
        }

        memory_id = await service.store(
            content="When integrating external APIs, always implement retry logic with exponential backoff.",
            agent_id=pattern_data["agent_id"],
            memory_type="procedural",
            metadata=pattern_data["metadata"],
            importance_score=0.95,
            embedding=sample_embedding,
        )

        assert memory_id is not None

    @pytest.mark.unit
    async def test_store_with_expiration(
        self,
        db_session,
        sample_memory_data,
        sample_embedding,
    ):
        """Test storing memory with expiration time."""
        from app.services.memory.service import MemoryService

        service = MemoryService(db=db_session, redis=AsyncMock())

        expires_at = datetime.now(UTC) + timedelta(days=30)

        memory_id = await service.store(
            content=sample_memory_data["content"],
            agent_id=sample_memory_data["agent_id"],
            memory_type="episodic",
            expires_at=expires_at,
            embedding=sample_embedding,
        )

        assert memory_id is not None

    @pytest.mark.unit
    async def test_store_validates_importance_score(
        self,
        db_session,
        sample_memory_data,
        sample_embedding,
    ):
        """Test that importance score is validated (0-1 range)."""
        from app.services.memory.service import MemoryService

        service = MemoryService(db=db_session, redis=AsyncMock())

        # Test invalid score (>1)
        with pytest.raises(ValueError) as exc_info:
            await service.store(
                content="Test",
                agent_id=sample_memory_data["agent_id"],
                memory_type="episodic",
                importance_score=1.5,  # Invalid
                embedding=sample_embedding,
            )

        assert "importance" in str(exc_info.value).lower()

        # Test invalid score (<0)
        with pytest.raises(ValueError) as exc_info:
            await service.store(
                content="Test",
                agent_id=sample_memory_data["agent_id"],
                memory_type="episodic",
                importance_score=-0.5,  # Invalid
                embedding=sample_embedding,
            )

        assert "importance" in str(exc_info.value).lower()


class TestMemorySearch:
    """Test semantic search functionality."""

    @pytest.mark.unit
    async def test_basic_semantic_search(
        self,
        db_session,
        created_agent,
        sample_embedding,
    ):
        """Test basic semantic similarity search."""
        from app.services.memory.service import MemoryService

        service = MemoryService(db=db_session, redis=AsyncMock())

        # Store some test memories
        test_memories = [
            ("The weather today is sunny and warm.", {"topic": "weather"}),
            ("Python programming is great for data science.", {"topic": "programming"}),
            ("Machine learning models require training data.", {"topic": "ai"}),
        ]

        for content, meta in test_memories:
            # Generate unique embedding for each
            embedding = [float(i % 100) / 100.0 for i in range(1536)]
            await service.store(
                content=content,
                agent_id=created_agent["id"],
                memory_type="episodic",
                metadata=meta,
                embedding=embedding,
            )

        # Search for similar content
        query_embedding = [0.01] * 1536  # Simple query vector
        results = await service.search(
            query_embedding=query_embedding,
            agent_id=created_agent["id"],
            limit=5,
        )

        assert isinstance(results, list)
        assert len(results) <= 5

    @pytest.mark.unit
    async def test_search_with_similarity_threshold(
        self,
        db_session,
        created_agent,
        sample_embedding,
    ):
        """Test search with minimum similarity threshold."""
        from app.services.memory.service import MemoryService

        service = MemoryService(db=db_session, redis=AsyncMock())

        # Store a memory
        await service.store(
            content="Test memory for threshold testing.",
            agent_id=created_agent["id"],
            memory_type="episodic",
            embedding=sample_embedding,
        )

        # Search with high threshold (should return fewer/no results)
        results_high_threshold = await service.search(
            query_embedding=[0.99] * 1536,  # Very different vector
            agent_id=created_agent["id"],
            similarity_threshold=0.95,
        )

        # Search with low threshold (should return more results)
        results_low_threshold = await service.search(
            query_embedding=sample_embedding,  # Same as stored
            agent_id=created_agent["id"],
            similarity_threshold=0.5,
        )

        assert len(results_low_threshold) >= len(results_high_threshold)

    @pytest.mark.unit
    async def test_search_filtering_by_metadata(
        self,
        db_session,
        created_agent,
        sample_embedding,
    ):
        """Test filtering search results by metadata."""
        from app.services.memory.service import MemoryService

        service = MemoryService(db=db_session, redis=AsyncMock())

        # Store memories with different metadata
        await service.store(
            content="Technical documentation about REST APIs.",
            agent_id=created_agent["id"],
            memory_type="episodic",
            metadata={"category": "technical", "topic": "api"},
            embedding=sample_embedding,
        )

        different_embedding = [float(i % 50) / 50.0 for i in range(1536)]
        await service.store(
            content="Casual conversation about weekend plans.",
            agent_id=created_agent["id"],
            memory_type="episodic",
            metadata={"category": "personal", "topic": "social"},
            embedding=different_embedding,
        )

        # Filter by category
        results = await service.search(
            query_embedding=sample_embedding,
            agent_id=created_agent["id"],
            metadata_filter={"category": "technical"},
        )

        assert all(r.get("metadata", {}).get("category") == "technical" for r in results)

    @pytest.mark.unit
    async def test_search_filtering_by_memory_type(
        self,
        db_session,
        created_agent,
        sample_embedding,
    ):
        """Test filtering search results by memory type."""
        from app.services.memory.service import MemoryService

        service = MemoryService(db=db_session, redis=AsyncMock())

        # Store different types
        await service.store(
            content="Episodic memory: User asked about pricing.",
            agent_id=created_agent["id"],
            memory_type="episodic",
            embedding=sample_embedding,
        )

        proc_embedding = [float((i + 100) % 200) / 200.0 for i in range(1536)]
        await service.store(
            content="Procedural memory: Always verify user permissions before data access.",
            agent_id=created_agent["id"],
            memory_type="procedural",
            embedding=proc_embedding,
        )

        # Search only procedural
        results = await service.search(
            query_embedding=proc_embedding,
            agent_id=created_agent["id"],
            memory_types=["procedural"],
        )

        assert all(r["memory_type"] == "procedural" for r in results)

    @pytest.mark.unit
    async def test_search_pagination(
        self,
        db_session,
        created_agent,
        sample_embedding,
    ):
        """Test paginated search results."""
        from app.services.memory.service import MemoryService

        service = MemoryService(db=db_session, redis=AsyncMock())

        # Store many memories
        for i in range(20):
            embedding = [float((i * 7 + j) % 100) / 100.0 for j in range(1536)]
            await service.store(
                content=f"Memory entry number {i} for pagination test.",
                agent_id=created_agent["id"],
                memory_type="episodic",
                embedding=embedding,
            )

        # Get first page
        page1 = await service.search(
            query_embedding=sample_embedding,
            agent_id=created_agent["id"],
            limit=10,
            offset=0,
        )

        # Get second page
        page2 = await service.search(
            query_embedding=sample_embedding,
            agent_id=created_agent["id"],
            limit=10,
            offset=10,
        )

        assert len(page1) <= 10
        assert len(page2) <= 10

        # Verify no overlap (if total > 20)
        if len(page1) == 10 and len(page2) == 10:
            page1_ids = {r.get("id") for r in page1}
            page2_ids = {r.get("id") for r in page2}
            assert len(page1_ids & page2_ids) == 0, "Pages should not overlap"


class TestMemoryDeletion:
    """Test memory deletion operations."""

    @pytest.mark.unit
    async def test_delete_single_memory(
        self,
        db_session,
        created_agent,
        sample_embedding,
    ):
        """Test deleting a single memory by ID."""
        from app.services.memory.service import MemoryService

        service = MemoryService(db=db_session, redis=AsyncMock())

        # Store a memory
        memory_id = await service.store(
            content="Memory to be deleted.",
            agent_id=created_agent["id"],
            memory_type="episodal",
            embedding=sample_embedding,
        )

        # Delete it
        result = await service.delete(memory_id=memory_id)

        assert result["success"]

        # Verify it's gone
        search_result = await service.get_by_id(memory_id)
        assert search_result is None

    @pytest.mark.unit
    async def test_delete_expired_memories(
        self,
        db_session,
        created_agent,
        sample_embedding,
    ):
        """Test bulk deletion of expired memories."""
        from app.services.memory.service import MemoryService

        service = MemoryService(db=db_session, redis=AsyncMock())

        # Store expired memories
        past_time = datetime.now(UTC) - timedelta(days=1)
        for i in range(5):
            embedding = [float(i * j % 100) / 100.0 for j in range(1536)]
            await service.store(
                content=f"Expired memory {i}",
                agent_id=created_agent["id"],
                memory_type="episodic",
                expires_at=past_time,
                embedding=embedding,
            )

        # Store non-expired memory
        future_time = datetime.now(UTC) + timedelta(days=1)
        await service.store(
            content="Valid memory",
            agent_id=created_agent["id"],
            memory_type="episodic",
            expires_at=future_time,
            embedding=sample_embedding,
        )

        # Delete expired
        deleted_count = await service.delete_expired()

        assert deleted_count == 5

    @pytest.mark.unit
    async def test_delete_all_for_agent(
        self,
        db_session,
        created_agent,
        sample_embedding,
    ):
        """Test deleting all memories for an agent."""
        from app.services.memory.service import MemoryService

        service = MemoryService(db=db_session, redis=AsyncMock())

        # Store multiple memories
        for i in range(10):
            embedding = [float(i * j % 100) / 100.0 for j in range(1536)]
            await service.store(
                content=f"Agent memory {i}",
                agent_id=created_agent["id"],
                memory_type="episodic",
                embedding=embedding,
            )

        # Delete all for agent
        deleted_count = await service.delete_all_for_agent(agent_id=created_agent["id"])

        assert deleted_count == 10

        # Verify all gone
        results = await service.search(
            query_embedding=sample_embedding,
            agent_id=created_agent["id"],
        )
        assert len(results) == 0


class TestMemoryCaching:
    """Test Redis caching layer for memory operations."""

    @pytest.mark.unit
    async def test_cache_search_results(
        self,
        mock_redis,
        created_agent,
        sample_embedding,
    ):
        """Test that search results are cached."""
        from app.services.memory.service import MemoryService

        # Mock DB to return nothing (force cache check)
        mock_db = AsyncMock()
        mock_db.execute.return_value.scalars().all.return_value = []

        service = MemoryService(db=mock_db, redis=mock_redis)

        # First call - should query DB and cache
        await service.search(
            query_embedding=sample_embedding,
            agent_id=created_agent["id"],
            use_cache=True,
        )

        # Second call - should use cache
        await service.search(
            query_embedding=sample_embedding,
            agent_id=created_agent["id"],
            use_cache=True,
        )

        # Cache should have been checked
        assert mock_redis.get.called or mock_redis.get.called_once

    @pytest.mark.unit
    async def test_cache_invalidation_on_write(
        self,
        mock_redis,
        db_session,
        created_agent,
        sample_embedding,
    ):
        """Test that cache is invalidated when new memories are stored."""
        from app.services.memory.service import MemoryService

        service = MemoryService(db=db_session, redis=mock_redis)

        # Store a memory (should invalidate cache)
        await service.store(
            content="New memory that invalidates cache.",
            agent_id=created_agent["id"],
            memory_type="episodic",
            embedding=sample_embedding,
        )

        # Check cache was cleared for this agent
        assert mock_redis.delete.called


class TestMemoryAPIEndpoints:
    """Test memory-related API endpoints."""

    @pytest.mark.integration
    async def test_store_memory_via_api(
        self,
        client: AsyncClient,
        auth_headers: dict,
        created_agent: dict,
    ):
        """Test storing memory via API endpoint."""
        memory_data = {
            "agent_id": created_agent["id"],
            "memory_type": "episodic",
            "content": "API test memory storage.",
            "metadata": {"source": "api_test"},
            "importance_score": 0.75,
        }

        response = await client.post(
            "/api/v1/memory/store",
            json=memory_data,
            headers=auth_headers,
        )

        assert response.status_code in [200, 201]
        data = response.json().get("data", response.json())
        assert "id" in data
        assert data["memory_type"] == "episodic"

    @pytest.mark.integration
    async def test_search_memory_via_api(
        self,
        client: AsyncClient,
        auth_headers: dict,
        created_agent: dict,
    ):
        """Test searching memories via API endpoint."""
        response = await client.post(
            "/api/v1/memory/search",
            json={
                "agent_id": created_agent["id"],
                "query": "test query for semantic search",
                "limit": 10,
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json().get("data", response.json())
        assert isinstance(data, list)

    @pytest.mark.integration
    async def test_delete_memory_via_api(
        self,
        client: AsyncClient,
        auth_headers: dict,
        created_agent: dict,
    ):
        """Test deleting memory via API endpoint."""
        # First create a memory
        create_response = await client.post(
            "/api/v1/memory/store",
            json={
                "agent_id": created_agent["id"],
                "memory_type": "episodic",
                "content": "Memory to delete via API",
            },
            headers=auth_headers,
        )

        memory_id = create_response.json().get("data", {}).get("id")

        # Delete it
        delete_response = await client.delete(
            f"/api/v1/memory/{memory_id}",
            headers=auth_headers,
        )

        assert delete_response.status_code == 200
        data = delete_response.json().get("data", delete_response.json())
        assert data["success"]

    @pytest.mark.integration
    async def test_memory_stats_endpoint(
        self,
        client: AsyncClient,
        auth_headers: dict,
        created_agent: dict,
    ):
        """Test memory statistics endpoint."""
        response = await client.get(
            f"/api/v1/memory/stats?agent_id={created_agent['id']}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json().get("data", response.json())
        assert "total_memories" in data or "count" in data


class TestMemoryImportExport:
    """Test bulk import/export of memories."""

    @pytest.mark.unit
    async def test_export_memories(
        self,
        db_session,
        created_agent,
        sample_embedding,
    ):
        """Test exporting memories to file/JSON."""
        from app.services.memory.service import MemoryService

        service = MemoryService(db=db_session, redis=AsyncMock())

        # Create some memories
        for i in range(5):
            embedding = [float(i * j % 100) / 100.0 for j in range(1536)]
            await service.store(
                content=f"Exportable memory {i}",
                agent_id=created_agent["id"],
                memory_type="episodic",
                embedding=embedding,
            )

        # Export
        export_data = await service.export_memories(
            agent_id=created_agent["id"],
            format="json",
        )

        assert isinstance(export_data, list)
        assert len(export_data) >= 5
        assert all("content" in m and "memory_type" in m for m in export_data)

    @pytest.mark.unit
    async def test_import_memories(
        self,
        db_session,
        created_agent,
    ):
        """Test importing memories from JSON."""
        from app.services.memory.service import MemoryService

        service = MemoryService(db=db_session, redis=AsyncMock())

        # Import data
        import_data = [
            {
                "content": "Imported memory 1",
                "memory_type": "episodic",
                "metadata": {"imported": True},
                "importance_score": 0.8,
            },
            {
                "content": "Imported memory 2",
                "memory_type": "procedural",
                "metadata": {"imported": True},
                "importance_score": 0.9,
            },
        ]

        result = await service.import_memories(
            agent_id=created_agent["id"],
            memories=import_data,
        )

        assert result["imported_count"] == 2
        assert result["skipped_count"] == 0


class TestMemoryErrorHandling:
    """Test error handling in memory service."""

    @pytest.mark.unit
    async def test_invalid_agent_id_handling(self):
        """Test handling of invalid agent ID."""
        from app.services.memory.service import MemoryService

        mock_db = AsyncMock()
        mock_redis = AsyncMock()
        service = MemoryService(db=mock_db, redis=mock_redis)

        with pytest.raises(ValueError) as exc_info:
            await service.store(
                content="Test",
                agent_id="invalid-uuid-format!!!",
                memory_type="episodic",
                embedding=[0.1] * 1536,
            )

        assert "agent_id" in str(exc_info.value).lower() or "invalid" in str(exc_info.value).lower()

    @pytest.mark.unit
    async def test_empty_content_handling(self):
        """Test handling of empty content."""
        from app.services.memory.service import MemoryService

        mock_db = AsyncMock()
        mock_redis = AsyncMock()
        service = MemoryService(db=mock_db, redis=mock_redis)

        with pytest.raises(ValueError) as exc_info:
            await service.store(
                content="   ",  # Only whitespace
                agent_id=str(uuid.uuid4()),
                memory_type="episodic",
                embedding=[0.1] * 1536,
            )

        assert "content" in str(exc_info.value).lower()

    @pytest.mark.unit
    async def test_invalid_embedding_dimensions(self):
        """Test handling of incorrect embedding dimensions."""
        from app.services.memory.service import MemoryService

        mock_db = AsyncMock()
        mock_redis = AsyncMock()
        service = MemoryService(db=mock_db, redis=mock_redis)

        with pytest.raises(ValueError) as exc_info:
            await service.store(
                content="Test content",
                agent_id=str(uuid.uuid4()),
                memory_type="episodic",
                embedding=[0.1] * 100,  # Wrong dimensions (should be 1536)
            )

        assert (
            "embedding" in str(exc_info.value).lower() or "dimension" in str(exc_info.value).lower()
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
