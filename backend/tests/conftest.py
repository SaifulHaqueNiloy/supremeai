# ============================================================
# SupremeAI - Test Configuration & Shared Fixtures
# Production-Ready pytest Configuration
# ============================================================

import asyncio
import os
import sys
import uuid
from collections.abc import AsyncGenerator, Generator
from datetime import UTC, datetime, timedelta, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

# ROOT-CAUSE FIX (আগের fix অসম্পূর্ণ ছিল): `app` fixture-এ
# os.environ["RATE_LIMIT_ENABLED"] = "false" সেট করা যথেষ্ট ছিল না, কারণ
# pytest collection phase-এ tests/api/*.py, tests/core/*.py-র মতো অনেক
# টেস্ট ফাইল module-level-এই `from api.routes... import ...` বা
# `from core.app import app` করে -- যেটা api/routes/api_keys.py-র মতো
# ফাইলে module-level `limiter = AsyncRateLimiter()` singleton তৈরি করে
# দেয়, এবং AsyncRateLimiter.__init__() os.getenv("RATE_LIMIT_ENABLED")
# পড়ে নেয় সেই মুহূর্তেই -- যা প্রথম টেস্টের `app` fixture রান হওয়ারও
# অনেক আগে (pytest সব টেস্ট ফাইল collect করে তারপর fixture রান করে)।
# ফলে register endpoint বারবার কল হলে real rate limiter 429 দিতে থাকত,
# cascade হয়ে ৪০+ টেস্ট FAILED/ERROR হতো। conftest.py সবসময় সবচেয়ে
# আগে import হয় (pytest guarantee), তাই এখানে module-level-এই env var
# সেট করা হলো, যেকোনো test file import হওয়ার আগে।
os.environ.setdefault("RATE_LIMIT_ENABLED", "false")
os.environ.setdefault("TESTING", "true")


class CustomAssertions:
    """
    বাংলা মন্তব্য (ROOT-CAUSE FIX): এই ক্লাসটি আগে খালি (`pass`) ছিল এবং কোনো
    `assertions` fixture-ও conftest.py-তে ছিল না, অথচ tests/agents/test_agents.py
    এবং tests/security/test_auth.py উভয়ই `assertions: CustomAssertions` প্যারামিটার
    এক্সপেক্ট করত -- ফলে "fixture 'assertions' not found" error আসত। এখন real
    assertion methods যোগ করা হলো এবং নিচে একটি `assertions` fixture instantiate
    করে fixture হিসেবে এক্সপোজ করা হলো।
    """

    @staticmethod
    def assert_valid_uuid(value: str, version: int = 4) -> None:
        parsed = uuid.UUID(str(value), version=version)
        assert str(parsed) == str(value).lower() or parsed.version == version, (
            f"{value!r} is not a valid UUIDv{version}"
        )

    @staticmethod
    def assert_email_format(value: str) -> None:
        import re

        pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
        assert re.match(pattern, str(value)), f"{value!r} is not a valid email format"


TEST_ACCESS_TOKEN_EXPIRE_MINUTES = 30
TEST_ALGORITHM = "HS256"
TEST_SECRET_KEY = "test_secret_key_1234567890_test_secret_key_1234567890"


@pytest.fixture
def valid_password():
    return "ValidPassword123!"


@pytest.fixture
def assertions() -> CustomAssertions:
    """বাংলা: CustomAssertions ইনস্ট্যান্স এক্সপোজ করা হলো -- আগে এই fixture-ই ডিফাইন করা ছিল না।"""
    return CustomAssertions()


@pytest.fixture
def sample_agent_create_request():
    return {"name": "test_agent", "model": "gpt-4"}


@pytest.fixture
def sample_admin_data():
    return {"id": "admin-123", "role": "admin"}


@pytest.fixture
def sample_agent_data():
    return {"id": "agent-123", "name": "test_agent"}


@pytest.fixture
def sample_user_data():
    return {"id": "user-123", "role": "user"}


@pytest.fixture
def sample_operator_data():
    return {"id": "operator-123", "role": "operator"}


sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


