# backend/conftest.py
# Test configuration and fixtures for SupremeAI backend
import os
import pytest
from unittest.mock import patch, MagicMock
import asyncio


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up test environment variables."""
    # Set test-specific environment variables
    os.environ.setdefault("TESTING", "True")
    os.environ.setdefault("ENV", "test")
    # Use in-memory or mock database/redis for tests
    os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
    os.environ.setdefault("REDIS_URL", "redis://mocked-redis-url")

    yield

    # Cleanup environment variables after test
    if "TESTING" in os.environ:
        del os.environ["TESTING"]
    if "ENV" in os.environ:
        del os.environ["ENV"]


@pytest.fixture
def mock_redis():
    """Provide a mocked Redis instance for tests."""
    with patch("redis.asyncio.from_url") as mock_redis_constructor:
        mock_connection = MagicMock()
        mock_connection.ping = MagicMock(return_value=True)
        mock_connection.set = MagicMock(return_value=True)
        mock_connection.get = MagicMock(return_value=None)
        mock_redis_constructor.return_value = mock_connection
        yield mock_connection


@pytest.fixture
def mock_async_redis():
    """Provide an async Redis mock for async tests."""
    with patch("redis.asyncio.Redis.from_url") as mock_redis_constructor:
        mock_instance = MagicMock()
        mock_instance.ping = asyncio.Future()
        mock_instance.ping.set_result(True)
        mock_instance.set = asyncio.Future()
        mock_instance.set.set_result(True)
        mock_instance.get = asyncio.Future()
        mock_instance.get.set_result(None)
        mock_redis_constructor.return_value = mock_instance
        yield mock_instance


@pytest.fixture(autouse=True)
def mock_external_apis():
    """Mock external API calls to prevent network requests during tests."""
    with (
        patch("requests.get") as mock_get,
        patch("requests.post") as mock_post,
        patch("requests.put") as mock_put,
        patch("requests.delete") as mock_delete,
    ):
        # Configure mocks to return successful responses
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {}
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {}

        yield {"get": mock_get, "post": mock_post, "put": mock_put, "delete": mock_delete}


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
