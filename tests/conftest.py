# tests/conftest.py
"""Pytest configuration and shared fixtures for SupremeAI root test suite.

বাংলা: এই conftest শুধু root tests/ ফোল্ডারের জন্য।
গুরুত্বপূর্ণ: sys.modules['core'] = MagicMock() করা হয় না এখানে কারণ
backend/tests/conftest.py ইতিমধ্যে সঠিকভাবে sys.path সেটআপ করে।
এই blanket MagicMock টেস্টে settings-এর real value নষ্ট করে দিত।
"""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add project root to sys.path so 'backend.*' imports resolve
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Add backend/ to sys.path so 'core.*' imports also resolve (same as backend/tests/conftest.py)
backend_root = project_root / "backend"
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))


# ---------------------------------------------------------------------------
# Fixtures shared across root tests/
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_docker_sandbox():
    """Mock DockerSandbox for testing without actual container runtime."""
    with patch("backend.agents.ephemeral_executor.DockerSandbox") as mock:
        instance = MagicMock()
        instance.run_quarantine_test.return_value = {
            "exit_code": 0,
            "stdout": "Success",
            "stderr": "",
        }
        mock.return_value = instance
        yield instance


@pytest.fixture
def mock_docker_sandbox_file_gate():
    """Mock DockerSandbox for FileIsolationGate tests."""
    with patch("backend.sandbox.file_isolation_gate.DockerSandbox") as mock:
        instance = MagicMock()
        instance.run_safe_container.return_value = {
            "exit_code": 0,
            "output": "File Size Processed inside Container: 52 bytes",
        }
        mock.return_value = instance
        yield instance


@pytest.fixture
def mock_genai():
    """Mock Google Gemini AI client."""
    with patch("backend.skills.core_knowledge_qa.genai") as mock_genai_module:
        mock_response = MagicMock()
        mock_response.text = "Test answer from AI"
        mock_response.candidates = []

        mock_genai_module.Client.return_value.models.generate_content.return_value = mock_response
        yield mock_genai_module


@pytest.fixture
def mock_firestore():
    """Mock Firestore client."""
    with patch("backend.api.dependencies.TenantAwareFirestore") as mock:
        instance = AsyncMock()
        mock.return_value = instance
        yield instance


@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    with patch("backend.core.config.settings") as mock:
        mock.gemini_api_key = "test-api-key"
        mock.supabase_url = "https://test.supabase.co"
        mock.supabase_key = "test-key"
        yield mock


@pytest.fixture
def mock_redis():
    """Mock Redis client for rate limiting and caching."""
    with patch("redis.asyncio.Redis") as mock:
        instance = AsyncMock()
        mock.return_value = instance
        yield instance


@pytest.fixture
def sample_skill_payload():
    """Sample skill payload for testing."""
    return {
        "name": "test_skill",
        "description": "A test skill for unit testing",
        "code": "def execute(payload): return {'result': payload}",
        "entry_file": "main.py",
    }


@pytest.fixture
def sample_bangla_text():
    """Sample Bangla text for testing language detection."""
    return "আমি সুপ্রিম এআই ব্যবহার করছি"


@pytest.fixture
def sample_user_context():
    """Sample user context for RBAC testing."""
    return {
        "user_id": "test-user-123",
        "user_role": "Admin",
        "tenant_id": "test-tenant-456",
    }