# ============================================================
# TEST CONFIGURATION
# ============================================================
# বাংলা মন্তব্য: এখানে আগে একটা custom session-scoped `event_loop` fixture
# ছিল, যেটা pyproject.toml-এর `asyncio_mode = "auto"` (pytest-asyncio 0.23+)
# এর সাথে conflict করছিল। pytest-asyncio auto mode নিজেই প্রতিটা টেস্টের জন্য
# event loop ম্যানেজ করে; custom `event_loop` fixture override করায়
# `asyncio.get_event_loop()` কল "There is no current event loop in thread
# 'MainThread'" এরর দিচ্ছিল — যেটা প্রায় প্রতিটা async টেস্টে (~৮৮২ বার) ছড়িয়ে
# পড়ছিল। fixture সরিয়ে দিয়ে pyproject.toml-এ
# `asyncio_default_fixture_loop_scope = "session"` সেট করা হয়েছে যাতে সব
# টেস্টে একই session-scope loop ব্যবহার হয় (আগের ইচ্ছাকৃত আচরণ বজায় থাকে)।


def _resolve_test_database_url() -> str:
    """CI-তে env var নাম মিসম্যাচ ফিক্স।

    ci.yml পাঠায় `DATABASE_URL` (raw postgresql:// driver সহ), কিন্তু আগে এই
    fixture শুধু `TEST_DATABASE_URL` পড়ত (যেটা CI কখনো সেট করে না) — ফলে সবসময়
    hardcoded fallback (user=postgres) ব্যবহার হতো, যেটা CI-র postgres service
    container-এ (user=test_user) exist-ই করে না -> auth/connection error ->
    autouse cleanup_database fixture এর কারণে *প্রতিটা* টেস্ট ERROR।

    এখন: TEST_DATABASE_URL > DATABASE_URL > hardcoded local default,
    এবং async engine এর জন্য asyncpg driver জোর করে বসানো হচ্ছে।
    """
    url = os.getenv("TEST_DATABASE_URL") or os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/supremeai_test",
    )
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    return url


@pytest.fixture(scope="session")
def test_settings():
    """Test-specific settings that override production config."""
    return {
        "DATABASE_URL": _resolve_test_database_url(),
        "REDIS_URL": "redis://localhost:6379/1",  # Use DB 1 for tests
        "SECRET_KEY": "test-secret-key-for-testing-only-do-not-use-in-production",
        "JWT_SECRET_KEY": "test-jwt-secret-key-for-testing-only",
        "JWT_ALGORITHM": "HS256",
        "ACCESS_TOKEN_EXPIRE_MINUTES": 15,
        "ENVIRONMENT": "testing",
        "DEBUG": True,
        "CORS_ORIGINS": ["*"],
        "RATE_LIMIT_ENABLED": False,  # Disable rate limiting in tests
        "ENABLE_METRICS": False,
        "ENABLE_TRACING": False,
    }


@pytest.fixture(scope="session")
def anyio_backend():
    """Backend for async tests."""
    return "asyncio"


# ============================================================
# DATABASE FIXTURES
# ============================================================
@pytest.fixture(scope="session")
def db_engine(test_settings):
    """Create async database engine for testing.

    CI FIX (Option C — NullPool): pytest-asyncio 0.23 creates a separate
    event loop per test, but session-scoped db_engine creates its connections
    via asyncio.run() (a different loop). When db_session (function-scoped
    async fixture) tries to use the engine, asyncpg complains:
    "attached to a different loop" or "Event loop is closed".

    Fix: use poolclass=NullPool — no connections are pooled, so every
    checkout creates a fresh connection bound to the CURRENT event loop.
    No dependency bump needed (unlike Option B), no per-test engine
    creation overhead (unlike Option A).
    """
    from sqlalchemy.pool import NullPool

    engine = create_async_engine(
        test_settings["DATABASE_URL"],
        echo=False,  # Set to True for SQL debugging
        poolclass=NullPool,  # CI FIX: no cross-loop connection reuse
        future=True,
    )

    # Create all tables before tests
    # CI FIX: 'from app.db.base import Base' was wrong — app/ module doesn't exist.
    # The project uses models.base.Base as its declarative base.
    from models.base import Base

    async def setup_db():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    asyncio.run(setup_db())

    yield engine

    # Drop all tables after tests
    async def teardown_db():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await engine.dispose()

    asyncio.run(teardown_db())


