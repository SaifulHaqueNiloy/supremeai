# tests/conftest.py
"""Pytest configuration and shared fixtures for SupremeAI test suite."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# বাংলা মন্তব্য: backend/ কে sys.path-এ যোগ করা হচ্ছে যাতে "core.x" ইম্পোর্টগুলো
# (backend/-এর ভেতরের কনভেনশন) আসল প্যাকেজ খুঁজে পায় — নিচের নির্দিষ্ট submodule mock গুলো
# (ভারী/optional dependency-ওয়ালা) তখনও কাজ করবে, কারণ Python import system প্রথমে
# sys.modules cache-ই চেক করে।
backend_dir = project_root / "backend"
if backend_dir.is_dir():
    sys.path.insert(0, str(backend_dir))

# Mock only the genuinely heavy/optional core submodules — NOT the whole "core" package.
# আগে এখানে sys.modules['core'] = MagicMock() ছিল যা পুরো core প্যাকেজকেই ব্লক করে দিত,
# ফলে core.cache, core.config, core.otp_router-এর মতো অন্য যেকোনো real submodule import
# (যেমন backend/middleware/anti_hacking.py) ভেঙে যেত: "ModuleNotFoundError: No module
# named 'core.cache'; 'core' is not a package"।
sys.modules['core.evolution'] = MagicMock()
sys.modules['core.llm'] = MagicMock()
sys.modules['core.observability'] = MagicMock()
sys.modules['core.orchestration'] = MagicMock()
# বাংলা: core.security ও core.messaging ব্লক করা যাবে না — core.config (সব core.* মডিউলের
# load-bearing dependency) ট্রানজিটিভলি এ দুটোর উপর নির্ভরশীল (secret_vault -> event_bus)।


@pytest.fixture
def mock_docker_sandbox():
    """Mock DockerSandbox for testing without actual container runtime."""
    with patch('backend.agents.ephemeral_executor.DockerSandbox') as mock:
        instance = MagicMock()
        instance.run_quarantine_test.return_value = {
            "exit_code": 0,
            "stdout": "Success",
            "stderr": ""
        }
        mock.return_value = instance
        yield instance


@pytest.fixture
def mock_docker_sandbox_file_gate():
    """Mock DockerSandbox for FileIsolationGate tests."""
    with patch('backend.sandbox.file_isolation_gate.DockerSandbox') as mock:
        instance = MagicMock()
        instance.run_safe_container.return_value = {
            "exit_code": 0,
            "output": "File Size Processed inside Container: 52 bytes"
        }
        mock.return_value = instance
        yield instance


@pytest.fixture
def mock_genai():
    """Mock Google Gemini AI client."""
    with patch('backend.skills.core_knowledge_qa.genai') as mock_genai_module:
        mock_client = MagicMock()
        mock_types = MagicMock()
        mock_types.GenerateContentResponse = MagicMock
        mock_types.Content = MagicMock

        # Create a mock response
        mock_response = MagicMock()
        mock_response.text = "Test answer from AI"
        mock_response.candidates = []

        mock_client.Client.return_value = MagicMock()
        mock_client.Client.return_value.models = MagicMock()
        mock_client.Client.return_value.models.generate_content.return_value = mock_response

        mock_genai_module.Client = MagicMock(return_value=MagicMock())
        mock_genai_module.Client.return_value.models = MagicMock()
        mock_genai_module.Client.return_value.models.generate_content.return_value = mock_response

        yield mock_client


@pytest.fixture
def mock_firestore():
    """Mock Firestore client."""
    with patch('backend.api.dependencies.TenantAwareFirestore') as mock:
        instance = AsyncMock()
        mock.return_value = instance
        yield instance


@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    with patch('backend.core.config.settings') as mock:
        mock.gemini_api_key = MagicMock(return_value="test-api-key")
        mock.supabase_url = MagicMock(return_value="https://test.supabase.co")
        mock.supabase_key = MagicMock(return_value="test-key")
        yield mock


@pytest.fixture
def mock_redis():
    """Mock Redis client for rate limiting and caching."""
    with patch('redis.asyncio.Redis') as mock:
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
        "entry_file": "main.py"
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
        "tenant_id": "test-tenant-456"
    }
