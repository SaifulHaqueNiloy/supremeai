"""Tests for core.cache.redis_manager — SecureRedisManager and IdempotencyLock.

বাংলা: Redis ক্যাশ ম্যানেজার এবং আইডেম্পোটেন্সি লক টেস্ট।
"""

from unittest.mock import AsyncMock

import pytest

from core.cache.redis_manager import (
    SecureRedisManager,
)


@pytest.fixture
def mock_redis_client():
    """Create a mock Redis async client."""
    client = AsyncMock(spec_set=["set", "get", "delete", "aclose", "pipeline"])
    client.pipeline.return_value = client
    client.set.return_value = True
    client.get.return_value = "test_value"
    client.delete.return_value = 1
    return client


@pytest.fixture
def manager():
    """Create a fresh SecureRedisManager for each test."""
    m = SecureRedisManager()
    m._client = None
    m._initialized = False
    return m