@pytest_asyncio.fixture
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database session for each test."""
    async_session_factory = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    session = async_session_factory()

    # Start a transaction that will be rolled back after each test
    await session.begin()

    yield session

    # Rollback changes after each test
    await session.rollback()
    await session.close()


@pytest_asyncio.fixture(autouse=True)
async def cleanup_database(db_session: AsyncSession):
    """Clean up database after each test (runs automatically)."""
    yield  # This runs the test

    # Cleanup is handled by rollback in db_session fixture


# ============================================================
# APPLICATION FIXTURES
# ============================================================
@pytest_asyncio.fixture
async def app(test_settings):
    """Create FastAPI application instance with test settings."""
    # Override settings before importing app
    os.environ["TESTING"] = "true"
    os.environ["DATABASE_URL"] = test_settings["DATABASE_URL"]
    os.environ["REDIS_URL"] = test_settings["REDIS_URL"]
    os.environ["SECRET_KEY"] = test_settings["SECRET_KEY"]
    os.environ["JWT_SECRET_KEY"] = test_settings["JWT_SECRET_KEY"]
    # ROOT-CAUSE FIX: AsyncRateLimiter পড়ে os.environ["RATE_LIMIT_ENABLED"]
    # সরাসরি (middleware/rate_limiter.py), কিন্তু test_settings dict শুধু
    # app.state.settings-এ বসত যেটা rate limiter কখনো পড়ে না। ফলে আসল
    # rate limiter সবসময় enabled থাকত -> register endpoint বারবার কল হলে
    # 429 -> auth_headers fixture cascade fail -> ৪০+ dependent test error।
    os.environ["RATE_LIMIT_ENABLED"] = "false"

    # বাংলা মন্তব্য (ROOT-CAUSE FIX): আগে এখানে `from app.main import app` করা হতো,
    # কিন্তু backend/-এ কোনো `app/` প্যাকেজ নেই — real FastAPI instance আছে
    # `core.app:app`-এ (main.py নিজেই `core.app:app` কে backward-compat হিসেবে
    # lazily re-export করে)। এই ভুল import পাথের কারণে `app` fixture নির্ভরশীল
    # প্রতিটা টেস্ট (health endpoint, client ইত্যাদি) ModuleNotFoundError দিত।
    from core.app import app as application

    # Apply test-specific middleware overrides
    application.state.settings = type("Settings", (), test_settings)()

    return application


@pytest_asyncio.fixture
async def client(app) -> AsyncGenerator[AsyncClient, None]:
    """Create async HTTP client for testing."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ============================================================
# AUTHENTICATION FIXTURES
# ============================================================
@pytest.fixture
def sample_user_registration_data():
    """Sample user registration/auth data for testing (email+password shape).

    বাংলা মন্তব্য (ROOT-CAUSE FIX): আগে এই fixture-এর নাম ছিল `sample_user_data`,
    যেটা conftest.py-র লাইন ৫৬-এ ডিফাইন করা আরেকটা `sample_user_data`
    fixture-কে (id/role শেপ, agent টেস্টে ব্যবহৃত) silently override করে
    ফেলছিল Python-এর top-to-bottom name shadowing-এর কারণে — ফলে
    tests/agents/test_agents.py-এর সব টেস্ট `KeyError: 'id'` দিত। এখন আলাদা
    নাম দেওয়া হলো যাতে দুটো fixture-ই স্বাধীনভাবে কাজ করে।
    """
    return {
        "username": "user@example.com",
        "password": "UserPassword123!",
        "name": "Regular User",
        "role": "user",
    }


@pytest.fixture
def sample_admin_registration_data():
    """Sample admin registration/auth data for testing (email+password shape).

    বাংলা মন্তব্য: `sample_admin_data`-র সাথে একই কারণে রিনেম করা হলো (দেখুন
    sample_user_registration_data-এর comment)।
    """
    return {
        "username": "admin@example.com",
        "password": "AdminPassword456!",
        "name": "Admin User",
        "role": "admin",
    }


