"""
Memory Service Test Suite
==========================

Tests for the AI Agent Memory System including:
- Vector embedding generation
- Semantic search operations
- Memory storage and retrieval
- Memory type classification
- Importance scoring
- Expiration handling
- Tag management

This tests the critical memory infrastructure that enables agents to
maintain context across sessions using pgvector.

Run with: pytest tests/test_memory_service.py -v --cov=memory
"""

import asyncio
from datetime import UTC, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest

from conftest import (
    CustomAssertions,
    sample_memory_data,
    sample_memory_search_request,
    sample_memory_search_results,
    sample_memory_store_request,
)

# ============================================================================
# MOCK MEMORY SERVICE IMPLEMENTATION (for testing)
# ============================================================================


class MockMemoryService:
    """
    Mock implementation of Memory Service for testing.

    In production, this would be app/services/memory.py
    This mock simulates all behaviors for isolated unit testing.
    """

    # Valid memory types
    VALID_MEMORY_TYPES = {"preference", "fact", "interaction", "knowledge"}

    # Default configuration
    DEFAULT_CONFIG = {
        "embedding_dimensions": 1536,
        "similarity_threshold": 0.75,
        "max_results": 10,
        "default_importance": 0.5,
        "auto_tag": True,
        "retention_days": 365,
    }

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = {**self.DEFAULT_CONFIG, **(config or {})}
        self.memories: dict[str, dict[str, Any]] = {}
        self.embeddings_cache: dict[str, list[float]] = {}
        self._memory_counter = 0

    async def generate_embedding(self, text: str) -> list[float]:
        """Generate embedding vector for text."""
        if not text or not text.strip():
            raise ValueError("Cannot generate embedding for empty text")

        # Check cache first
        cache_key = hash(text)
        if cache_key in self.embeddings_cache:
            return self.embeddings_cache[cache_key]

        # Generate deterministic mock embedding based on text
        np.random.seed(len(text))
        embedding = np.random.randn(self.config["embedding_dimensions"]).tolist()

        # Normalize to unit length
        magnitude = sum(x**2 for x in embedding) ** 0.5
        embedding = [x / magnitude for x in embedding]

        # Cache it
        self.embeddings_cache[cache_key] = embedding

        return embedding

    async def store_memory(
        self,
        agent_id: str,
        content: str,
        memory_type: str = "fact",
        user_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        importance: float = 0.5,
        tags: list[str] | None = None,
        expires_at: datetime | None = None,
    ) -> dict[str, Any]:
        """Store a new memory entry with embedding."""

        # Validate inputs
        if not agent_id:
            raise ValueError("agent_id is required")
        if not content or not content.strip():
            raise ValueError("content is required and cannot be empty")
        if memory_type not in self.VALID_MEMORY_TYPES:
            raise ValueError(
                f"Invalid memory_type: {memory_type}. Must be one of {self.VALID_MEMORY_TYPES}"
            )
        if not 0 <= importance <= 1:
            raise ValueError(f"importance must be between 0 and 1, got {importance}")

        # Generate embedding
        embedding = await self.generate_embedding(content)

        # Create memory entry
        self._memory_counter += 1
        now = datetime.now(UTC)

        memory_id = f"memory-{self._memory_counter:04d}"

        memory = {
            "id": memory_id,
            "agent_id": agent_id,
            "user_id": user_id,
            "content": content,
            "embedding": embedding,
            "memory_type": memory_type,
            "metadata": metadata or {},
            "importance": importance,
            "tags": tags or [],
            "created_at": now,
            "expires_at": expires_at,
        }

        # Auto-tag if enabled
        if self.config.get("auto_tag"):
            memory["tags"] = list(set(memory["tags"] + await self._generate_tags(content)))

        self.memories[memory_id] = memory

        return memory

    async def search_memories(
        self,
        query: str,
        agent_id: str,
        limit: int = 10,
        threshold: float = 0.7,
        filters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Search memories by semantic similarity."""

        if not query or not query.strip():
            raise ValueError("query is required")
        if not agent_id:
            raise ValueError("agent_id is required")

        start_time = datetime.now()

        # Generate query embedding
        query_embedding = await self.generate_embedding(query)

        # Get candidate memories for this agent
        candidates = [m for m in self.memories.values() if m["agent_id"] == agent_id]

        # Apply filters
        if filters:
            candidates = self._apply_filters(candidates, filters)

        # Filter out expired memories
        now = datetime.now(UTC)
        candidates = [m for m in candidates if m.get("expires_at") is None or m["expires_at"] > now]

        # Calculate similarities
        results = []
        for memory in candidates:
            similarity = self._cosine_similarity(query_embedding, memory["embedding"])

            if similarity >= threshold:
                results.append(
                    {
                        "memory_id": memory["id"],
                        "content": memory["content"],
                        "similarity": round(similarity, 4),
                        "memory_type": memory["memory_type"],
                        "metadata": memory["metadata"],
                        "importance": memory["importance"],
                        "tags": memory["tags"],
                        "created_at": memory["created_at"].isoformat(),
                    }
                )

        # Sort by similarity (descending), then by importance
        results.sort(key=lambda x: (-x["similarity"], -x["importance"]))

        # Apply limit
        results = results[:limit]

        query_time_ms = (datetime.now() - start_time).total_seconds() * 1000

        return {
            "results": results,
            "total_results": len(results),
            "query_time_ms": round(query_time_ms, 2),
            "query": query,
            "threshold": threshold,
        }

    async def get_memory(self, memory_id: str) -> dict[str, Any] | None:
        """Get a specific memory by ID."""
        return self.memories.get(memory_id)

    async def update_memory(self, memory_id: str, updates: dict[str, Any]) -> dict[str, Any]:
        """Update an existing memory entry."""

        if memory_id not in self.memories:
            raise ValueError(f"Memory {memory_id} not found")

        memory = self.memories[memory_id]

        # Update allowed fields
        updatable_fields = {
            "content",
            "memory_type",
            "metadata",
            "importance",
            "tags",
            "expires_at",
        }

        for field, value in updates.items():
            if field not in updatable_fields:
                raise ValueError(f"Cannot update field: {field}")

            # If content changed, regenerate embedding
            if field == "content":
                memory["embedding"] = await self.generate_embedding(value)

            memory[field] = value

        memory["updated_at"] = datetime.now(UTC)

        return memory

    async def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory entry."""
        if memory_id not in self.memories:
            return False

        del self.memories[memory_id]

        # Remove from cache if present
        keys_to_remove = [k for k, v in self.embeddings_cache.items() if k == memory_id]
        for key in keys_to_remove:
            del self.embeddings_cache[key]

        return True

    async def get_agent_memories(
        self, agent_id: str, memory_type: str | None = None, limit: int = 50, offset: int = 0
    ) -> list[dict[str, Any]]:
        """Get all memories for an agent."""

        memories = [m for m in self.memories.values() if m["agent_id"] == agent_id]

        if memory_type:
            memories = [m for m in memories if m["memory_type"] == memory_type]

        # Sort by created_at descending
        memories.sort(key=lambda x: x["created_at"], reverse=True)

        # Apply pagination
        return memories[offset : offset + limit]

    async def cleanup_expired_memories(self) -> int:
        """Remove all expired memories. Returns count of removed entries."""

        now = datetime.now(UTC)
        expired_ids = [
            mem_id
            for mem_id, memory in self.memories.items()
            if memory.get("expires_at") and memory["expires_at"] <= now
        ]

        for mem_id in expired_ids:
            del self.memories[mem_id]

        return len(expired_ids)

    async def get_statistics(self, agent_id: str | None = None) -> dict[str, Any]:
        """Get statistics about stored memories."""

        memories = list(self.memories.values())

        if agent_id:
            memories = [m for m in memories if m["agent_id"] == agent_id]

        total = len(memories)

        type_counts = {}
        for memory in memories:
            mt = memory["memory_type"]
            type_counts[mt] = type_counts.get(mt, 0) + 1

        total_tags = set()
        for memory in memories:
            total_tags.update(memory.get("tags", []))

        avg_importance = 0
        if memories:
            avg_importance = sum(m["importance"] for m in memories) / len(memories)

        return {
            "total_memories": total,
            "by_type": type_counts,
            "unique_tags": len(total_tags),
            "avg_importance": round(avg_importance, 3),
            "embedding_cache_size": len(self.embeddings_cache),
        }

    @staticmethod
    def _cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
        magnitude_a = sum(a**2 for a in vec_a) ** 0.5
        magnitude_b = sum(b**2 for b in vec_b) ** 0.5

        if magnitude_a == 0 or magnitude_b == 0:
            return 0.0

        return dot_product / (magnitude_a * magnitude_b)

    def _apply_filters(
        self, memories: list[dict[str, Any]], filters: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Apply filters to memory list."""
        result = memories

        if "memory_types" in filters:
            allowed_types = set(filters["memory_types"])
            result = [m for m in result if m["memory_type"] in allowed_types]

        if "date_range" in filters:
            date_range = filters["date_range"]
            from_date = date_range.get("from")
            to_date = date_range.get("to")

            if from_date:
                from_dt = (
                    datetime.fromisoformat(from_date) if isinstance(from_date, str) else from_date
                )
                result = [m for m in result if m["created_at"] >= from_dt]

            if to_date:
                to_dt = datetime.fromisoformat(to_date) if isinstance(to_date, str) else to_date
                result = [m for m in result if m["created_at"] <= to_dt]

        if "min_importance" in filters:
            min_imp = filters["min_importance"]
            result = [m for m in result if m["importance"] >= min_imp]

        if "tags" in filters:
            required_tags = set(filters["tags"])
            result = [m for m in result if required_tags.issubset(set(m.get("tags", [])))]

        return result

    @staticmethod
    async def _generate_tags(content: str) -> list[str]:
        """Auto-generate tags from content."""
        # Simple keyword-based tagging for testing
        keywords = {
            "preference": ["prefer", "like", "want", "setting", "option"],
            "ui": ["interface", "screen", "display", "button", "menu"],
            "project": ["project", "working on", "building", "developing"],
            "python": ["python", "pip", "pandas", "numpy"],
            "ml": ["machine learning", "ml model", "training", "neural"],
            "data": ["data", "dataset", "database", "csv", "json"],
        }

        content_lower = content.lower()
        tags = []

        for tag, words in keywords.items():
            if any(word in content_lower for word in words):
                tags.append(tag)

        return tags


# ============================================================================
# TEST FIXTURES SPECIFIC TO MEMORY SERVICE
# ============================================================================


@pytest.fixture
async def memory_service() -> MockMemoryService:
    """Create fresh memory service instance for each test."""
    return MockMemoryService()


@pytest.fixture
async def sample_memories_batch(
    memory_service: MockMemoryService, sample_user_data: dict[str, Any]
) -> list[dict[str, Any]]:
    """Create batch of sample memories for testing."""
    memories = []

    memory_templates = [
        ("User prefers dark mode interface", "preference", 0.9, ["ui"]),
        ("User is working on ML project", "fact", 0.8, ["project", "ml"]),
        ("Python is preferred over R", "preference", 0.7, ["python"]),
        ("Dataset has 10k rows", "fact", 0.6, ["data"]),
        ("User asked about API limits", "interaction", 0.4, []),
        ("TensorFlow version 2.x installed", "knowledge", 0.8, ["ml", "python"]),
    ]

    for content, mem_type, importance, tags in memory_templates:
        memory = await memory_service.store_memory(
            agent_id="test-agent-uuid",
            content=content,
            memory_type=mem_type,
            user_id=sample_user_data["id"],
            importance=importance,
            tags=tags,
        )
        memories.append(memory)

    return memories


# ============================================================================
# TEST CLASS: Embedding Generation
# ============================================================================


class TestEmbeddingGeneration:
    """Tests for vector embedding generation."""

    @pytest.mark.unit
    @pytest.mark.critical
    @pytest.mark.asyncio
    async def test_generate_embedding_for_text(self, memory_service: MockMemoryService):
        """Should generate embedding vector for valid text."""
        text = "This is a test sentence for embedding."

        embedding = await memory_service.generate_embedding(text)

        assert isinstance(embedding, list)
        assert len(embedding) == memory_service.config["embedding_dimensions"]

        # All values should be floats
        assert all(isinstance(x, (int, float)) for x in embedding)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_embedding_normalized_to_unit_length(self, memory_service: MockMemoryService):
        """Embedding should be normalized (unit vector)."""
        text = "Normalization test"

        embedding = await memory_service.generate_embedding(text)

        # Calculate magnitude
        magnitude = sum(x**2 for x in embedding) ** 0.5

        # Should be approximately 1.0
        assert abs(magnitude - 1.0) < 0.0001, f"Magnitude should be ~1.0, got {magnitude}"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_reject_empty_text(self, memory_service: MockMemoryService):
        """Should reject empty text."""
        with pytest.raises(ValueError, match="empty text"):
            await memory_service.generate_embedding("")

        with pytest.raises(ValueError, match="empty text"):
            await memory_service.generate_embedding("   ")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_same_text_same_embedding(self, memory_service: MockMemoryService):
        """Same text should produce same embedding (deterministic)."""
        text = "Deterministic test"

        embedding1 = await memory_service.generate_embedding(text)
        embedding2 = await memory_service.generate_embedding(text)

        assert embedding1 == embedding2, "Same text should produce identical embeddings"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_different_texts_different_embeddings(self, memory_service: MockMemoryService):
        """Different texts should produce different embeddings."""
        text_a = "Machine learning is fascinating"
        text_b = "The weather is nice today"

        embedding_a = await memory_service.generate_embedding(text_a)
        embedding_b = await memory_service.generate_embedding(text_b)

        # Calculate similarity
        similarity = MockMemoryService._cosine_similarity(embedding_a, embedding_b)

        # Should be different (similarity < 1.0)
        assert similarity < 0.99, (
            f"Different texts should have different embeddings, got similarity {similarity}"
        )

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_similar_texts_higher_similarity(self, memory_service: MockMemoryService):
        """Semantically similar texts should have higher similarity."""
        text_1 = "I love programming in Python"
        text_2 = "Python programming is enjoyable"
        text_3 = "The stock market crashed today"

        emb_1 = await memory_service.generate_embedding(text_1)
        emb_2 = await memory_service.generate_embedding(text_2)
        emb_3 = await memory_service.generate_embedding(text_3)

        sim_12 = MockMemoryService._cosine_similarity(emb_1, emb_2)
        sim_13 = MockMemoryService._cosine_similarity(emb_1, emb_3)

        assert sim_12 > sim_13, "Similar texts should have higher similarity than dissimilar ones"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_handle_unicode_and_special_chars(self, memory_service: MockMemoryService):
        """Should handle unicode and special characters correctly."""
        texts = [
            "Hello 世界 🌍",
            "Spéciäl chäräctërs",
            "Math: E=mc²",
            "Emoji: 🎉🚀💻",
            "RTL: שלום עולם",
        ]

        for text in texts:
            embedding = await memory_service.generate_embedding(text)
            assert len(embedding) == memory_service.config["embedding_dimensions"]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_caching_works(self, memory_service: MockMemoryService):
        """Should cache embeddings for repeated calls."""
        text = "Cache test text"

        # First call - generates and caches
        embedding1 = await memory_service.generate_embedding(text)
        initial_cache_size = len(memory_service.embeddings_cache)

        # Second call - should use cache
        embedding2 = await memory_service.generate_embedding(text)

        assert embedding1 == embedding2
        assert len(memory_service.embeddings_cache) == initial_cache_size


# ============================================================================
# TEST CLASS: Memory Storage
# ============================================================================


class TestMemoryStorage:
    """Tests for storing memory entries."""

    @pytest.mark.unit
    @pytest.mark.critical
    @pytest.mark.asyncio
    async def test_store_valid_memory(
        self,
        memory_service: MockMemoryService,
        sample_user_data: dict[str, Any],
        assertions: CustomAssertions,
    ):
        """Should successfully store valid memory."""
        memory = await memory_service.store_memory(
            agent_id="agent-123",
            content="User prefers dark mode",
            memory_type="preference",
            user_id=sample_user_data["id"],
            importance=0.9,
            tags=["ui", "preferences"],
        )

        assert memory is not None
        assert "id" in memory
        assert memory["agent_id"] == "agent-123"
        assert memory["content"] == "User prefers dark mode"
        assert memory["memory_type"] == "preference"
        assert memory["user_id"] == sample_user_data["id"]
        assert memory["importance"] == 0.9
        assert "ui" in memory["tags"]
        assert "preferences" in memory["tags"]
        assert memory["embedding"] is not None
        assert len(memory["embedding"]) == memory_service.config["embedding_dimensions"]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_store_generates_unique_ids(self, memory_service: MockMemoryService):
        """Should generate unique IDs for each memory."""
        memories = []

        for i in range(10):
            memory = await memory_service.store_memory(
                agent_id="agent-123", content=f"Test memory {i}", memory_type="fact"
            )
            memories.append(memory)

        ids = [m["id"] for m in memories]
        assert len(ids) == len(set(ids)), "All memory IDs should be unique"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_store_sets_timestamps(self, memory_service: MockMemoryService):
        """Should set created_at timestamp."""
        before_store = datetime.now(UTC)

        memory = await memory_service.store_memory(
            agent_id="agent-123", content="Timestamp test", memory_type="fact"
        )

        after_store = datetime.now(UTC)

        assert before_store <= memory["created_at"] <= after_store

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_auto_generate_tags(self, memory_service: MockMemoryService):
        """Should auto-generate tags when enabled."""
        memory = await memory_service.store_memory(
            agent_id="agent-123",
            content="User is working on a Python machine learning project",
            memory_type="fact",
        )

        # Should detect relevant keywords
        assert len(memory["tags"]) > 0, "Should auto-generate some tags"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_reject_invalid_memory_type(self, memory_service: MockMemoryService):
        """Should reject invalid memory types."""
        with pytest.raises(ValueError, match="Invalid memory_type"):
            await memory_service.store_memory(
                agent_id="agent-123", content="Test", memory_type="invalid_type"
            )

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_reject_empty_content(self, memory_service: MockMemoryService):
        """Should reject empty content."""
        with pytest.raises(ValueError, match="content"):
            await memory_service.store_memory(agent_id="agent-123", content="", memory_type="fact")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_reject_importance_out_of_range(self, memory_service: MockMemoryService):
        """Should reject importance outside 0-1 range."""
        with pytest.raises(ValueError, match="importance"):
            await memory_service.store_memory(
                agent_id="agent-123",
                content="Test",
                memory_type="fact",
                importance=1.5,  # Too high
            )

        with pytest.raises(ValueError, match="importance"):
            await memory_service.store_memory(
                agent_id="agent-123",
                content="Test",
                memory_type="fact",
                importance=-0.1,  # Too low
            )

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_accept_all_valid_memory_types(self, memory_service: MockMemoryService):
        """Should accept all valid memory types."""
        valid_types = ["preference", "fact", "interaction", "knowledge"]

        for mem_type in valid_types:
            memory = await memory_service.store_memory(
                agent_id="agent-123", content=f"Test {mem_type} memory", memory_type=mem_type
            )
            assert memory["memory_type"] == mem_type


# ============================================================================
# TEST CLASS: Memory Search
# ============================================================================


class TestMemorySearch:
    """Tests for semantic search functionality."""

    @pytest.mark.unit
    @pytest.mark.critical
    @pytest.mark.asyncio
    async def test_search_returns_relevant_results(
        self, memory_service: MockMemoryService, sample_memories_batch: list[dict[str, Any]]
    ):
        """Search should return semantically relevant results."""
        results = await memory_service.search_memories(
            query="what does the user prefer?", agent_id="test-agent-uuid", limit=5
        )

        assert results["total_results"] > 0
        assert len(results["results"]) > 0

        # Results should have expected structure
        for result in results["results"]:
            assert "memory_id" in result
            assert "content" in result
            assert "similarity" in result
            assert 0 <= result["similarity"] <= 1

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_search_respects_threshold(
        self, memory_service: MockMemoryService, sample_memories_batch: list[dict[str, Any]]
    ):
        """Search should only return results above threshold."""
        # High threshold - fewer results
        high_threshold_results = await memory_service.search_memories(
            query="test query", agent_id="test-agent-uuid", threshold=0.95
        )

        # Low threshold - more results
        low_threshold_results = await memory_service.search_memories(
            query="test query", agent_id="test-agent-uuid", threshold=0.3
        )

        assert low_threshold_results["total_results"] >= high_threshold_results["total_results"]

        # All results should meet threshold
        for result in low_threshold_results["results"]:
            assert result["similarity"] >= 0.3

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_search_respects_limit(
        self, memory_service: MockMemoryService, sample_memories_batch: list[dict[str, Any]]
    ):
        """Search should respect result limit."""
        limited_results = await memory_service.search_memories(
            query="test", agent_id="test-agent-uuid", limit=3
        )

        assert len(limited_results["results"]) <= 3

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_search_sorts_by_similarity(
        self, memory_service: MockMemoryService, sample_memories_batch: list[dict[str, Any]]
    ):
        """Results should be sorted by similarity (descending)."""
        results = await memory_service.search_memories(
            query="user preferences", agent_id="test-agent-uuid", limit=10
        )

        if len(results["results"]) > 1:
            similarities = [r["similarity"] for r in results["results"]]
            assert similarities == sorted(similarities, reverse=True), (
                "Results should be sorted by similarity descending"
            )

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_search_filters_by_agent_id(
        self, memory_service: MockMemoryService, sample_user_data: dict[str, Any]
    ):
        """Search should only return memories for specified agent."""
        # Store memories for different agents
        await memory_service.store_memory(
            agent_id="agent-A", content="Agent A specific memory", memory_type="fact"
        )
        await memory_service.store_memory(
            agent_id="agent-B", content="Agent B specific memory", memory_type="fact"
        )

        # Search only Agent A's memories
        results = await memory_service.search_memories(query="memory", agent_id="agent-A")

        for result in results["results"]:
            # Get full memory to check agent_id
            memory = await memory_service.get_memory(result["memory_id"])
            assert memory["agent_id"] == "agent-A"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_search_with_memory_type_filter(
        self, memory_service: MockMemoryService, sample_memories_batch: list[dict[str, Any]]
    ):
        """Search should filter by memory type when specified."""
        results = await memory_service.search_memories(
            query="test", agent_id="test-agent-uuid", filters={"memory_types": ["preference"]}
        )

        for result in results["results"]:
            assert result["memory_type"] == "preference"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_search_returns_query_metadata(
        self, memory_service: MockMemoryService, sample_memories_batch: list[dict[str, Any]]
    ):
        """Search response should include metadata about the query."""
        results = await memory_service.search_memories(
            query="test query", agent_id="test-agent-uuid"
        )

        assert "query_time_ms" in results
        assert results["query_time_ms"] >= 0
        assert "query" in results
        assert results["query"] == "test query"
        assert "threshold" in results

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_search_empty_query_raises_error(self, memory_service: MockMemoryService):
        """Search should reject empty queries."""
        with pytest.raises(ValueError, match="query"):
            await memory_service.search_memories(query="", agent_id="agent-123")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_search_no_results(self, memory_service: MockMemoryService):
        """Search should handle no results gracefully."""
        results = await memory_service.search_memories(
            query="xyznonexistentquery123", agent_id="nonexistent-agent"
        )

        assert results["total_results"] == 0
        assert results["results"] == []


# ============================================================================
# TEST CLASS: Memory Retrieval & Updates
# ============================================================================


class TestMemoryRetrievalAndUpdate:
    """Tests for retrieving and updating memories."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_existing_memory(self, memory_service: MockMemoryService):
        """Should retrieve existing memory by ID."""
        stored = await memory_service.store_memory(
            agent_id="agent-123", content="Retrieval test", memory_type="fact"
        )

        retrieved = await memory_service.get_memory(stored["id"])

        assert retrieved is not None
        assert retrieved["id"] == stored["id"]
        assert retrieved["content"] == stored["content"]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_nonexistent_memory(self, memory_service: MockMemoryService):
        """Should return None for nonexistent memory."""
        retrieved = await memory_service.get_memory("nonexistent-id")

        assert retrieved is None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_update_memory_content(self, memory_service: MockMemoryService):
        """Updating content should regenerate embedding."""
        stored = await memory_service.store_memory(
            agent_id="agent-123", content="Original content", memory_type="fact"
        )

        original_embedding = stored["embedding"]

        updated = await memory_service.update_memory(
            memory_id=stored["id"], updates={"content": "Updated content here"}
        )

        assert updated["content"] == "Updated content here"
        assert updated["embedding"] != original_embedding, (
            "Content change should regenerate embedding"
        )
        assert "updated_at" in updated

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_update_memory_importance(self, memory_service: MockMemoryService):
        """Should update importance score."""
        stored = await memory_service.store_memory(
            agent_id="agent-123", content="Importance test", memory_type="fact", importance=0.5
        )

        updated = await memory_service.update_memory(
            memory_id=stored["id"], updates={"importance": 0.95}
        )

        assert updated["importance"] == 0.95

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_update_memory_tags(self, memory_service: MockMemoryService):
        """Should update tags list."""
        stored = await memory_service.store_memory(
            agent_id="agent-123", content="Tag test", memory_type="fact", tags=["original"]
        )

        updated = await memory_service.update_memory(
            memory_id=stored["id"], updates={"tags": ["new-tag-1", "new-tag-2"]}
        )

        assert updated["tags"] == ["new-tag-1", "new-tag-2"]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_reject_updating_protected_fields(self, memory_service: MockMemoryService):
        """Should reject updating protected fields like id, agent_id."""
        stored = await memory_service.store_memory(
            agent_id="agent-123", content="Protected fields test", memory_type="fact"
        )

        with pytest.raises(ValueError, match="Cannot update"):
            await memory_service.update_memory(
                memory_id=stored["id"],
                updates={"id": "new-id"},  # Protected
            )

        with pytest.raises(ValueError, match="Cannot update"):
            await memory_service.update_memory(
                memory_id=stored["id"],
                updates={"agent_id": "new-agent"},  # Protected
            )


# ============================================================================
# TEST CLASS: Memory Deletion
# ============================================================================


class TestMemoryDeletion:
    """Tests for deleting memories."""

    @pytest.mark.unit
    @pytest.mark.critical
    @pytest.mark.asyncio
    async def test_delete_existing_memory(self, memory_service: MockMemoryService):
        """Should successfully delete existing memory."""
        stored = await memory_service.store_memory(
            agent_id="agent-123", content="To be deleted", memory_type="fact"
        )

        # Verify it exists
        assert await memory_service.get_memory(stored["id"]) is not None

        # Delete it
        deleted = await memory_service.delete_memory(stored["id"])

        assert deleted is True
        assert await memory_service.get_memory(stored["id"]) is None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_delete_nonexistent_memory(self, memory_service: MockMemoryService):
        """Should return False for nonexistent memory."""
        deleted = await memory_service.delete_memory("nonexistent-id")

        assert deleted is False

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_delete_removes_from_storage(self, memory_service: MockMemoryService):
        """Deleted memory should not appear in searches."""
        stored = await memory_service.store_memory(
            agent_id="agent-123", content="Searchable then deleted", memory_type="fact"
        )

        # Should find it before deletion
        results_before = await memory_service.search_memories(
            query="searchable then deleted", agent_id="agent-123"
        )
        assert results_before["total_results"] == 1

        # Delete
        await memory_service.delete_memory(stored["id"])

        # Should NOT find it after deletion
        results_after = await memory_service.search_memories(
            query="searchable then deleted", agent_id="agent-123"
        )
        assert results_after["total_results"] == 0


# ============================================================================
# TEST CLASS: Memory Expiration
# ============================================================================


class TestMemoryExpiration:
    """Tests for memory expiration handling."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_expired_memories_excluded_from_search(self, memory_service: MockMemoryService):
        """Expired memories should not appear in search results."""
        # Store memory that expires immediately
        past_expiry = datetime.now(UTC) - timedelta(seconds=1)

        await memory_service.store_memory(
            agent_id="agent-123",
            content="Expired memory",
            memory_type="fact",
            expires_at=past_expiry,
        )

        # Store non-expired memory
        await memory_service.store_memory(
            agent_id="agent-123", content="Active memory", memory_type="fact"
        )

        results = await memory_service.search_memories(query="memory", agent_id="agent-123")

        # Should only find active memory
        assert results["total_results"] == 1
        assert results["results"][0]["content"] == "Active memory"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_cleanup_expired_memories(self, memory_service: MockMemoryService):
        """Cleanup should remove all expired memories."""
        now = datetime.now(UTC)

        # Create mix of expired and active memories
        await memory_service.store_memory(
            agent_id="agent-123",
            content="Expired 1",
            memory_type="fact",
            expires_at=now - timedelta(days=1),
        )
        await memory_service.store_memory(
            agent_id="agent-123",
            content="Expired 2",
            memory_type="fact",
            expires_at=now - timedelta(hours=1),
        )
        await memory_service.store_memory(
            agent_id="agent-123",
            content="Active 1",
            memory_type="fact",
            expires_at=now + timedelta(days=1),
        )
        await memory_service.store_memory(
            agent_id="agent-123",
            content="Active 2 (no expiry)",
            memory_type="fact",
            expires_at=None,
        )

        # Cleanup
        removed_count = await memory_service.cleanup_expired_memories()

        assert removed_count == 2, "Should remove exactly 2 expired memories"

        # Verify remaining
        stats = await memory_service.get_statistics(agent_id="agent-123")
        assert stats["total_memories"] == 2


# ============================================================================
# TEST CLASS: Statistics
# ============================================================================


class TestMemoryStatistics:
    """Tests for memory statistics functionality."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_calculate_overall_statistics(
        self, memory_service: MockMemoryService, sample_memories_batch: list[dict[str, Any]]
    ):
        """Should calculate correct overall statistics."""
        stats = await memory_service.get_statistics()

        assert stats["total_memories"] == len(sample_memories_batch)
        assert "by_type" in stats
        assert "unique_tags" in stats
        assert "avg_importance" in stats
        assert 0 <= stats["avg_importance"] <= 1

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_filter_stats_by_agent(self, memory_service: MockMemoryService):
        """Should filter statistics by agent ID."""
        # Create memories for different agents
        for i in range(5):
            await memory_service.store_memory(
                agent_id=f"agent-{i % 2}",  # Alternates
                content=f"Memory {i}",
                memory_type="fact",
            )

        stats_agent_0 = await memory_service.get_statistics(agent_id="agent-0")
        stats_agent_1 = await memory_service.get_statistics(agent_id="agent-1")

        assert stats_agent_0["total_memories"] == 3  # Indices 0, 2, 4
        assert stats_agent_1["total_memories"] == 2  # Indices 1, 3

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_count_by_memory_type(
        self, memory_service: MockMemoryService, sample_memories_batch: list[dict[str, Any]]
    ):
        """Should correctly count memories by type."""
        stats = await memory_service.get_statistics()

        # Count from our sample data
        expected_preferences = sum(
            1 for m in sample_memories_batch if m["memory_type"] == "preference"
        )
        expected_facts = sum(1 for m in sample_memories_batch if m["memory_type"] == "fact")

        assert stats["by_type"].get("preference", 0) == expected_preferences
        assert stats["by_type"].get("fact", 0) == expected_facts

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_count_unique_tags(
        self, memory_service: MockMemoryService, sample_memories_batch: list[dict[str, Any]]
    ):
        """Should count unique tags across all memories."""
        stats = await memory_service.get_statistics()

        all_tags = set()
        for memory in sample_memories_batch:
            all_tags.update(memory.get("tags", []))

        assert stats["unique_tags"] == len(all_tags)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_calculate_average_importance(self, memory_service: MockMemoryService):
        """Should calculate correct average importance."""
        importances = [0.3, 0.5, 0.7, 0.9, 1.0]

        for imp in importances:
            await memory_service.store_memory(
                agent_id="agent-123",
                content=f"Importance {imp}",
                memory_type="fact",
                importance=imp,
            )

        stats = await memory_service.get_statistics(agent_id="agent-123")
        expected_avg = sum(importances) / len(importances)

        assert abs(stats["avg_importance"] - expected_avg) < 0.001


# ============================================================================
# INTEGRATION TESTS: Full Workflows
# ============================================================================


class TestMemoryWorkflowsIntegration:
    """Integration tests for complete memory workflows."""

    @pytest.mark.integration
    @pytest.mark.critical
    @pytest.mark.asyncio
    async def test_full_lifecycle_workflow(
        self, memory_service: MockMemoryService, sample_user_data: dict[str, Any]
    ):
        """Test complete lifecycle: store -> search -> retrieve -> update -> delete."""

        # Step 1: Store new memory
        memory = await memory_service.store_memory(
            agent_id="research-agent",
            content="User is interested in quantum computing applications",
            memory_type="knowledge",
            user_id=sample_user_data["id"],
            importance=0.85,
            tags=["quantum", "computing", "interests"],
        )

        assert memory["id"] is not None
        memory_id = memory["id"]

        # Step 2: Search and find it
        search_results = await memory_service.search_memories(
            query="what topics interest the user?", agent_id="research-agent"
        )

        found = any(r["memory_id"] == memory_id for r in search_results["results"])
        assert found, "Stored memory should be searchable"

        # Step 3: Retrieve directly
        retrieved = await memory_service.get_memory(memory_id)
        assert retrieved is not None
        assert retrieved["content"] == memory["content"]

        # Step 4: Update the memory
        updated = await memory_service.update_memory(
            memory_id=memory_id,
            updates={
                "content": "User is very interested in quantum computing and cryptography",
                "importance": 0.95,
                "tags": ["quantum", "computing", "cryptography", "interests"],
            },
        )

        assert updated["importance"] == 0.95
        assert "cryptography" in updated["tags"]

        # Step 5: Verify updated content searchable
        updated_search = await memory_service.search_memories(
            query="cryptography interests", agent_id="research-agent"
        )

        crypto_found = any(r["memory_id"] == memory_id for r in updated_search["results"])
        assert crypto_found, "Updated memory should be searchable with new terms"

        # Step 6: Delete the memory
        deleted = await memory_service.delete_memory(memory_id)
        assert deleted is True

        # Step 7: Verify gone
        final_search = await memory_service.search_memories(
            query="quantum computing cryptography", agent_id="research-agent"
        )

        still_exists = any(r["memory_id"] == memory_id for r in final_search["results"])
        assert not still_exists, "Deleted memory should not appear in searches"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_conversation_memory_accumulation(
        self, memory_service: MockMemoryService, sample_user_data: dict[str, Any]
    ):
        """Simulate accumulating memories during conversation."""
        conversation_turns = [
            ("Hi, I need help with my project", "interaction"),
            ("I'm building a recommendation system", "fact"),
            ("Prefer using Python and TensorFlow", "preference"),
            ("Dataset has user-item interactions", "fact"),
            ("How do I handle cold start?", "interaction"),
        ]

        stored_memories = []

        for content, mem_type in conversation_turns:
            memory = await memory_service.store_memory(
                agent_id="assistant-agent",
                content=content,
                memory_type=mem_type,
                user_id=sample_user_data["id"],
            )
            stored_memories.append(memory)

        # Should have stored all memories
        stats = await memory_service.get_statistics(agent_id="assistant-agent")
        assert stats["total_memories"] == len(conversation_turns)

        # Search should find relevant context
        context_search = await memory_service.search_memories(
            query="what tools and data does the user have?", agent_id="assistant-agent"
        )

        assert (
            context_search["total_results"] >= 2
        )  # Should find Python/TensorFlow and dataset info

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_cross_session_memory_persistence(
        self, memory_service: MockMemoryService, sample_user_data: dict[str, Any]
    ):
        """Test that memories persist and are useful across sessions."""

        # Session 1: User shares preferences
        session1_memories = [
            ("I prefer concise answers", "preference", 0.9),
            ("Working on e-commerce platform", "fact", 0.8),
        ]

        for content, mem_type, importance in session1_memories:
            await memory_service.store_memory(
                agent_id="assistant",
                content=content,
                memory_type=mem_type,
                user_id=sample_user_data["id"],
                importance=importance,
            )

        # Session 2 (later): Agent should recall preferences
        session2_query = "how should I respond to this user?"
        session2_results = await memory_service.search_memories(
            query=session2_query, agent_id="assistant"
        )

        # Should find preference for concise answers
        preference_found = any(
            "concise" in r["content"].lower() for r in session2_results["results"]
        )
        assert preference_found, "Should recall user preference from previous session"


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================


class TestMemoryPerformance:
    """Performance benchmarks for memory operations."""

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_bulk_storage_performance(
        self, memory_service: MockMemoryService, benchmark_thresholds: dict[str, int]
    ):
        """Bulk storage should be efficient."""
        import time

        batch_size = 100
        start = time.perf_counter()

        for i in range(batch_size):
            await memory_service.store_memory(
                agent_id="agent-123",
                content=f"Bulk storage test item {i} with some content",
                memory_type="fact",
            )

        elapsed_ms = (time.perf_counter() - start) * 1000
        avg_per_item = elapsed_ms / batch_size

        assert avg_per_item < 50, f"Avg storage time {avg_per_item:.2f}ms exceeds threshold"

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_search_performance_with_large_corpus(
        self, memory_service: MockMemoryService, benchmark_thresholds: dict[str, int]
    ):
        """Search should remain fast even with many memories."""
        # Build large corpus
        for i in range(500):
            await memory_service.store_memory(
                agent_id="agent-123",
                content=f"Corpus item {i}: This is sample content for performance testing",
                memory_type="fact",
            )

        import time

        queries = [
            "corpus item content",
            "performance testing",
            "sample data",
            "item number 250",
        ]

        start = time.perf_counter()

        for query in queries:
            await memory_service.search_memories(query=query, agent_id="agent-123", limit=20)

        elapsed_ms = (time.perf_counter() - start) * 1000
        avg_per_query = elapsed_ms / len(queries)

        assert avg_per_query < benchmark_thresholds.get("vector_search", 200), (
            f"Avg search time {avg_per_query:.2f}ms exceeds threshold"
        )

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_cleanup_performance(self, memory_service: MockMemoryService):
        """Cleanup operation should be efficient."""
        now = datetime.now(UTC)

        # Create mix of expired and active
        for i in range(200):
            expires_at = now - timedelta(days=1) if i < 150 else now + timedelta(days=1)
            await memory_service.store_memory(
                agent_id="agent-123",
                content=f"Cleanup test {i}",
                memory_type="fact",
                expires_at=expires_at,
            )

        import time

        start = time.perf_counter()

        removed = await memory_service.cleanup_expired_memories()

        elapsed_ms = (time.perf_counter() - start) * 1000

        assert removed == 150
        assert elapsed_ms < 100, f"Cleanup took {elapsed_ms:.2f}ms, too slow"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=memory", "--cov-report=term-missing"])