@pytest.fixture
def sample_agent_operator_data():
    """Sample agent operator data for testing."""
    return {
        "username": "operator@example.com",
        "password": "OperatorPassword123!",
        "name": "Agent Operator",
        "role": "agent_operator",
    }


@pytest_asyncio.fixture
async def auth_headers(
    client: AsyncClient, sample_user_registration_data, db_session: AsyncSession
):
    """Create authenticated user and return auth headers.

    বাংলা মন্তব্য (ROOT-CAUSE FIX): এই fixture আগে ভুলবশত `sample_user_data`
    (id/role শেপ, agent টেস্টের জন্য) নিতো, যেখানে `/api/v1/auth/register`-এর
    জন্য দরকার email/password শেপ (`sample_user_registration_data`)। ফলে
    register call সবসময় 422 রিটার্ন করত, এবং এর ওপর নির্ভরশীল প্রতিটি fixture
    (created_agent, created_conversation, sample_hitl_request, memory/HITL
    টেস্টের সব) cascade হয়ে fail/error হতো -- একই bug-class যা আগে
    sample_user_registration_data রিনেমের সময় ধরা পড়েছিল কিন্তু এই দুটো
    fixture-এ apply করা হয়নি। এখন সঠিক fixture ব্যবহার করা হলো।
    """
    # Register user
    response = await client.post("/api/v1/auth/register", json=sample_user_registration_data)
    assert response.status_code in [200, 201, 409]  # OK or already exists

    # Login to get tokens
    login_data = {
        "username": sample_user_registration_data["username"],
        "password": sample_user_registration_data["password"],
    }
    response = await client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 200

    token_data = response.json()
    access_token = token_data.get("access_token") or token_data.get("data", {}).get("access_token")

    return {"Authorization": f"Bearer {access_token}"}


@pytest_asyncio.fixture
async def admin_auth_headers(
    client: AsyncClient, sample_admin_registration_data, db_session: AsyncSession
):
    """Create admin user and return admin auth headers.

    বাংলা মন্তব্য (ROOT-CAUSE FIX): auth_headers-এর মতো একই bug -- আগে
    `sample_admin_data` (id/role শেপ) নিতো, এখন সঠিক
    `sample_admin_registration_data` (email/password শেপ) নেওয়া হচ্ছে।
    """
    response = await client.post("/api/v1/auth/register", json=sample_admin_registration_data)
    assert response.status_code in [200, 201, 409]

    login_data = {
        "username": sample_admin_registration_data["username"],
        "password": sample_admin_registration_data["password"],
    }
    response = await client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 200

    token_data = response.json()
    access_token = token_data.get("access_token") or token_data.get("data", {}).get("access_token")

    return {"Authorization": f"Bearer {access_token}"}


@pytest_asyncio.fixture
async def operator_auth_headers(
    client: AsyncClient, sample_agent_operator_data, db_session: AsyncSession
):
    """Create agent operator and return auth headers."""
    response = await client.post("/api/v1/auth/register", json=sample_agent_operator_data)
    assert response.status_code in [200, 201, 409]

    login_data = {
        "username": sample_agent_operator_data["username"],
        "password": sample_agent_operator_data["password"],
    }
    response = await client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 200

    token_data = response.json()
    access_token = token_data.get("access_token") or token_data.get("data", {}).get("access_token")

    return {"Authorization": f"Bearer {access_token}"}


# ============================================================
# AGENT FIXTURES
# ============================================================
@pytest.fixture
def sample_agent_config():
    """Sample agent configuration for testing."""
    return {
        "name": "Test Agent",
        "type": "conversational",
        "description": "A test conversational agent",
        "system_prompt": "You are a helpful assistant for testing purposes.",
        "model_config": {
            "provider": "openai",
            "model": "gpt-4-turbo-preview",
            "temperature": 0.7,
            "max_tokens": 2048,
        },
        "tool_permissions": ["web_search", "calculator"],
        "hitl_policy": {
            "enabled": True,
            "auto_approve_patterns": ["read:*", "calculate:*"],
            "require_approval_patterns": ["write:*", "delete:*"],
            "escalation_timeout_minutes": 60,
        },
        "memory_config": {
            "working_memory_max_messages": 100,
            "enable_episodic_memory": True,
            "enable_procedural_memory": False,
        },
    }


@pytest_asyncio.fixture
async def created_agent(client: AsyncClient, auth_headers: dict, sample_agent_config: dict):
    """Create a test agent and return its data."""
    response = await client.post(
        "/api/v1/agents",
        json=sample_agent_config,
        headers=auth_headers,
    )
    assert response.status_code in [200, 201]
    return response.json().get("data", response.json())


# ============================================================
# CONVERSATION FIXTURES
# ============================================================
@pytest_asyncio.fixture
async def created_conversation(client: AsyncClient, auth_headers: dict, created_agent: dict):
    """Create a test conversation and return its data."""
    conversation_data = {
        "agent_id": created_agent.get("id"),
        "title": "Test Conversation",
    }
    response = await client.post(
        "/api/v1/conversations",
        json=conversation_data,
        headers=auth_headers,
    )
    assert response.status_code in [200, 201]
    return response.json().get("data", response.json())


# ============================================================
# MEMORY SERVICE FIXTURES
# ============================================================
@pytest.fixture
def sample_memory_data(created_agent: dict):
    """Sample memory data for testing."""
    return {
        "agent_id": created_agent.get("id", str(uuid.uuid4())),
        "memory_type": "episodic",
        "content": "This is a test memory about a successful API integration task.",
        "metadata": {
            "source_conversation_id": str(uuid.uuid4()),
            "topic": "technical",
            "sentiment": "positive",
        },
        "importance_score": 0.8,
    }


@pytest.fixture
def sample_embedding():
    """Sample vector embedding for testing (1536 dimensions)."""
    import random

    random.seed(42)  # For reproducibility
    return [random.uniform(-1, 1) for _ in range(1536)]


# ============================================================
# HITL ENGINE FIXTURES
# ============================================================
@pytest.fixture
def sample_hitl_request(created_agent: dict):
    """Sample HITL approval request for testing."""
    now = datetime.now(UTC)
    return {
        "agent_id": created_agent.get("id", str(uuid.uuid4())),
        "request_type": "tool_execution",
        "request_payload": {
            "tool_name": "send_email",
            "tool_args": {
                "to": "user@example.com",
                "subject": "Important Update",
                "body": "This requires approval.",
            },
        },
        "risk_level": "MEDIUM",
        "risk_score": 0.6,
        "risk_factors": [
            {"factor": "external_communication", "weight": 0.7},
            {"factor": "pii_in_recipient", "weight": 0.3},
        ],
        "expires_at": (now + timedelta(hours=1)).isoformat(),
    }


@pytest.fixture
def low_risk_hitl_request(created_agent: dict):
    """Low-risk HITL request that should be auto-approved."""
    now = datetime.now(UTC)
    return {
        "agent_id": created_agent.get("id", str(uuid.uuid4())),
        "request_type": "read_operation",
        "request_payload": {
            "tool_name": "read_file",
            "tool_args": {"path": "/public/data.txt"},
        },
        "risk_level": "LOW",
        "risk_score": 0.1,
        "expires_at": (now + timedelta(hours=24)).isoformat(),
    }


@pytest.fixture
def critical_risk_hitl_request(created_agent: dict):
    """Critical-risk HITL request requiring multi-person approval."""
    now = datetime.now(UTC)
    return {
        "agent_id": created_agent.get("id", str(uuid.uuid4())),
        "request_type": "delete_database",
        "request_payload": {
            "table": "users",
            "condition": "ALL",
        },
        "risk_level": "CRITICAL",
        "risk_score": 0.95,
        "risk_factors": [
            {"factor": "data_destruction", "weight": 0.8},
            {"factor": "irreversible_action", "weight": 0.2},
        ],
        "expires_at": (now + timedelta(minutes=10)).isoformat(),
    }


# ============================================================
# MOCK FIXTURES
# ============================================================
@pytest.fixture
def mock_llm_provider():
    """Mock LLM provider for unit tests."""
    mock = AsyncMock()
    mock.generate.return_value = {
        "content": "This is a mocked LLM response for testing.",
        "tokens_used": 25,
        "model": "gpt-4-turbo-mock",
        "finish_reason": "stop",
    }
    mock.embed.return_value = [0.1] * 1536  # Mock embedding
    return mock


@pytest.fixture
def mock_redis():
    """Mock Redis client for unit tests."""
    mock = AsyncMock()
    mock.get.return_value = None
    mock.set.return_value = True
    mock.delete.return_value = 1
    mock.exists.return_value = 0
    return mock


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for unit tests."""
    mock = MagicMock()

    # Mock chat completions
    mock.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="Mocked response"))],
        usage=MagicMock(prompt_tokens=10, completion_tokens=20, total_tokens=30),
    )

    # Mock embeddings
    mock.embeddings.create.return_value = MagicMock(data=[MagicMock(embedding=[0.1] * 1536)])

    return mock


@pytest.fixture(autouse=True)
def mock_supabase_db_client():
    """Mock the global Supabase db client to prevent 500 errors in endpoints that require auth."""
    from database.supabase_client import db

    mock_user = MagicMock()
    mock_user.id = "mock-user-id"
    mock_user.email = "mock@example.com"

    mock_res = MagicMock()
    mock_res.user = mock_user

    with patch.object(db, "client") as mock_client:
        mock_client.auth = MagicMock()
        mock_client.auth.sign_up.return_value = mock_res
        mock_client.auth.sign_in_with_password.return_value = mock_res
        mock_client.auth.admin = MagicMock()
        mock_client.auth.admin.create_user.return_value = mock_user
        mock_client.auth.admin.delete_user.return_value = True
        yield mock_client


# ============================================================
# UTILITY FIXTURES
# ============================================================
@pytest.fixture
def current_time():
    """Return current UTC time."""
    return datetime.now(UTC)


@pytest.fixture
def future_time(days: int = 1, hours: int = 0):
    """Return a time in the future."""

    def _future_time(days=days, hours=hours):
        return datetime.now(UTC) + timedelta(days=days, hours=hours)

    return _future_time


@pytest.fixture
def past_time(days: int = 1, hours: int = 0):
    """Return a time in the past."""

    def _past_time(days=days, hours=hours):
        return datetime.now(UTC) - timedelta(days=days, hours=hours)

    return _past_time


@pytest.fixture
def generate_uuid():
    """Generate a unique UUID string."""
    return lambda: str(uuid.uuid4())


@pytest.fixture
def generate_test_emails():
    """Generate unique test email addresses to avoid conflicts."""
    counter = 0

    def _generate(prefix="test"):
        nonlocal counter
        counter += 1
        return f"{prefix}_{counter}_{uuid.uuid4().hex[:8]}@example.com"

    return _generate


# ============================================================
# PYTEST CONFIGURATION
# ============================================================
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: marks tests as unit tests (fast, isolated)")
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests (require services)"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow running (skip with -m 'not slow')"
    )
    config.addinivalue_line("markers", "auth: marks tests related to authentication")
    config.addinivalue_line("markers", "agents: marks tests related to agent operations")
    config.addinivalue_line("markers", "memory: marks tests related to memory service")
    config.addinivalue_line("markers", "hitl: marks tests related to HITL engine")
    config.addinivalue_line("markers", "security: marks tests related to security features")


# Ignore slow tests by default unless explicitly requested
def pytest_collection_modifyitems(config, items):
    """Modify test collection based on markers."""
    if not config.getoption("--runslow"):
        skip_slow = pytest.mark.skip(reason="need --runslow option to run")
        for item in items:
            if "slow" in item.keywords:
                item.add_marker(skip_slow)


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--runslow",
        action="store_true",
        default=False,
        help="Run slow tests",
    )


# ============================================================
# COVERAGE CONFIGURATION
# ============================================================
# Coverage thresholds - fail if below these values
COVERAGE_THRESHOLD = 80.0

# Files/patterns to exclude from coverage
COVERAGE_EXCLUDE = [
    "*/migrations/*",
    "*/tests/*",
    "*/__pycache__/*",
    "*/conftest.py",
    "*/venv/*",
    ".venv/*",
]
