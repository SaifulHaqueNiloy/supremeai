# Part 12: Pytest Test Suite & Integration Tests Audit

> **Audit Generation Time:** `2026-07-24 20:29:11 UTC`
> **Module Description:** Backend pytest test suite, API integration test cases, and resilience coverage.
> **Status:** `SELF_CONTAINED / READY FOR EXTERNAL AI AUDIT`

---

## 1. 📁 Target Subsystems & File Inventory

- `backend/tests/` (Directory, 1244 files)

---

## 2. 🔍 Audit Objectives & Key Checklist

- [ ] **Code Quality & Type Safety:** Check MyPy type hints and Ruff linting rules.
- [ ] **Security & Resilience:** Check exception handling, circuit breakers, and rate limiters.
- [ ] **Zero-Cost & Free-Tier Optimization:** Ensure no paid cloud service dependencies.
- [ ] **Bangla Code Comments:** Verify `// বাংলা মন্তব্য` is present across updated code blocks.

---

## 3. 📦 Complete Subsystem Source Code Dump

Below is the full source code for all target files in this module. Any external AI can audit this single document directly.

### 📄 `backend/tests/conftest.py`

```py
import os
import sys

from loguru import logger

# বাংলা মন্তব্য: pytest কালেকশনের সময় loguru-এর ডিফল্ট stderr হ্যান্ডলার যেন I/O error না দেয়, তাই প্রথমেই সেটি রিমুভ করা হলো।
logger.remove()

# Mock external dependencies that are not installed
import importlib.machinery
from unittest.mock import MagicMock, patch


def create_mock_module(name, is_package=False):
    m = MagicMock()
    m.__spec__ = importlib.machinery.ModuleSpec(name=name, loader=MagicMock(), is_package=is_package)
    if is_package:
        m.__path__ = []
    return m


# বাংলা মন্তব্য: টেস্টে Supabase নেটওয়ার্ক রিকোয়েস্ট আটকাতে module import এর আগেই
# SUPABASE_URL ও SUPABASE_KEY খালি করা হচ্ছে। SupabaseDB.__init__() এ শর্ত আছে:
# "if self.url and self.key: create_client()" — ফলে url বা key না থাকলে create_client কল হবে না।
os.environ["SUPABASE_URL"] = ""
os.environ["SUPABASE_KEY"] = ""

sys.modules["slowapi"] = create_mock_module("slowapi", is_package=True)
sys.modules["slowapi.util"] = create_mock_module("slowapi.util")


class RateLimitExceeded(Exception):
    pass


slowapi_errors_mock = create_mock_module("slowapi.errors")
slowapi_errors_mock.RateLimitExceeded = RateLimitExceeded
sys.modules["slowapi.errors"] = slowapi_errors_mock
sys.modules["pinecone"] = create_mock_module("pinecone", is_package=True)
sys.modules["chromadb"] = create_mock_module("chromadb", is_package=True)
sys.modules["chromadb.config"] = create_mock_module("chromadb.config")
sys.modules["chromadb.utils"] = create_mock_module("chromadb.utils", is_package=True)
sys.modules["chromadb.utils.embedding_functions"] = create_mock_module("chromadb.utils.embedding_functions")
sys.modules["cachetools"] = create_mock_module("cachetools", is_package=True)
sys.modules["nats"] = create_mock_module("nats", is_package=True)
sys.modules["nats.aio"] = create_mock_module("nats.aio", is_package=True)
sys.modules["nats.aio.client"] = create_mock_module("nats.aio.client")
sys.modules["nats.errors"] = create_mock_module("nats.errors")
sys.modules["docker"] = create_mock_module("docker", is_package=True)
sys.modules["docker.errors"] = create_mock_module("docker.errors")

# ✅ SECURITY: Use explicit test-only placeholders that cannot be mistaken for real credentials.
os.environ["SUPREMEAI_ENCRYPTION_KEY"] = "TEST_ONLY_SUPREMEAI_ENCRYPTION_KEY_DO_NOT_USE_IN_PROD"
os.environ["ENCRYPTION_KEY"] = "TEST_ONLY_ENCRYPTION_KEY_DO_NOT_USE_IN_PROD"
os.environ["STRIPE_API_KEY"] = "TEST_ONLY_STRIPE_API_KEY"
os.environ["STRIPE_WEBHOOK_SECRET"] = "TEST_ONLY_STRIPE_WEBHOOK_SECRET"
os.environ["OPENROUTER_API_KEY"] = "TEST_ONLY_OPENROUTER_API_KEY"
os.environ["GEMINI_API_KEY"] = "TEST_ONLY_GEMINI_API_KEY"
os.environ["CI_WEBHOOK_SECRET"] = "TEST_ONLY_CI_WEBHOOK_SECRET"
os.environ["ENV"] = "test"
os.environ["DOCS_PASSWORD"] = "dummy_pass"
os.environ["SUPREMEAI_ADMIN_PASSWORD_HASH"] = "dummy_admin_hash"
import sys

import matplotlib

matplotlib.use("Agg")


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
# Also add repository root and scripts/ directory so tests can import moved modules
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SCRIPTS_DIR = os.path.join(REPO_ROOT, "scripts")
if REPO_ROOT not in sys.path:
    sys.path.append(REPO_ROOT)
if os.path.isdir(SCRIPTS_DIR) and SCRIPTS_DIR not in sys.path:
    sys.path.append(SCRIPTS_DIR)
os.environ.setdefault("OPENROUTER_API_KEY", "mock-key-value")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:3000,http://localhost:8000")

# বাংলা মন্তব্য: টেস্ট রান করার সময় রিয়াল ডাটাবেস এড়াতে এবং লক হওয়া রোধ করতে ইন-মেমোরি ডাটাবেস সেট করা হলো
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["SUPABASE_DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["SUPABASE_DATABASE_URL_POOLER"] = "sqlite+aiosqlite:///:memory:"

# বাংলা মন্তব্য: env var সেট হওয়ার পরে settings._cached_secrets ক্লিয়ার করা হচ্ছে।
# এটা না করলে settings.supabase_url পুরানো ক্যাশড মান return করতে পারে,
# যার ফলে create_client() রিয়াল Supabase URL-এ নেটওয়ার্ক রিকোয়েস্ট পাঠাবে।
try:
    from core.config import secret_vault, settings

    settings._cached_secrets.clear()
    secret_vault.invalidate_cache()
except Exception as e:
    import warnings

    # বাংলা মন্তব্য: B028 ফিক্স — stacklevel=2 যোগ করা হয়েছে যাতে warning সঠিক caller লাইন দেখায়
    warnings.warn(
        f"Failed to clear settings caches during test setup: {e}",
        UserWarning,
        stacklevel=2,
    )


# Mock Google Auth credentials and services globally during tests


try:
    import google.auth

    google.auth.default = lambda *args, **kwargs: (MagicMock(), "mock-project-id")
except ImportError:
    sys.modules["google.auth"] = MagicMock()

try:
    import google.cloud.firestore

    google.cloud.firestore.Client = MagicMock
except ImportError:
    sys.modules["google.cloud.firestore"] = MagicMock()

try:
    import google.cloud.secretmanager

    google.cloud.secretmanager.SecretManagerServiceClient = MagicMock
except ImportError:
    sys.modules["google.cloud.secretmanager"] = MagicMock()

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/dev/null"


import pytest

from core.security.rbac import RoleBasedAccessControl

_TEST_ENV_DEFAULTS = {
    "ENV": "test",
    "OPENROUTER_API_KEY": "TEST_ONLY_OPENROUTER_API_KEY",
    "HF_API_KEY": "TEST_ONLY_HF_API_KEY",
    "GEMINI_API_KEY": "TEST_ONLY_GEMINI_API_KEY",
    "DEEPSEEK_API_KEY": "TEST_ONLY_DEEPSEEK_API_KEY",
    "GROQ_API_KEY": "TEST_ONLY_GROQ_API_KEY",
    "NVIDIA_API_KEY": "TEST_ONLY_NVIDIA_API_KEY",
    "FIRECRAWL_API_KEY": "TEST_ONLY_FIRECRAWL_API_KEY",
    "OLLAMA_URL": "http://127.0.0.1:11434",
    "SUPREMEAI_API_TOKEN": "",
    "SENTRY_DSN": "",
    "GCP_PROJECT_ID": "",
    "GCP_REGION": "",
    "SUPABASE_DATABASE_URL": "sqlite+aiosqlite:///:memory:",
    "SUPABASE_DATABASE_URL_POOLER": "sqlite+aiosqlite:///:memory:",
    "GITHUB_TOKEN": "TEST_ONLY_GITHUB_TOKEN",
    "RENDER_API_KEY": "TEST_ONLY_RENDER_API_KEY",
    "ADMIN_AUTHORIZED": "false",
    "RAILWAY_TOKEN": "TEST_ONLY_RAILWAY_TOKEN",
    "ORACLE_CLOUD_API_KEY": "TEST_ONLY_ORACLE_CLOUD_API_KEY",
    "AUTOFIX_AUTHORIZED": "false",
    "EXPERIENCE_DB_PATH": f"data/test_experience_{os.getpid()}.db",
    "LITELLM_DISABLE_ASYNC_CLIENT_CLEANUP": "True",
}


@pytest.fixture
def rbac():
    return RoleBasedAccessControl()


@pytest.fixture(autouse=True)
def isolate_env(monkeypatch: pytest.MonkeyPatch):
    import core.config

    for key, value in _TEST_ENV_DEFAULTS.items():
        monkeypatch.setenv(key, value)
        try:
            import brain.model_router

            if hasattr(brain.model_router.ModelRouter, "_breakers"):
                brain.model_router.ModelRouter._breakers.clear()
        except ImportError:
            pass
        try:
            if hasattr(core.config.settings, key.lower()):
                setattr(core.config.settings, key.lower(), value)
            elif hasattr(core.config.settings, key):
                setattr(core.config.settings, key, value)
            elif getattr(core.config.settings.model_config, "extra", "ignore") == "allow":
                setattr(core.config.settings, key.lower(), value)
        except AttributeError:
            pass


@pytest.fixture(autouse=True)
def override_auth():
    from api.dependencies import get_current_user_token, verify_autonomous_agent_token
    from core.app import app

    app.dependency_overrides[get_current_user_token] = lambda: {
        "sub": "test_admin@supremeai.com",
        "role": "admin",
    }
    app.dependency_overrides[verify_autonomous_agent_token] = lambda: {
        "sub": "test_admin@supremeai.com",
        "role": "admin",
    }
    yield
    app.dependency_overrides = {}


@pytest.fixture(autouse=True)
def configure_litellm():
    """টেস্টের জন্য litellm সেটিংস কনফিগার করুন"""
    # বাংলা মন্তব্য: লিটেলএলএম প্রক্সি এবং টেলিমেট্রি সেটিংস নিশ্চিত করা
    try:
        import threading

        result = {}

        def _import():
            try:
                import litellm

                result["module"] = litellm
            except Exception as e:  # noqa: BLE001
                result["error"] = e

        t = threading.Thread(target=_import, daemon=True)
        t.start()
        t.join(timeout=8)
        if t.is_alive():
            import logging

            logging.warning("litellm import timed out; skipping configuration")
        elif "error" in result:
            import logging

            logging.warning(f"Exception suppressed: {result['error']}")
        else:
            litellm = result["module"]
            litellm.use_litellm_proxy = False
            litellm.drop_params = True
            litellm.telemetry = False
    except Exception as e:  # noqa: BLE001
        import logging

        logging.warning(f"Exception suppressed: {e}")
    yield


@pytest.fixture
def mock_production_env(monkeypatch):
    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-mock-123")
    monkeypatch.setenv("GEMINI_API_KEY", "mock-key")


import pytest_asyncio

pytest_plugins = ["pytest_asyncio"]


# ✅ FIXED: anyio's built-in `anyio_backend` fixture defaults to module scope, which is
# narrower than our session-scoped `setup_test_database` fixture below. Any anyio-marked
# async test then fails at setup with:
#   "ScopeMismatch: You tried to access the module scoped fixture anyio_backend
#    with a session scoped request object."
# Overriding `anyio_backend` here at session scope (the standard anyio fix for this
# exact conflict) resolves it for every @pytest.mark.anyio test in the suite.
@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest_asyncio.fixture(autouse=True, scope="session")  # বাংলা: টেস্ট রান টাইম কমাতে session scope ব্যবহার করা হচ্ছে
async def setup_test_database():
    import sqlalchemy.dialects.sqlite as sqlite_dialect  # noqa: F401
    from sqlalchemy.dialects.postgresql import JSONB
    from sqlalchemy.ext.compiler import compiles
    from sqlalchemy.types import JSON  # noqa: F401

    @compiles(JSONB, "sqlite")
    def compile_jsonb_sqlite(type_, compiler, **kw):
        return "JSON"

    from database.session import engine
    from models.base import Base

    # বাংলা মন্তব্য: সব মডেল স্পষ্টভাবে ইম্পোর্ট করা হলো যাতে Base.metadata তে রেজিস্ট্রি হয়
    # বাংলা: wallet.py তে UserWallet ও TransactionLedgerEntry (SQLAlchemy) আছে — সরাসরি ইম্পোর্ট করো

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)  # à¦ªà¦°à¦¿à¦·à§à¦•à¦¾à¦° à¦¶à§à¦°à§ à¦¨à¦¿à¦¶à§à¦šà¦¿à¦¤ à¦•à¦°à¦¤à§‡
        try:
            await conn.run_sync(Base.metadata.create_all)  # à¦¸à¦¬ à¦Ÿà§‡à¦¬à¦¿à¦² à¦¤à§ˆà¦°à¦¿
        except Exception as e:  # noqa: BLE001
            import warnings

            warnings.warn(f"Test database setup skipped due to schema issue: {e}", stacklevel=2)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def async_session():
    from unittest.mock import AsyncMock

    yield AsyncMock()


@pytest.fixture(autouse=True)
def clear_settings_cache():
    """Clear cached secrets before each test to prevent test bleed."""
    import os

    from core.config import secret_vault, settings

    settings._cached_secrets.clear()
    secret_vault.invalidate_cache()

    # Many tests mutate os.environ without cleaning up
    # MUST set to "" instead of del, otherwise secret_vault will mock it with "mock_SUPREMEAI_API_TOKEN"
    os.environ["SUPREMEAI_API_TOKEN"] = ""
    yield


@pytest.fixture(autouse=True)
def mock_supabase():
    # বাংলা মন্তব্য: Supabase নেটওয়ার্ক লিক সম্পূর্ণ বন্ধ করা হলো।
    # create_client মক করার পাশাপাশি settings-এ supabase_url/key খালি রেখে
    # যেকোনো রিয়েল নেটওয়ার্ক রিকোয়েস্ট আটকানো হচ্ছে।
    import os
    from unittest.mock import MagicMock

    # নিশ্চিত করো env-এ URL/KEY নেই যাতে create_client কল না হয়
    old_url = os.environ.get("SUPABASE_URL", "")
    old_key = os.environ.get("SUPABASE_KEY", "")
    os.environ["SUPABASE_URL"] = ""
    os.environ["SUPABASE_KEY"] = ""

    with (
        patch("database.supabase_client.create_client") as mock_create,
        patch("database.supabase_client.SupabaseDB.__init__", return_value=None) as mock_init,
    ):
        mock_db = MagicMock()
        mock_db.client = MagicMock()
        mock_create.return_value = mock_db.client
        yield mock_create

    # টেস্টের পর env পুনরুদ্ধার
    if old_url:
        os.environ["SUPABASE_URL"] = old_url
    if old_key:
        os.environ["SUPABASE_KEY"] = old_key


@pytest.fixture(autouse=True)
def mock_network():
    # সব ধরণের আউটগোয়িং নেটওয়ার্ক কল ব্লক করুন
    import respx

    with respx.mock(base_url="https://mock.supabase.co", assert_all_mocked=False) as respx_mock:
        yield respx_mock

```

### 📄 `backend/tests/mock_dataset.jsonl`

```jsonl
{"prompt": "hello", "completion": "world"}
```

### 📄 `backend/tests/test_adaptive_engine.py`

```py
from unittest.mock import MagicMock

import pytest

from adaptive_engine.experience_db import Experience, ExperienceDatabase
from adaptive_engine.intent_parser import IntentParser
from adaptive_engine.platform_learner import PlatformLearner
from adaptive_engine.registry import PlatformProfile, PlatformRegistry


def test_platform_registry():
    registry = PlatformRegistry()

    # Check preloaded
    github = registry.get_platform("github")
    assert github is not None
    assert github.display_name == "GitHub"
    assert "oauth2" in github.auth_methods

    # Register new
    new_profile = PlatformProfile(
        name="customcloud",
        display_name="Custom Cloud",
        category="cloud",
        auth_methods=["api_key"],
        capabilities=["compute"],
        deploy_methods=["api"],
    )
    registry.register_platform(new_profile)

    retrieved = registry.get_platform("customcloud")
    assert retrieved is not None
    assert retrieved.display_name == "Custom Cloud"


def test_intent_parser():
    fake_router = MagicMock()
    fake_router.route_and_generate.return_value = {
        "text": """
        {
          "app_type": "blog",
          "features": ["auth", "comments"],
          "tech_stack": {"frontend": "react", "backend": "fastapi"},
          "pages": ["home", "detail"],
          "integrations": [],
          "deployment_target": "vercel",
          "clarification_question": null
        }
        """
    }

    parser = IntentParser(fake_router)
    spec = parser.parse_intent("I want a react blog deployed to Vercel")

    assert spec.app_type == "blog"
    assert "auth" in spec.features
    assert spec.tech_stack["frontend"] == "react"
    assert spec.deployment_target == "vercel"


def test_experience_db(tmp_path):
    db_file = tmp_path / "test_experience.db"
    db = ExperienceDatabase(db_path=str(db_file))

    exp = Experience(
        user_id="user-123",
        request="I want a blog",
        context={"app_type": "blog"},
        action_taken="Code generation",
        result="success",
        what_worked=["parsed"],
        what_failed=[],
    )

    row_id = db.record_experience(exp)
    assert row_id > 0

    list_exp = db.get_experiences()
    assert len(list_exp) == 1
    assert list_exp[0].user_id == "user-123"
    assert list_exp[0].context["app_type"] == "blog"


@pytest.mark.anyio
async def test_platform_learner():
    fake_router = MagicMock()

    # Mock async_route_and_generate
    async def mock_async_route_and_generate(*args, **kwargs):
        return {
            "text": """
            {
              "display_name": "Cool Cloud",
              "category": "cloud",
              "auth_methods": ["oauth2"],
              "capabilities": ["hosting"],
              "deploy_methods": ["git_push"],
              "sdk_code": "class CoolCloudClient:\\n    pass",
              "api_endpoints": {"deploy": "/v1/deploy"}
            }
            """
        }

    fake_router.async_route_and_generate = mock_async_route_and_generate

    registry = PlatformRegistry()
    learner = PlatformLearner(fake_router, registry)

    profile = await learner.learn_from_docs("coolcloud", "https://docs.coolcloud.io")
    assert profile.display_name == "Cool Cloud"
    assert "oauth2" in profile.auth_methods
    assert "hosting" in profile.capabilities

    # Check it is in registry
    assert registry.get_platform("coolcloud") is not None

```

### 📄 `backend/tests/test_admin_dashboard_coverage.py`

```py
"""Tests to improve coverage for admin_dashboard routes (17.6% -> target 60%)."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from api.routes.admin_dashboard import (
    _in_memory_jwt_blacklist,
    admin_rate_limit,
    require_admin_token,
)


class TestRequireAdminToken:
    """Tests for require_admin_token dependency."""

    def test_valid_admin_token(self):
        """Valid admin JWT should be accepted."""
        from jose import jwt

        from core.config import settings

        payload = {"uid": "admin-user", "role": "admin", "jti": "token-123"}
        token = jwt.encode(payload, settings.jwt_secret, algorithm="HS256")

        result = require_admin_token(HTTPAuthorizationCredentials(credentials=token, scheme="Bearer"))
        assert result["uid"] == "admin-user"
        assert result["role"] == "admin"

    def test_non_admin_role_raises_401(self):
        """Token without admin role must be rejected with 401."""
        from jose import jwt

        from core.config import settings

        payload = {"uid": "user", "role": "user"}
        token = jwt.encode(payload, settings.jwt_secret, algorithm="HS256")

        with pytest.raises(HTTPException) as exc_info:
            require_admin_token(HTTPAuthorizationCredentials(credentials=token, scheme="Bearer"))

        assert exc_info.value.status_code == 401

    def test_revoked_jti_raises_401(self):
        """Revoked jti must raise 401 from in-memory blacklist."""
        from jose import jwt

        from core.config import settings

        payload = {"uid": "admin", "role": "admin", "jti": "revoked-token"}
        token = jwt.encode(payload, settings.jwt_secret, algorithm="HS256")

        _in_memory_jwt_blacklist.add("revoked-token")
        try:
            with pytest.raises(HTTPException) as exc_info:
                require_admin_token(HTTPAuthorizationCredentials(credentials=token, scheme="Bearer"))
            assert exc_info.value.status_code == 401
        finally:
            _in_memory_jwt_blacklist.discard("revoked-token")

    def test_invalid_token_raises_401(self):
        """Malformed token should raise 401."""
        with pytest.raises(HTTPException) as exc_info:
            require_admin_token(HTTPAuthorizationCredentials(credentials="not-a-valid-token", scheme="Bearer"))
        assert exc_info.value.status_code == 401

    def test_fallback_api_token_auth(self):
        """SupremeAI API token fallback auth succeeds."""
        from core.config import settings

        expected = getattr(settings, "supremeai_api_token", None)
        if not expected:
            pytest.skip("supremeai_api_token not configured")

        with patch("api.routes.admin_dashboard.jwt.decode", side_effect=Exception("bad")):
            result = require_admin_token(HTTPAuthorizationCredentials(credentials=expected, scheme="Bearer"))
        assert result["role"] == "admin"


class TestAdminRateLimit:
    """Tests for admin_rate_limit dependency."""

    def test_rate_limit_allows_request(self):
        """Request within limit should pass."""
        from fastapi import Request

        request = MagicMock(spec=Request)
        request.client.host = "127.0.0.1"

        with patch("core.services.redis_queue", new=MagicMock(configured=False)):
            with patch("api.routes.admin_dashboard.logger"):
                admin_rate_limit(request)

    def test_rate_limit_raises_after_limit(self):
        """Exceeding rate limit should raise 429."""
        from fastapi import Request

        request = MagicMock(spec=Request)
        request.client.host = "127.0.0.1"

        fake_redis = MagicMock()
        fake_redis.configured = True
        fake_redis.get.return_value = "600"

        with patch("core.services.redis_queue", fake_redis):
            with patch("api.routes.admin_dashboard.logger"):
                with pytest.raises(HTTPException) as exc_info:
                    admin_rate_limit(request)
        assert exc_info.value.status_code == 429

```

### 📄 `backend/tests/test_admin_dashboard_full.py`

```py
"""Comprehensive tests for api/routes/admin_dashboard.py — targets 100% line + branch coverage.

Covers all endpoints and helper functions not yet tested by test_admin_dashboard_coverage.py:
  - load_users / save_users (success, file-not-found default creation, exception)
  - get_users, create_user (create + update), delete_user (found + not-found)
  - get_costs (success, no-file, exception)
  - get_health_map (various config states)
  - trigger_deploy
  - get_metrics (with/without keys, psutil ok/failed)
  - get_providers (with/without keys)
  - get_model_router, set_router_override
  - get_codebase_export (success + failure)
  - load_cost_caps / save_cost_caps / get_cost_caps / update_cost_caps
  - get_env_etag (redis cached, .env exists, .env missing, exception)
  - _acquire_env_lock / _release_env_lock (redis + file fallback)
  - logs_stream (log generator with file present/absent, cancellation)
"""

import asyncio
import json
import os
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from api.routes.admin_dashboard import (
    UserUpdate,
    RouterOverrideRequest,
    _acquire_env_lock,
    _release_env_lock,
    get_costs,
    get_cost_caps,
    get_env_etag,
    get_health_map,
    get_metrics,
    get_model_router,
    get_providers,
    get_users,
    load_cost_caps,
    load_users,
    save_cost_caps,
    save_users,
    set_router_override,
    trigger_deploy,
    update_cost_caps,
    create_user,
    delete_user,
    logs_stream,
)


# ── Helpers ────────────────────────────────────────────────────────────


@pytest.fixture
def temp_users_file(tmp_path, monkeypatch):
    """Redirect USERS_FILE to a temp directory."""
    import api.routes.admin_dashboard as mod

    users_file = str(tmp_path / "users.json")
    monkeypatch.setattr(mod, "USERS_FILE", users_file)
    return users_file


@pytest.fixture
def temp_cost_caps_file(tmp_path, monkeypatch):
    """Redirect COST_CAPS_FILE to a temp directory."""
    import api.routes.admin_dashboard as mod

    caps_file = str(tmp_path / "cost_caps.json")
    monkeypatch.setattr(mod, "COST_CAPS_FILE", caps_file)
    return caps_file


@pytest.fixture
def temp_env_file(tmp_path, monkeypatch):
    """Redirect .env and .env.lock to a temp directory."""
    env_file = str(tmp_path / ".env")
    lock_file = str(tmp_path / ".env.lock")
    monkeypatch.setattr("os.getcwd", lambda: str(tmp_path))
    return env_file, lock_file


# ── load_users / save_users ────────────────────────────────────────────


class TestLoadSaveUsers:
    def test_load_users_creates_default(self, temp_users_file):
        """File doesn't exist → creates default users and returns them."""
        users = load_users()
        assert len(users) == 3
        assert users[0]["username"] == "admin"
        assert users[1]["role"] == "Operator"
        assert os.path.exists(temp_users_file)

    def test_load_users_existing_file(self, temp_users_file):
        """File exists → loads from file."""
        with open(temp_users_file, "w") as f:
            json.dump([{"username": "custom", "role": "Admin", "permissions": ["all"]}], f)
        users = load_users()
        assert len(users) == 1
        assert users[0]["username"] == "custom"

    def test_load_users_corrupt_file(self, temp_users_file):
        """Corrupt JSON → returns empty list."""
        with open(temp_users_file, "w") as f:
            f.write("not valid json{{{")
        users = load_users()
        assert users == []

    def test_save_users(self, temp_users_file):
        """save_users writes to file."""
        users = [{"username": "test", "role": "Admin", "permissions": ["all"]}]
        save_users(users)
        with open(temp_users_file) as f:
            loaded = json.load(f)
        assert loaded == users


# ── get_users / create_user / delete_user ──────────────────────────────


class TestUserCRUD:
    def test_get_users(self, temp_users_file):
        """get_users returns loaded users."""
        result = get_users()
        assert len(result) == 3
        assert result[0]["username"] == "admin"

    def test_create_user_new(self, temp_users_file):
        """Creating a new user adds them."""
        user = UserUpdate(username="newuser", role="Operator", permissions=["read"])
        result = create_user(user)
        assert result["status"] == "success"
        assert "created" in result["message"]
        users = load_users()
        assert any(u["username"] == "newuser" for u in users)

    def test_create_user_updates_existing(self, temp_users_file):
        """Creating an existing user updates them."""
        user = UserUpdate(username="admin", role="SuperAdmin", permissions=["all", "delete"])
        result = create_user(user)
        assert result["status"] == "success"
        assert "updated" in result["message"]
        users = load_users()
        admin = [u for u in users if u["username"] == "admin"][0]
        assert admin["role"] == "SuperAdmin"

    def test_delete_user_found(self, temp_users_file):
        """Deleting an existing user succeeds."""
        result = delete_user("admin")
        assert result["status"] == "success"
        users = load_users()
        assert not any(u["username"] == "admin" for u in users)

    def test_delete_user_not_found(self, temp_users_file):
        """Deleting a non-existent user raises 404."""
        with pytest.raises(HTTPException) as exc_info:
            delete_user("nonexistent")
        assert exc_info.value.status_code == 404


# ── get_costs ──────────────────────────────────────────────────────────


class TestGetCosts:
    def test_get_costs_no_report_file(self, tmp_path, monkeypatch):
        """CostAuditor returns no text_report → returns unavailable message."""
        with patch("api.routes.admin_dashboard.CostAuditor") as mock_cls:
            mock_auditor = MagicMock()
            mock_auditor.generate_report.return_value = {"text_report": str(tmp_path / "nonexistent.md")}
            mock_cls.return_value = mock_auditor
            result = get_costs()
        assert result["status"] == "ok"
        assert "Unavailable" in result["report"]

    def test_get_costs_with_report_file(self, tmp_path, monkeypatch):
        """CostAuditor returns a valid report path → reads and returns content."""
        report_file = tmp_path / "cost_report.md"
        report_file.write_text("# Cost Report\nSome content")
        with patch("api.routes.admin_dashboard.CostAuditor") as mock_cls:
            mock_auditor = MagicMock()
            mock_auditor.generate_report.return_value = {"text_report": str(report_file)}
            mock_cls.return_value = mock_auditor
            result = get_costs()
        assert result["status"] == "ok"
        assert "# Cost Report" in result["report"]

    def test_get_costs_exception(self):
        """CostAuditor raises → returns error status."""
        with patch("api.routes.admin_dashboard.CostAuditor") as mock_cls:
            mock_auditor = MagicMock()
            mock_auditor.generate_report.side_effect = RuntimeError("DB error")
            mock_cls.return_value = mock_auditor
            result = get_costs()
        assert result["status"] == "error"
        assert "DB error" in result["report"]


# ── get_health_map ─────────────────────────────────────────────────────


class TestGetHealthMap:
    def test_all_offline(self, monkeypatch):
        """No services configured → all offline."""
        from core.config import settings

        monkeypatch.setattr(settings, "gcp_project_id", None)
        monkeypatch.setattr(settings, "upstash_redis_rest_url", None)
        monkeypatch.setattr(settings, "supabase_database_url", None)
        result = get_health_map()
        assert result["gcp"]["status"] == "offline"
        assert result["railway"]["status"] == "offline"
        assert result["render"]["status"] == "offline"

    def test_all_healthy(self, monkeypatch):
        """All services configured → all healthy."""
        from core.config import settings

        monkeypatch.setattr(settings, "gcp_project_id", "my-project")
        monkeypatch.setattr(settings, "gcp_region", "us-east1")
        monkeypatch.setattr(settings, "upstash_redis_rest_url", "https://redis.upstash.com")
        monkeypatch.setattr(settings, "supabase_database_url", "postgresql://db")
        result = get_health_map()
        assert result["gcp"]["status"] == "healthy"
        assert result["railway"]["status"] == "healthy"
        assert result["render"]["status"] == "healthy"
        assert result["gcp"]["latency"] == "42ms"
        assert result["railway"]["latency"] == "78ms"
        assert result["render"]["latency"] == "120ms"


# ── trigger_deploy ─────────────────────────────────────────────────────


class TestTriggerDeploy:
    def test_trigger_deploy(self):
        """Deploy trigger returns success."""
        result = trigger_deploy()
        assert result["status"] == "success"
        assert "triggered" in result["message"]


# ── get_metrics ────────────────────────────────────────────────────────


class TestGetMetrics:
    def test_metrics_with_keys(self, monkeypatch):
        """All API keys set → all providers active."""
        from core.config import settings

        monkeypatch.setattr(settings, "openrouter_api_key", "key1")
        monkeypatch.setattr(settings, "gemini_api_key", "key2")
        monkeypatch.setattr(settings, "groq_api_key", "key3")
        monkeypatch.setattr(settings, "deepseek_api_key", "key4")
        result = get_metrics()
        assert "openrouter" in result["active_providers"]
        assert "gemini" in result["active_providers"]
        assert "groq" in result["active_providers"]
        assert "deepseek" in result["active_providers"]
        assert result["cpu_usage_percent"] >= 0

    def test_metrics_no_keys(self, monkeypatch):
        """No API keys → falls back to ollama."""
        from core.config import settings

        monkeypatch.setattr(settings, "openrouter_api_key", None)
        monkeypatch.setattr(settings, "gemini_api_key", None)
        monkeypatch.setattr(settings, "groq_api_key", None)
        monkeypatch.setattr(settings, "deepseek_api_key", None)
        result = get_metrics()
        assert result["active_providers"] == ["ollama"]
        assert result["model_call_distribution"] == {"ollama": 100}

    def test_metrics_psutil_failure(self, monkeypatch):
        """psutil fails → uses fallback values."""
        from core.config import settings

        monkeypatch.setattr(settings, "openrouter_api_key", "key1")
        monkeypatch.setattr(settings, "gemini_api_key", None)
        monkeypatch.setattr(settings, "groq_api_key", None)
        monkeypatch.setattr(settings, "deepseek_api_key", None)
        with patch("api.routes.admin_dashboard.psutil", create=True) as mock_psutil:
            mock_psutil.cpu_percent.side_effect = RuntimeError("psutil broken")
            result = get_metrics()
        assert result["cpu_usage_percent"] == 22.4
        assert result["memory_usage_percent"] == 45.2
        assert result["gpu_usage_percent"] == 12.0


# ── get_providers ──────────────────────────────────────────────────────


class TestGetProviders:
    def test_providers_with_keys(self, monkeypatch):
        """API keys set → providers listed."""
        from core.config import settings

        monkeypatch.setattr(settings, "openrouter_api_key", "key1")
        monkeypatch.setattr(settings, "gemini_api_key", "key2")
        monkeypatch.setattr(settings, "groq_api_key", None)
        monkeypatch.setattr(settings, "deepseek_api_key", None)
        result = get_providers()
        assert len(result) == 2
        assert result[0]["id"] == "openrouter"
        assert result[1]["id"] == "gemini"

    def test_providers_no_keys(self, monkeypatch):
        """No API keys → falls back to ollama."""
        from core.config import settings

        monkeypatch.setattr(settings, "openrouter_api_key", None)
        monkeypatch.setattr(settings, "gemini_api_key", None)
        monkeypatch.setattr(settings, "groq_api_key", None)
        monkeypatch.setattr(settings, "deepseek_api_key", None)
        result = get_providers()
        assert len(result) == 1
        assert result[0]["id"] == "ollama"


# ── get_model_router / set_router_override ─────────────────────────────


class TestModelRouter:
    def test_get_model_router(self):
        """Returns default router state."""
        result = get_model_router()
        assert result["current_override"] is None
        assert result["ab_test_active"] is False
        assert "openrouter" in result["provider_order"]

    def test_set_router_override(self):
        """Sets override and returns success."""
        payload = RouterOverrideRequest(provider="openrouter", model="gpt-4o", remaining_requests=100)
        result = set_router_override(payload)
        assert result["status"] == "success"
        assert result["override"]["provider"] == "openrouter"
        assert result["override"]["remaining"] == 100


# ── get_codebase_export ────────────────────────────────────────────────


class TestCodebaseExport:
    def test_export_success(self):
        """Export succeeds → returns markdown."""
        with patch("api.routes.admin_dashboard.export_codebase_to_markdown") as mock_export:
            mock_export.return_value = "# Codebase\nSome markdown"
            result = get_codebase_export()
        assert result["success"] is True
        assert "# Codebase" in result["markdown"]

    def test_export_failure(self):
        """Export fails → raises HTTPException 500."""
        with patch("api.routes.admin_dashboard.export_codebase_to_markdown") as mock_export:
            mock_export.side_effect = RuntimeError("Export failed")
            with pytest.raises(HTTPException) as exc_info:
                get_codebase_export()
        assert exc_info.value.status_code == 500


# ── load_cost_caps / save_cost_caps / get_cost_caps / update_cost_caps ─


class TestCostCaps:
    def test_load_cost_caps_creates_default(self, temp_cost_caps_file):
        """File doesn't exist → creates default caps."""
        caps = load_cost_caps()
        assert "default_cap" in caps
        assert caps["default_cap"] == 10.0
        assert os.path.exists(temp_cost_caps_file)

    def test_load_cost_caps_existing(self, temp_cost_caps_file):
        """File exists → loads from file."""
        with open(temp_cost_caps_file, "w") as f:
            json.dump({"default_cap": 50.0, "per_tenant": {"t1": 10.0}}, f)
        caps = load_cost_caps()
        assert caps["default_cap"] == 50.0
        assert caps["per_tenant"]["t1"] == 10.0

    def test_save_cost_caps(self, temp_cost_caps_file):
        """save_cost_caps writes to file."""
        caps = {"default_cap": 100.0, "per_tenant": {}}
        save_cost_caps(caps)
        with open(temp_cost_caps_file) as f:
            loaded = json.load(f)
        assert loaded == caps

    def test_get_cost_caps(self, temp_cost_caps_file):
        """get_cost_caps returns loaded caps."""
        result = get_cost_caps()
        assert "default_cap" in result

    def test_update_cost_caps(self, temp_cost_caps_file):
        """update_cost_caps merges and saves."""
        payload = {"new_cap": 200.0}
        result = update_cost_caps(payload)
        assert result["status"] == "success"
        assert result["caps"]["new_cap"] == 200.0
        assert result["caps"]["default_cap"] == 10.0  # original preserved


# ── get_env_etag ───────────────────────────────────────────────────────


class TestGetEnvEtag:
    def test_env_etag_redis_cached(self):
        """Redis has cached etag → returns it."""
        import core.services as app_mod

        mock_redis = MagicMock()
        mock_redis.configured = True
        mock_redis.get.return_value = "cached-etag"
        old = getattr(app_mod, "redis_queue", None)
        app_mod.redis_queue = mock_redis
        try:
            result = get_env_etag()
            assert result == "cached-etag"
        finally:
            app_mod.redis_queue = old

    def test_env_etag_no_redis_no_env_file(self):
        """No redis, no .env file → returns 'empty-env'."""
        import core.services as app_mod

        old = getattr(app_mod, "redis_queue", None)
        app_mod.redis_queue = None
        try:
            with patch("os.path.exists", return_value=False):
                result = get_env_etag()
            assert result == "empty-env"
        finally:
            app_mod.redis_queue = old

    def test_env_etag_redis_not_configured(self):
        """Redis exists but not configured → falls back to .env file."""
        import core.services as app_mod

        mock_redis = MagicMock()
        mock_redis.configured = False
        old = getattr(app_mod, "redis_queue", None)
        app_mod.redis_queue = mock_redis
        try:
            with patch("os.path.exists", return_value=False):
                result = get_env_etag()
            assert result == "empty-env"
        finally:
            app_mod.redis_queue = old


# ── _acquire_env_lock / _release_env_lock ──────────────────────────────


class TestEnvLock:
    def test_acquire_redis_lock(self):
        """Redis lock acquired → returns True."""
        import core.services as app_mod

        mock_redis = MagicMock()
        mock_redis.configured = True
        mock_redis.set_nx.return_value = True
        old = getattr(app_mod, "redis_queue", None)
        app_mod.redis_queue = mock_redis
        try:
            result = _acquire_env_lock()
            assert result is True
            mock_redis.set_nx.assert_called_once()
        finally:
            app_mod.redis_queue = old

    def test_acquire_redis_fails_fallback_file(self, tmp_path):
        """Redis lock fails → falls back to file lock."""
        import core.services as app_mod

        mock_redis = MagicMock()
        mock_redis.configured = True
        mock_redis.set_nx.side_effect = RuntimeError("redis down")
        old = getattr(app_mod, "redis_queue", None)
        app_mod.redis_queue = mock_redis
        lock_path = str(tmp_path / ".env.lock")
        try:
            result = _acquire_env_lock(lock_path=lock_path)
            assert result is True
            assert os.path.exists(lock_path)
        finally:
            app_mod.redis_queue = old
            if os.path.exists(lock_path):
                os.remove(lock_path)

    def test_acquire_file_exists(self, tmp_path):
        """File lock already exists → returns False."""
        lock_path = str(tmp_path / ".env.lock")
        with open(lock_path, "w") as f:
            f.write("locked")
        result = _acquire_env_lock(lock_path=lock_path)
        assert result is False

    def test_acquire_no_redis_file_lock(self, tmp_path):
        """No redis → uses file lock."""
        import core.services as app_mod

        old = getattr(app_mod, "redis_queue", None)
        app_mod.redis_queue = None
        lock_path = str(tmp_path / ".env.lock")
        try:
            result = _acquire_env_lock(lock_path=lock_path)
            assert result is True
        finally:
            app_mod.redis_queue = old
            if os.path.exists(lock_path):
                os.remove(lock_path)

    def test_release_lock_redis(self):
        """Release lock with redis configured."""
        import core.services as app_mod

        mock_redis = MagicMock()
        mock_redis.configured = True
        old = getattr(app_mod, "redis_queue", None)
        app_mod.redis_queue = mock_redis
        try:
            _release_env_lock()
            mock_redis._request.assert_called_once_with("DEL", "lock:env_write")
        finally:
            app_mod.redis_queue = old

    def test_release_lock_no_redis(self, tmp_path):
        """Release lock without redis → tries to remove file."""
        import core.services as app_mod

        old = getattr(app_mod, "redis_queue", None)
        app_mod.redis_queue = None
        lock_path = str(tmp_path / ".env.lock")
        with open(lock_path, "w") as f:
            f.write("locked")
        try:
            _release_env_lock(lock_path=lock_path)
            assert not os.path.exists(lock_path)
        finally:
            app_mod.redis_queue = old


# ── logs_stream ────────────────────────────────────────────────────────


class TestLogsStream:
    def test_logs_stream_no_log_file(self):
        """No log file exists → returns streaming response."""
        with patch("os.path.exists", return_value=False):
            result = logs_stream()
        assert result is not None
        assert result.media_type == "text/event-stream"

    def test_logs_stream_with_log_file(self, tmp_path):
        """Log file exists → yields log lines."""
        log_file = tmp_path / "app.log"
        log_file.write_text("line1\nline2\nline3\n")
        with patch("os.path.exists", side_effect=lambda p: p == str(log_file) or p == "logs/app.log"):
            with patch("builtins.open", create=True) as mock_open:
                mock_open.return_value = MagicMock(
                    __enter__=MagicMock(
                        return_value=MagicMock(
                            readlines=MagicMock(return_value=["line1\n", "line2\n", "line3\n"]),
                            readline=MagicMock(return_value=""),
                            seek=MagicMock(),
                            close=MagicMock(),
                        )
                    ),
                    __exit__=MagicMock(return_value=False),
                )
                result = logs_stream()
        assert result is not None

    def test_logs_stream_log_generator_cancellation(self, tmp_path):
        """Log generator handles CancelledError."""
        import api.routes.admin_dashboard as mod

        async def mock_generator():
            yield "data: test\n\n"
            raise asyncio.CancelledError()

        with patch.object(mod, "StreamingResponse") as mock_sr:
            mock_sr.return_value = MagicMock()
            logs_stream()

```

### 📄 `backend/tests/test_admin_god.py`

```py
"""Admin God Layer tests for SupremeAI 2.0."""

import os
from unittest.mock import patch

import pytest

from core.admin_god import AdminGodLayer, GodModeAuditLog, GodModeContext
from core.security.rbac import UserContext


class TestGodModeAuditLog:
    """Tests for GodModeAuditLog class."""

    def test_record_creates_entry(self):
        """একটি নতুন audit entry রেকর্ড করা হচ্ছে।"""
        # Clear any existing entries
        GodModeAuditLog._entries = []

        session_id = GodModeAuditLog.record(
            actor="test_user",
            action="TEST_ACTION",
            resource="test_resource",
            reason="test_reason",
            ip_address="192.168.1.1",
        )

        assert session_id is not None
        assert len(session_id) == 32  # token_hex(16) produces 32 char string
        assert len(GodModeAuditLog._entries) == 1

    def test_record_default_ip_address(self):
        """ডিফল্ট IP ঠিক আছে।"""
        GodModeAuditLog._entries = []

        session_id = GodModeAuditLog.record(
            actor="test_user",
            action="TEST_ACTION",
            resource="test_resource",
            reason="test_reason",
        )

        assert session_id is not None
        assert GodModeAuditLog._entries[0]["ip_address"] == "unknown"

    def test_update_creates_entry(self):
        """Update মেথড একটি নতুন entry যোগ করে।"""
        GodModeAuditLog._entries = []

        session_id = GodModeAuditLog.record(
            actor="test_user",
            action="GOD_MODE_ACTIVATED",
            resource="system",
            reason="test",
        )

        GodModeAuditLog.update(session_id, "GOD_MODE_TERMINATED", 100.5)

        assert len(GodModeAuditLog._entries) == 2
        assert GodModeAuditLog._entries[1]["action"] == "GOD_MODE_TERMINATED"
        assert GodModeAuditLog._entries[1]["duration_ms"] == 100.5

    def test_update_default_duration(self):
        """Update এর ডিফল্ট duration_ms ঠিক আছে।"""
        GodModeAuditLog._entries = []

        session_id = GodModeAuditLog.record(actor="test_user", action="ACTIVATED", resource="system", reason="test")

        GodModeAuditLog.update(session_id, "TERMINATED")

        assert GodModeAuditLog._entries[1]["duration_ms"] == 0.0

    def test_get_entries_returns_copy(self):
        """get_entries মূল লিস্টের কপি রিটার্ন করে।"""
        GodModeAuditLog._entries = []

        GodModeAuditLog.record(actor="user1", action="ACTION1", resource="res1", reason="reason1")
        GodModeAuditLog.record(actor="user2", action="ACTION2", resource="res2", reason="reason2")

        entries = GodModeAuditLog.get_entries()
        assert len(entries) == 2

        # Modify the returned list
        entries.append({"test": "modified"})

        # Original should be unchanged
        assert len(GodModeAuditLog.get_entries()) == 2

    def test_entry_structure(self):
        """Entry-এর structure সঠিক।"""
        GodModeAuditLog._entries = []

        GodModeAuditLog.record(
            actor="test_actor",
            action="TEST_ACTION",
            resource="test_resource",
            reason="test_reason",
            ip_address="10.0.0.1",
        )

        entry = GodModeAuditLog._entries[0]
        assert entry["session_id"] is not None
        assert entry["actor"] == "test_actor"
        assert entry["action"] == "TEST_ACTION"
        assert entry["resource"] == "test_resource"
        assert entry["reason"] == "test_reason"
        assert entry["ip_address"] == "10.0.0.1"
        assert "timestamp" in entry


class TestGodModeContext:
    """Tests for GodModeContext class."""

    def test_context_creation(self):
        """GodModeContext সঠিকভাবে তৈরি হয়।"""
        ctx = GodModeContext(session_id="test_session_123")

        assert ctx.session_id == "test_session_123"

    def test_context_session_id_type(self):
        """Session ID স্ট্রিং টাইপ হয়।"""
        ctx = GodModeContext(session_id="abc123xyz")

        assert isinstance(ctx.session_id, str)


class TestAdminGodLayer:
    """Tests for AdminGodLayer enforcement and constraint injection."""

    @patch.dict(os.environ, {"SUPREMEAI_ADMIN_PASSWORD_HASH": ""})
    def test_init_default(self):
        """ডিফল্ট ইনিশialization ঠিক আছে।"""
        layer = AdminGodLayer()
        assert layer.rules_engine is not None
        assert layer.rbac is not None
        assert layer.admin_password_hash == ""

    def test_init_with_custom_rules_engine(self):
        """কাস্টম রুলস ইঞ্জিন সহ ইনিশialization করা হচ্ছে।"""
        from core.universal_rules import UniversalRulesEngine

        custom_engine = UniversalRulesEngine()
        layer = AdminGodLayer(rules_engine=custom_engine)
        assert layer.rules_engine is custom_engine

    def test_verify_admin_no_password(self):
        """খালি পাসওয়ার্ড রিজেক্স করা হচ্ছে।"""
        layer = AdminGodLayer()
        assert layer.verify_admin("") is False
        assert layer.verify_admin(None) is False

    def test_verify_admin_no_hash(self):
        """অ্যাডমিন হ্যাশ ছাড়াই ভেরিফিকেশন ব্যর্থ হয়।"""
        layer = AdminGodLayer.__new__(AdminGodLayer)
        layer.admin_password_hash = ""
        layer.rules_engine = None
        layer.rbac = None
        assert layer.verify_admin("password") is False

    def test_enforce_no_user_context(self):
        """UserContext ছাড়াই enforce করলে ডিফল্ট ভিউয়ার রোল ব্যবহার হয়।"""
        layer = AdminGodLayer()
        ctx = UserContext(user_id="test-user", role="admin")
        result = layer.enforce("read", ctx)
        assert result["allowed"] is True
        assert result["role"] == "admin"

    def test_enforce_with_string_context(self):
        """স্ট্রিং রোল সহ UserContext তৈরি করে enforce করা হচ্ছে।"""
        layer = AdminGodLayer()
        result = layer.enforce("read", "admin")
        assert result["allowed"] is True
        assert result["role"] == "admin"

    def test_enforce_with_none_context(self):
        """None কন্টেক্সটে ডিফল্ট ভিউয়ার রোল ব্যবহার হয়।"""
        from core.security.rbac import PermissionDeniedError

        layer = AdminGodLayer()
        # This raises PermissionDeniedError for permission denied
        with pytest.raises(PermissionDeniedError):
            layer.enforce("admin", None)

    def test_enforce_permission_denied(self):
        """অনুমতি ছাড়াই enforce করলে PermissionDeniedError দেওয়া হয়।"""
        from core.security.rbac import PermissionDeniedError

        layer = AdminGodLayer()
        ctx = UserContext(user_id="test-user", role="viewer")
        # The actual error message is "Role 'viewer' lacks permission for 'admin'"
        with pytest.raises(PermissionDeniedError, match="lacks permission"):
            layer.enforce("admin", ctx)

    def test_enforce_rules(self):
        """এনফোর্স রুলস ফাংশন কাজ করছে।"""
        layer = AdminGodLayer()
        context = {"test": "value"}
        result = layer.enforce_rules(context)
        assert isinstance(result, dict)

    def test_inject_prompt_constraints(self):
        """প্রম্পট কনস্ট্রেন্টস ইনজেক্ট করা হচ্ছে।"""
        layer = AdminGodLayer()
        original_prompt = "You are a helpful assistant."
        result = layer.inject_prompt_constraints(original_prompt)
        assert "CONSTITUTIONAL RULES" in result
        assert original_prompt in result

    def test_inject_prompt_constraints_empty_prompt(self):
        """খালি প্রম্পটের উপর ইনজেকশন করা হচ্ছে।"""
        layer = AdminGodLayer()
        result = layer.inject_prompt_constraints("")
        assert "CONSTITUTIONAL RULES" in result

    def test_inject_prompt_constraints_with_rules(self):
        """রুলস সহ প্রম্পট কনস্ট্রেন্টস ইনজেক্ট করা হচ্ছে।"""
        layer = AdminGodLayer()
        # Add a custom rule to test the injection
        layer.rules_engine.rules["test_rule"] = "test value"
        result = layer.inject_prompt_constraints("Original prompt")
        assert "Test Rule" in result
        assert "test value" in result

    @patch.dict(os.environ, {"SUPREMEAI_ADMIN_PASSWORD_HASH": "valid_hash"})
    def test_verify_admin_success(self):
        """সফল পাসওয়ার্ড ভেরিফিকেশন কাজ করছে।"""
        import bcrypt

        # Create a valid password hash
        password = "test_password_123"
        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

        with patch.object(AdminGodLayer, "__init__", lambda self: None):
            layer = AdminGodLayer()
            layer.admin_password_hash = password_hash

        result = layer.verify_admin(password)
        assert result is True

    @patch.dict(os.environ, {"SUPREMEAI_ADMIN_PASSWORD_HASH": "valid_hash"})
    def test_verify_admin_incorrect_password(self):
        """ভুল পাসওয়ার্ড ভেরিফিকেশন ব্যর্থ হয়।"""
        import bcrypt

        # Create a hash for a different password
        password_hash = bcrypt.hashpw(b"correct_password", bcrypt.gensalt()).decode()

        with patch.object(AdminGodLayer, "__init__", lambda self: None):
            layer = AdminGodLayer()
            layer.admin_password_hash = password_hash

        result = layer.verify_admin("wrong_password")
        assert result is False

    @patch.dict(
        os.environ,
        {"SUPREMEAI_ADMIN_PASSWORD_HASH": "dGhpcyBpcyBhIGJhdnNwYXJzaHdpY2FsbHkgaGFnZSBmb3IgZW5jb2Rpbmc="},
    )
    def test_verify_admin_bcrypt_exception(self):
        """bcrypt exception during verification is handled gracefully."""
        layer = AdminGodLayer()
        layer.admin_password_hash = "invalid_format_that_causes_exception"

        # This should return False and log VERIFY_ERROR
        result = layer.verify_admin("anypassword")
        assert result is False


class TestAdminGodLayerSessions:
    """Tests for god_mode_session context manager."""

    @pytest.mark.anyio
    async def test_god_mode_session_activates_and_terminates(self):
        """god_mode_session কনটেক্সট ম্যানেজার কাজ করছে।"""
        GodModeAuditLog._entries = []
        layer = AdminGodLayer()

        async with layer.god_mode_session("test_user", "testing session") as ctx:
            assert ctx is not None
            assert ctx.session_id is not None
            # Session is active
            assert any(e["action"] == "GOD_MODE_ACTIVATED" for e in GodModeAuditLog._entries)

        # After context exit, terminated entry should be added
        assert any(e["action"] == "GOD_MODE_TERMINATED" for e in GodModeAuditLog._entries)

    @pytest.mark.anyio
    async def test_god_mode_session_logs_ip_address(self):
        """IP ঠিকানা সঠিকভাবে লগ হয়।"""
        GodModeAuditLog._entries = []
        layer = AdminGodLayer()

        async with layer.god_mode_session("user123", "test reason", ip_address="192.168.1.100"):
            pass

        entries = GodModeAuditLog.get_entries()
        activated_entry = next((e for e in entries if e["action"] == "GOD_MODE_ACTIVATED"), None)
        assert activated_entry is not None
        assert activated_entry["ip_address"] == "192.168.1.100"


class TestRBACIntegration:
    """Tests for RBAC integration with AdminGodLayer."""

    def test_rbac_has_permission_admin(self):
        """অ্যাডমিন রোলের অনুমতি চেক করা হচ্ছে।"""
        layer = AdminGodLayer()
        ctx = UserContext(user_id="admin", role="admin")
        result = layer.enforce("admin", ctx)
        assert result["allowed"] is True

    def test_rbac_has_permission_viewer(self):
        """ভিউয়ার রোলের অনুমতি সীমিত থাকে।"""
        layer = AdminGodLayer()
        ctx = UserContext(user_id="viewer", role="viewer")
        result = layer.enforce("read", ctx)
        assert result["allowed"] is True

    def test_rbac_permission_denied_viewer_admin(self):
        """ভিউয়ার রোলের অ্যাডমিন অ্যাকশন অনুমতি নেই।"""
        from core.security.rbac import PermissionDeniedError

        layer = AdminGodLayer()
        ctx = UserContext(user_id="viewer", role="viewer")
        with pytest.raises(PermissionDeniedError):
            layer.enforce("admin", ctx)

```

### 📄 `backend/tests/test_admin_god_security.py`

```py
"""Integration tests for admin god security.

বাংলা: AdminGodLayer — অ্যাডমিন প্রমাণীকরণ, গড মোড অডিট, এবং রুলس এনফোর্সমেন্ট।
"""

from __future__ import annotations

import pytest

from core.admin_god import AdminGodLayer, GodModeAuditLog, GodModeContext
from core.security.rbac import UserContext


class TestAdminGodSecurity:
    """Tests for admin god security."""

    def setup_method(self):
        """Clear audit log before each test."""
        GodModeAuditLog._entries = []

    def test_record_creates_entry(self):
        """Test audit record creation."""
        session_id = GodModeAuditLog.record(
            actor="test_user",
            action="TEST_ACTION",
            resource="test_resource",
            reason="test_reason",
            ip_address="192.168.1.1",
        )
        assert session_id is not None
        assert len(GodModeAuditLog._entries) == 1

    def test_record_default_ip_address(self):
        """Test default IP address."""
        session_id = GodModeAuditLog.record(
            actor="test_user",
            action="TEST_ACTION",
            resource="test_resource",
            reason="test_reason",
        )
        assert GodModeAuditLog._entries[0]["ip_address"] == "unknown"

    def test_update_creates_entry(self):
        """Test update creates new entry."""
        session_id = GodModeAuditLog.record(
            actor="test_user",
            action="GOD_MODE_ACTIVATED",
            resource="system",
            reason="test",
        )
        GodModeAuditLog.update(session_id, "GOD_MODE_TERMINATED", 100.5)
        assert len(GodModeAuditLog._entries) == 2
        assert GodModeAuditLog._entries[1]["action"] == "GOD_MODE_TERMINATED"
        assert GodModeAuditLog._entries[1]["duration_ms"] == 100.5

    def test_update_default_duration(self):
        """Test update with default duration."""
        session_id = GodModeAuditLog.record(actor="test_user", action="ACTIVATED", resource="system", reason="test")
        GodModeAuditLog.update(session_id, "TERMINATED")
        assert GodModeAuditLog._entries[1]["duration_ms"] == 0.0

    def test_get_entries_returns_copy(self):
        """Test get_entries returns a copy."""
        GodModeAuditLog.record(actor="user1", action="ACTION1", resource="res1", reason="reason1")
        GodModeAuditLog.record(actor="user2", action="ACTION2", resource="res2", reason="reason2")
        entries = GodModeAuditLog.get_entries()
        assert len(entries) == 2
        entries.append({"test": "modified"})
        assert len(GodModeAuditLog.get_entries()) == 2

    def test_entry_structure(self):
        """Test entry structure is correct."""
        GodModeAuditLog.record(
            actor="test_actor",
            action="TEST_ACTION",
            resource="test_resource",
            reason="test_reason",
            ip_address="10.0.0.1",
        )
        entry = GodModeAuditLog._entries[0]
        assert "session_id" in entry
        assert "timestamp" in entry
        assert entry["actor"] == "test_actor"
        assert entry["action"] == "TEST_ACTION"

    def test_god_mode_context_creation(self):
        """Test GodModeContext creation."""
        ctx = GodModeContext(session_id="test-session")
        assert ctx.session_id == "test-session"

    def test_enforce_allows_admin(self):
        """Test enforce allows admin role."""
        layer = AdminGodLayer()
        user = UserContext(user_id="admin-1", roles=["admin"])
        result = layer.enforce("test_action", user)
        assert result is True

    def test_enforce_denies_non_admin(self):
        """Test enforce denies non-admin role."""
        layer = AdminGodLayer()
        user = UserContext(user_id="user-1", roles=["user"])
        with pytest.raises(PermissionError):
            layer.enforce("test_action", user)

    def test_inject_prompt_constraints_returns_string(self):
        """Test inject_prompt_constraints returns modified prompt."""
        layer = AdminGodLayer()
        prompt = "You are a helpful assistant."
        result = layer.inject_prompt_constraints(prompt)
        assert isinstance(result, str)
        assert len(result) > 0

```

### 📄 `backend/tests/test_admin_models.py`

```py
from models.admin import (
    AdminEasyLoginRequest,
    AdminFirebaseLoginRequest,
    AdminFirebaseTotpSetupRequest,
    AdminFirebaseTotpVerifyRequest,
)


def test_admin_firebase_login_request():
    req = AdminFirebaseLoginRequest(id_token="token")
    assert req.id_token == "token"


def test_admin_firebase_totp_setup_request():
    req = AdminFirebaseTotpSetupRequest(id_token="token")
    assert req.id_token == "token"


def test_admin_firebase_totp_verify_request():
    req = AdminFirebaseTotpVerifyRequest(id_token="token", otp="789012")
    assert req.id_token == "token"
    assert req.otp == "789012"


def test_admin_easy_login_request():
    req = AdminEasyLoginRequest(code="easy-code")
    assert req.code == "easy-code"

```

### 📄 `backend/tests/test_admin_routes.py`

```py
"""Admin routes tests for SupremeAI 2.0."""

import base64
import hashlib
import hmac
import os
import struct
import time
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient


class TestHelperFunctions:
    """Tests for admin route helper functions."""

    def test_hash_password_requires_bcrypt(self):
        """bcrypt ছাড়া হ্যাশ fails."""
        try:
            # If bcrypt is installed, this should work
            import bcrypt  # noqa: F401

            from core.admin_routes import _hash_password

            hashed = _hash_password("password")
            assert isinstance(hashed, str)
            assert len(hashed) > 0
        except ImportError:
            pytest.skip("bcrypt not installed")
        except RuntimeError as e:
            assert "bcrypt is required" in str(e)

    @pytest.mark.skip(reason="Needs update")
    @pytest.mark.skip(reason="Needs update")
    def test_verify_password_no_bcrypt(self):
        """bcrypt ছাড়া ভেরিফিকেশন False রিটার্ন করে।"""
        with patch.dict("sys.modules", {"bcrypt": None}):
            import importlib

            from core import admin_routes

            importlib.reload(admin_routes)
            assert admin_routes._verify_password("pass", "hash") is False

    @pytest.mark.skip(reason="Needs update")
    @pytest.mark.skip(reason="Needs update")
    def test_verify_password_empty_hash(self):
        """খালি হ্যাশে ভেরিফিকেশন False রিটার্ন করে।"""
        from core.admin_routes import _verify_password

        assert _verify_password("password", "") is False
        assert _verify_password("password", None) is False

    @pytest.mark.skip(reason="Needs update")
    @pytest.mark.skip(reason="Needs update")
    def test_get_admin_credentials_missing_hash(self):
        """এডমিন পাসওয়ার্ড হ্যাশ নেই থাকলে 500 রিটার্ন করে।"""
        with patch.dict(os.environ, {"SUPREMEAI_ADMIN_PASSWORD_HASH": ""}, clear=False):
            from core.admin_routes import _get_admin_credentials

            with pytest.raises(HTTPException) as exc_info:
                _get_admin_credentials()

            assert exc_info.value.status_code == 500

    @pytest.mark.skip(reason="Needs update")
    @pytest.mark.skip(reason="Needs update")
    def test_get_admin_credentials_returns_hash(self):
        """যোগ্য এডমিন হ্যাশ রিটার্ন করে।"""
        test_hash = "test-admin-hash-value"
        with patch.dict(os.environ, {"SUPREMEAI_ADMIN_PASSWORD_HASH": test_hash}, clear=False):
            from core.admin_routes import _get_admin_credentials

            assert _get_admin_credentials() == test_hash


class TestVerifyTotpCode:
    """Tests for TOTP verification functions."""

    def test_verify_totp_code_valid(self):
        """বৈধ TOTP কোড ভেরিফিকেশন."""
        from core.admin_routes import verify_totp_code

        secret = base64.b32encode(os.urandom(10)).decode("utf-8")

        current_time = int(time.time() // 30)
        msg = struct.pack(">Q", current_time)
        key = base64.b32decode(secret.upper())
        h = hmac.new(key, msg, hashlib.sha1).digest()
        o = h[19] & 15
        h_num = struct.unpack(">I", h[o : o + 4])[0] & 0x7FFFFFFF
        valid_otp = f"{h_num % 1000000:06d}"

        assert verify_totp_code(valid_otp, secret) is True

    def test_verify_totp_code_invalid(self):
        """অবৈধ TOTP কোড রিজেক্স করা হচ্ছে।"""
        from core.admin_routes import verify_totp_code

        secret = base64.b32encode(os.urandom(10)).decode("utf-8")
        assert verify_totp_code("000000", secret) is False

    def test_check_totp_valid(self):
        """check_totp বৈধ কোড ভেরিফাই করে."""
        from core.admin_routes import check_totp

        secret = base64.b32encode(os.urandom(10)).decode("utf-8")

        current_time = int(time.time() // 30)
        msg = struct.pack(">Q", current_time)
        key = base64.b32decode(secret.upper())
        h = hmac.new(key, msg, hashlib.sha1).digest()
        o = h[19] & 15
        h_num = struct.unpack(">I", h[o : o + 4])[0] & 0x7FFFFFFF
        valid_otp = f"{h_num % 1000000:06d}"

        assert check_totp(valid_otp, secret) is True

    def test_check_totp_invalid(self):
        """check_totp অবৈধ কোড রিজেক্স করে."""
        from core.admin_routes import check_totp

        secret = base64.b32encode(os.urandom(10)).decode("utf-8")
        assert check_totp("123456", secret) is False

    def test_verify_totp_code_bad_secret(self):
        """খারাপ সিক্রেটে TOTP False রিটার্ন করে।"""
        from core.admin_routes import verify_totp_code

        assert verify_totp_code("1234567", "not-valid-base32-!@#$") is False


class TestAdminRoutes:
    """Tests for admin FastAPI routes using TestClient."""

    @pytest.fixture
    def client(self):
        """TestClient with mocked dependencies and auth header."""
        from core.app import app as fastapi_app

        return TestClient(fastapi_app, headers={"Authorization": "Bearer test-admin-token"})

    def test_health(self, client):
        """Health endpoint."""
        response = client.get("/health")
        assert response.status_code in [200, 503]

    def test_actuator_health(self, client):
        """Actuator health check."""
        response = client.get("/actuator/health")
        assert response.status_code == 200

    def test_admin_firebase_login_no_token(self, client):
        """Firebase login with no token returns 422."""
        response = client.post("/api/admin/firebase-login", json={})
        assert response.status_code == 422

    def test_admin_firebase_login_mock_token_non_production(self, client):
        """মক ফায়ারবেস টোকেন লগইন non-production."""
        with patch("core.config.settings.env", "local"):
            response = client.post("/api/admin/firebase-login", json={"id_token": "mock-test-token"})
            assert response.status_code in [200, 403]

    def test_admin_firebase_login_mock_token_production(self, client):
        """মক টোকেন প্রোডাকশন নিষিদ্ধ."""
        with patch("core.config.settings.env", "production"):
            response = client.post("/api/admin/firebase-login", json={"id_token": "mock-test-token"})
            assert response.status_code == 403

    def test_admin_firebase_totp_setup_no_token(self, client):
        """TOTP setup missing token returns 422."""
        response = client.post("/api/admin/firebase-totp-setup", json={})
        assert response.status_code == 422

    def test_admin_firebase_totp_verify_no_token(self, client):
        """TOTP verify missing token returns 422."""
        response = client.post("/api/admin/firebase-totp-verify", json={})
        assert response.status_code == 422

    def test_cloud_distribution(self, client):
        """Cloud distribution endpoint."""
        with patch("core.admin_routes.services") as mock_services:
            mock_provider = {"status": "active", "current_requests": 0}
            mock_services.parallel_router.PROVIDERS = {"provider1": mock_provider}
            mock_services.parallel_router.get_distribution_stats = MagicMock(return_value={})

            response = client.get("/admin/cloud-distribution")
            assert response.status_code == 200

    def test_free_tier_status(self, client):
        """Free tier status endpoint."""
        mock_tracker = MagicMock()
        mock_tracker.get_status.return_value = {"status": "active"}

        with patch("core.admin_routes.services") as mock_services:
            mock_services.get_tracker = MagicMock(return_value=mock_tracker)
            with patch.dict(
                "sys.modules",
                {"core.free_tier_tracker": MagicMock(get_tracker=MagicMock(return_value=mock_tracker))},
            ):
                response = client.get("/admin/free-tier-status")
                assert response.status_code == 200

    def test_free_tier_provider_status_not_found(self, client):
        """অন tracked provider."""
        mock_tracker = MagicMock()
        mock_tracker.get_provider_status.return_value = None

        with patch.dict(
            "sys.modules",
            {"core.free_tier_tracker": MagicMock(get_tracker=MagicMock(return_value=mock_tracker))},
        ):
            response = client.get("/admin/free-tier-status/nonexistent")
            assert response.status_code == 404

    def test_free_tier_pause_provider(self, client):
        """Free tier pause provider endpoint."""
        mock_tracker = MagicMock()
        mock_tracker.mark_rate_limited.return_value = None

        with patch.dict(
            "sys.modules",
            {"core.free_tier_tracker": MagicMock(get_tracker=MagicMock(return_value=mock_tracker))},
        ):
            response = client.post("/admin/free-tier-pause/provider1")
            assert response.status_code == 200

    def test_free_tier_override_limits(self, client):
        """free tier override limits."""
        mock_tracker = MagicMock()
        mock_tracker.override_limits.return_value = None

        with patch.dict(
            "sys.modules",
            {"core.free_tier_tracker": MagicMock(get_tracker=MagicMock(return_value=mock_tracker))},
        ):
            response = client.post("/admin/free-tier-override/provider1", json={"limit": 100})
            assert response.status_code == 200

    def test_token_budget_stats(self, client):
        """Token budget stats endpoint."""
        mock_manager = MagicMock()
        mock_manager.get_stats.return_value = {"total": 1000}

        with patch.dict(
            "sys.modules",
            {"core.token_budget": MagicMock(get_budget_manager=MagicMock(return_value=mock_manager))},
        ):
            response = client.get("/admin/token-budget-stats")
            assert response.status_code == 200

    def test_gcp_health(self, client):
        """GCP health endpoint."""
        with patch("core.admin_routes.services") as mock_services:
            mock_services.gcp_router.health_check.return_value = {"status": "ok"}
            mock_services.verification_queue.provider = "firestore"
            mock_services.gcp_pubsub_queue.provider = "pubsub"
            mock_services.cloud_function_client.get_config.return_value = {}

            response = client.get("/gcp/health")
            assert response.status_code == 200

    def test_gcp_verification_queue_stats(self, client):
        """GCP verification queue stats."""
        with patch("core.admin_routes.services") as mock_services:
            mock_services.verification_queue.stats.return_value = {"total": 0}
            response = client.get("/gcp/verification-queue/stats")
            assert response.status_code == 200

    def test_gcp_pubsub_stats(self, client):
        """GCP pubsub stats."""
        with patch("core.admin_routes.services") as mock_services:
            mock_services.gcp_pubsub_queue.stats.return_value = {"messages": 0}
            response = client.get("/gcp/pubsub/stats")
            assert response.status_code == 200

    def test_get_admin_rules(self, client):
        """Get admin rules endpoint."""
        with patch("core.admin_routes.services") as mock_services:
            mock_services.rules_engine.rules = {"test": "rule"}
            response = client.get("/admin/rules")
            assert response.status_code == 200

    def test_post_admin_rules(self, client):
        """Post admin rules endpoint."""
        with patch("core.admin_routes.services") as mock_services:
            mock_services.rules_engine.save_rules.return_value = True
            response = client.post("/admin/rules", json={"rules": {"new": "rule"}})
            assert response.status_code == 200

    def test_post_admin_rules_failure(self, client):
        """Post admin rules failure."""
        with patch("core.admin_routes.services") as mock_services:
            mock_services.rules_engine.save_rules.return_value = False
            response = client.post("/admin/rules", json={"rules": {"new": "rule"}})
            assert response.status_code == 200

    def test_get_skills(self, client):
        """Skills endpoint."""
        response = client.get("/skills")
        assert response.status_code == 200


class TestGetCurrentAdminGuard:
    """Regression tests for get_current_admin() — previously referenced an
    undefined HTTP_403_FORBIDDEN name, so a non-admin request crashed with an
    unhandled NameError (-> 500) instead of a clean 403. See core/admin_routes.py.
    """

    def test_non_admin_role_raises_403(self):
        """অ-এডমিন role হলে পরিষ্কার 403 HTTPException রেইজ হওয়া উচিত, NameError না।"""
        from core.admin_routes import get_current_admin

        with pytest.raises(HTTPException) as exc_info:
            get_current_admin({"role": "user", "sub": "someone@example.com"})

        assert exc_info.value.status_code == 403
        assert "Admin access required" in exc_info.value.detail

    def test_missing_role_raises_403(self):
        """payload-এ role কী-ই না থাকলেও 403 হওয়া উচিত।"""
        from core.admin_routes import get_current_admin

        with pytest.raises(HTTPException) as exc_info:
            get_current_admin({"sub": "someone@example.com"})

        assert exc_info.value.status_code == 403

    def test_admin_role_passes_through(self):
        """role == 'admin' হলে payload অপরিবর্তিত রিটার্ন হবে, কোনো exception ছাড়াই।"""
        from core.admin_routes import get_current_admin

        payload = {"role": "admin", "sub": "admin@example.com"}
        result = get_current_admin(payload)
        assert result == payload

```

### 📄 `backend/tests/test_advanced.py`

```py
import os
import sys
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.evolution.evolution_engine import EvolutionEngine
from core.queue.task_router import TaskRouter
from memory.chromadb_store import ChromaDBStore
from memory.rag_pipeline import RAGPipeline
from memory.sqlite_store import SQLiteMemoryStore
from tools.ai_agents.browser_agent import BrowserAgent
from tools.ai_agents.computer_agent import ComputerAgent
from tools.api_gateway import APIGateway
from tools.security_tools.multi_account_rotator import MultiAccountRotator
from tools.social.telegram_bot import TelegramBotHandler


def test_task_router():
    router = TaskRouter()
    r = router.analyze_and_route("write a python script to search a list")
    assert r["task_type"] == "coding"

    r = router.analyze_and_route("generate an image of a red square")
    assert r["task_type"] == "image_generation"


@pytest.mark.anyio
async def test_evolution_engine():
    engine = EvolutionEngine()
    history = [{"success": True}, {"success": False}]
    # বাংলা মন্তব্য: run_daily_evolution অ্যাসিঙ্ক হওয়ায় এখানে await করা হলো।
    report = await engine.run_daily_evolution(history)
    assert report["total_tasks_processed"] == 2
    assert report["success_rate"] == 50.0


def test_sqlite_memory_store():
    # Use in-memory SQLite for testing
    store = SQLiteMemoryStore(":memory:")
    store.log_task("Write code", "coding", True, 0.01, "Code written")
    history = store.get_task_history()
    assert len(history) == 1
    assert history[0]["task_description"] == "Write code"


def test_chromadb_local_vector_db():
    db = ChromaDBStore(":memory:")
    db.add_document("doc1", "apple fruit red sweet")
    db.add_document("doc2", "banana yellow long fruit")

    res = db.query("red apple", n_results=1)
    assert len(res) == 1
    assert res[0][0] == "doc1"


def test_rag_pipeline():
    db = ChromaDBStore(":memory:")
    pipeline = RAGPipeline(db)
    pipeline.ingest_document("test_doc", "The secret passcode is 12345.")
    ctx = pipeline.retrieve_context("passcode")
    assert "12345" in ctx


@pytest.mark.asyncio
async def test_browser_agent():
    agent = BrowserAgent()
    with patch("tools.ai_agents.browser_agent.is_safe_url", return_value=True):
        with patch("tools.ai_agents.browser_agent.get_global_browser", new_callable=AsyncMock) as mock_browser:
            mock_browser.return_value = None
            with patch("httpx.get") as mock_get:
                mock_resp = MagicMock()
                mock_resp.text = "<html><title>Sample Site</title><body>Hello world</body></html>"
                mock_resp.is_success = True
                mock_get.return_value = mock_resp

                res = await agent.navigate_and_interact("http://example.com")
                assert res["success"] is True
                assert res["title"] == "Sample Site"


def test_computer_agent_security():
    agent = ComputerAgent()
    res = agent.execute_command("rm -rf /")
    assert res["success"] is False
    assert "Security block" in res["error"]


def test_api_gateway():
    gateway = APIGateway()
    with patch("httpx.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.is_success = True
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"status": "ok"}
        mock_post.return_value = mock_resp

        res = gateway.trigger_n8n_workflow("webhook/test", {"test": "val"})
        assert res["success"] is True
        assert res["data"] == {"status": "ok"}


def test_telegram_bot_handler():
    handler = TelegramBotHandler()
    res = handler.handle_message("/rules", "user1")
    assert "5 directions" in res


@pytest.mark.asyncio
async def test_task_queue():
    from core.queue.task_queue_enhanced import get_task_result, submit_task

    async def mock_task():
        return "done"

    task_id = await submit_task(mock_task)
    res = await get_task_result(task_id, timeout=2.0)
    assert res.status == "completed"


@pytest.mark.anyio
async def test_perform_autonomous_signup():
    from unittest.mock import AsyncMock

    mock_p = MagicMock()
    mock_playwright = MagicMock()
    mock_playwright.return_value.__aenter__.return_value = mock_p

    mock_browser = MagicMock()
    mock_browser.new_page = AsyncMock()
    mock_browser.close = AsyncMock()

    mock_p.chromium.launch = AsyncMock(return_value=mock_browser)

    mock_page = MagicMock()
    mock_page.goto = AsyncMock()
    mock_page.fill = AsyncMock()
    mock_page.click = AsyncMock()
    mock_page.wait_for_selector = AsyncMock()
    mock_browser.new_page.return_value = mock_page

    mock_playwright_module = MagicMock()
    mock_playwright_module.async_api.async_playwright = mock_playwright

    with (
        patch.dict(
            "sys.modules",
            {
                "playwright": mock_playwright_module,
                "playwright.async_api": mock_playwright_module.async_api,
            },
        ),
        tempfile.TemporaryDirectory() as tmpdir,
    ):
        config_path = os.path.join(tmpdir, "rotation_config.json")
        rotator = MultiAccountRotator(config_file=config_path)
        success = await rotator.perform_autonomous_signup("google_ai_studio")
        assert success is True
        assert "google_ai_studio" in rotator.providers
        accounts = rotator.providers["google_ai_studio"].accounts
        assert len(accounts) == 1
        assert accounts[0].email.startswith("supremeai+")
        assert accounts[0].password is not None
        # বাংলা মন্তব্য: ডাইনামিক রিকভারি ইমেইল ভ্যালিডেশন
        assert "@yourdomain.com" in accounts[0].recovery_email

```

### 📄 `backend/tests/test_agent_department.py`

```py
from unittest.mock import MagicMock

from brain.agent_department import AgentDepartment


def test_agent_department_coding_success():
    mock_router = MagicMock()
    mock_router.route_and_generate.return_value = {
        "success": True,
        "text": "def test(): pass",
        "provider": "gemini",
        "cost": 0.002,
    }

    dept = AgentDepartment(mock_router)
    res = dept.run("coding", "write code for addition")
    assert res["success"]
    assert res["output"] == "def test(): pass"
    assert res["provider"] == "gemini"


def test_agent_department_review_failure():
    mock_router = MagicMock()
    mock_router.route_and_generate.return_value = {
        "success": False,
        "error": "rate limit reached",
    }

    dept = AgentDepartment(mock_router)
    res = dept.run("review", "review this code")
    assert not res["success"]
    assert res["error"] == "rate limit reached"


def test_agent_department_qa_exception():
    mock_router = MagicMock()
    mock_router.route_and_generate.side_effect = Exception("connection failed")

    dept = AgentDepartment(mock_router)
    res = dept.run("qa", "write tests")
    assert not res["success"]
    assert "connection failed" in res["error"]


def test_agent_department_unknown():
    mock_router = MagicMock()
    dept = AgentDepartment(mock_router)
    res = dept.run("unknown_dept", "do task")
    assert not res["success"]
    assert "Unknown department" in res["error"]

```

### 📄 `backend/tests/test_agent_departments.py`

```py
from __future__ import annotations

from unittest.mock import MagicMock

from brain.agent_departments import AgentDepartment


def _make_dept(model_router=None):
    if model_router is None:
        model_router = MagicMock()
    return AgentDepartment(model_router=model_router)


def test_list_roles_returns_all_defined_roles():
    dept = _make_dept()
    roles = dept.list_roles()
    assert "coder" in roles
    assert "code-reviewer" in roles
    assert "architect" in roles
    assert "qa" in roles
    assert "data" in roles
    assert "security" in roles
    assert len(roles) == 6


def test_execute_coder_success():
    mock_router = MagicMock()
    mock_router.route_and_generate.return_value = {
        "success": True,
        "text": "def hello(): pass",
        "cost": 0.003,
    }
    dept = _make_dept(mock_router)
    result = dept.execute("coder", "write a hello function", "Python context")
    assert result["success"] is True
    assert result["role"] == "coder"
    assert result["output"] == "def hello(): pass"
    assert result["cost"] == 0.003
    prompt = mock_router.route_and_generate.call_args.kwargs["prompt"]
    assert "write a hello function" in prompt
    assert "R-A-C-E" in prompt


def test_execute_code_reviewer_success():
    mock_router = MagicMock()
    mock_router.route_and_generate.return_value = {
        "success": True,
        "text": "Review: looks good",
        "cost": 0.002,
    }
    dept = _make_dept(mock_router)
    result = dept.execute("code-reviewer", "review this code", "code context")
    assert result["success"] is True
    assert result["role"] == "code-reviewer"
    assert "C-L-E-A-R" in mock_router.route_and_generate.call_args.kwargs["prompt"]


def test_execute_qa_success():
    mock_router = MagicMock()
    mock_router.route_and_generate.return_value = {
        "success": True,
        "text": "Test cases: 1, 2, 3",
        "cost": 0.001,
    }
    dept = _make_dept(mock_router)
    result = dept.execute("qa", "write test cases", "app context")
    assert result["success"] is True
    assert result["role"] == "qa"
    assert "S-T-A-R" in mock_router.route_and_generate.call_args.kwargs["prompt"]


def test_execute_architect_success():
    mock_router = MagicMock()
    mock_router.route_and_generate.return_value = {
        "success": True,
        "text": "Architecture plan",
        "cost": 0.004,
    }
    dept = _make_dept(mock_router)
    result = dept.execute("architect", "design system", "context")
    assert result["success"] is True
    assert result["role"] == "architect"
    assert "S-O-A-P" in mock_router.route_and_generate.call_args.kwargs["prompt"]


def test_execute_data_success():
    mock_router = MagicMock()
    mock_router.route_and_generate.return_value = {
        "success": True,
        "text": "Pipeline plan",
        "cost": 0.002,
    }
    dept = _make_dept(mock_router)
    result = dept.execute("data", "build pipeline", "context")
    assert result["success"] is True
    assert result["role"] == "data"
    assert "G-R-O-W" in mock_router.route_and_generate.call_args.kwargs["prompt"]


def test_execute_security_success():
    mock_router = MagicMock()
    mock_router.route_and_generate.return_value = {
        "success": True,
        "text": "Threat: SQLi, Mitigation: parameterized queries",
        "cost": 0.003,
    }
    dept = _make_dept(mock_router)
    result = dept.execute("security", "audit login flow", "context")
    assert result["success"] is True
    assert result["role"] == "security"
    assert result["output"] == "Threat: SQLi, Mitigation: parameterized queries"


def test_execute_unknown_role_falls_back_to_coder_prompt():
    mock_router = MagicMock()
    mock_router.route_and_generate.return_value = {
        "success": True,
        "text": "fallback output",
        "cost": 0.001,
    }
    dept = _make_dept(mock_router)
    result = dept.execute("unknown_role", "do something")
    assert result["success"] is True
    assert result["role"] == "unknown_role"
    assert "R-A-C-E" in mock_router.route_and_generate.call_args.kwargs["prompt"]


def test_execute_router_returns_text_without_success_flag():
    mock_router = MagicMock()
    mock_router.route_and_generate.return_value = {
        "success": False,
        "text": "fallback text output",
        "cost": 0.001,
    }
    dept = _make_dept(mock_router)
    result = dept.execute("coder", "generate code")
    assert result["success"] is True
    assert result["output"] == "fallback text output"


def test_execute_router_returns_neither_success_nor_text():
    mock_router = MagicMock()
    mock_router.route_and_generate.return_value = {
        "success": False,
        "error": "model unavailable",
        "cost": 0.0,
    }
    dept = _make_dept(mock_router)
    result = dept.execute("coder", "generate code")
    assert result["success"] is False
    assert result["error"] == "model unavailable"


def test_execute_exception_handling():
    mock_router = MagicMock()
    mock_router.route_and_generate.side_effect = RuntimeError("connection lost")
    dept = _make_dept(mock_router)
    result = dept.execute("coder", "generate code")
    assert result["success"] is False
    assert "connection lost" in result["error"]


def test_execute_case_insensitive_role():
    mock_router = MagicMock()
    mock_router.route_and_generate.return_value = {
        "success": True,
        "text": "output",
        "cost": 0.001,
    }
    dept = _make_dept(mock_router)
    result = dept.execute("CODER", "do task")
    assert result["role"] == "coder"


def test_execute_empty_context_defaults_to_none_string():
    mock_router = MagicMock()
    mock_router.route_and_generate.return_value = {
        "success": True,
        "text": "output",
        "cost": 0.001,
    }
    dept = _make_dept(mock_router)
    dept.execute("coder", "do task", context="")
    prompt = mock_router.route_and_generate.call_args.kwargs["prompt"]
    assert "Context: None" in prompt


def test_execute_with_context_includes_context():
    mock_router = MagicMock()
    mock_router.route_and_generate.return_value = {
        "success": True,
        "text": "output",
        "cost": 0.001,
    }
    dept = _make_dept(mock_router)
    dept.execute("coder", "do task", context="my context")
    prompt = mock_router.route_and_generate.call_args.kwargs["prompt"]
    assert "my context" in prompt
    assert "Context: my context" in prompt


def test_default_model_router_initialized():
    dept = _make_dept(None)
    assert dept.model_router is not None

```

### 📄 `backend/tests/test_agent_factory.py`

```py
"""
Tests for core/agent_factory.py — DynamicAgentFactory
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.agent_factory import DynamicAgentFactory


@pytest.fixture
def mock_db_session():
    return AsyncMock()


@pytest.fixture
def factory(mock_db_session):
    return DynamicAgentFactory(db_session=mock_db_session)


def test_get_registered_agent_found(factory, tmp_path):
    """Test get_registered_agent returns agent config when found in registry."""
    agent_data = {"name": "test-agent", "description": "A test agent"}
    registry_path = Path(__file__).resolve().parent.parent / "core" / "agent_registry.json"

    # Create a temporary registry
    test_registry = {"test-agent": agent_data}
    with patch.object(Path, "exists", return_value=True), patch("builtins.open", MagicMock()) as mock_open:
        mock_file = MagicMock()
        mock_file.__enter__.return_value.read.return_value = json.dumps(test_registry)
        mock_open.return_value = mock_file

        result = factory.get_registered_agent("test-agent")
        assert result == agent_data


def test_get_registered_agent_not_found(factory):
    """Test get_registered_agent returns None when agent not in registry."""
    with patch.object(Path, "exists", return_value=True), patch("builtins.open", MagicMock()) as mock_open:
        mock_file = MagicMock()
        mock_file.__enter__.return_value.read.return_value = json.dumps({})
        mock_open.return_value = mock_file

        result = factory.get_registered_agent("nonexistent")
        assert result is None


def test_get_registered_agent_no_registry(factory):
    """Test get_registered_agent returns None when registry file doesn't exist."""
    with patch.object(Path, "exists", return_value=False):
        result = factory.get_registered_agent("test-agent")
        assert result is None


def test_get_registered_agent_bad_json(factory):
    """Test get_registered_agent returns None on JSON parse error."""
    with patch.object(Path, "exists", return_value=True), patch("builtins.open", MagicMock()) as mock_open:
        mock_file = MagicMock()
        mock_file.__enter__.return_value.read.return_value = "invalid json{{{"
        mock_open.return_value = mock_file

        result = factory.get_registered_agent("test-agent")
        assert result is None


@pytest.mark.asyncio
async def test_create_specialized_agent_success(factory, mock_db_session):
    """Test create_specialized_agent successfully creates an agent."""
    mock_response = {
        "text": json.dumps(
            {
                "agent_name": "test_agent_123",
                "description": "Solve a test task",
                "script": "print('hello world')",
            }
        )
    }

    with patch("core.agent_factory.llm_gateway") as mock_llm:
        mock_llm.acompletion = AsyncMock(return_value=mock_response)

        # Mock DB operations
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_db_session.execute.return_value = mock_result

        result = await factory.create_specialized_agent("Solve a test task")

        assert result["agent_name"] == "test_agent_123"
        assert result["description"] == "Solve a test task"
        assert "script" in result
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_create_specialized_agent_parse_fallback(factory, mock_db_session):
    """Test create_specialized_agent falls back when JSON parsing fails."""
    mock_response = {"text": "not valid json at all"}

    with patch("core.agent_factory.llm_gateway") as mock_llm:
        mock_llm.acompletion = AsyncMock(return_value=mock_response)

        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_db_session.execute.return_value = mock_result

        result = await factory.create_specialized_agent("Solve a test task")

        assert "agent_name" in result
        assert "AutoAgent_" in result["agent_name"]
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_create_specialized_agent_db_rollback(factory, mock_db_session):
    """Test create_specialized_agent handles DB errors gracefully."""
    mock_response = {
        "text": json.dumps(
            {
                "agent_name": "test_agent",
                "description": "Test",
                "script": "print('hello')",
            }
        )
    }

    with patch("core.agent_factory.llm_gateway") as mock_llm:
        mock_llm.acompletion = AsyncMock(return_value=mock_response)
        mock_db_session.commit.side_effect = Exception("DB error")

        result = await factory.create_specialized_agent("Solve a test task")

        assert result["agent_name"] == "test_agent"
        mock_db_session.rollback.assert_called_once()


@pytest.mark.asyncio
async def test_save_agent_to_registry_existing(factory, mock_db_session):
    """Test _save_agent_to_registry updates existing agent."""
    mock_agent = MagicMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_agent
    mock_db_session.execute.return_value = mock_result

    await factory._save_agent_to_registry(
        name="existing_agent",
        description="Updated description",
        steps={"script": "print('updated')"},
    )

    assert mock_agent.execution_steps is not None
    assert mock_agent.description == "Updated description"
    mock_db_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_save_agent_to_registry_new(factory, mock_db_session):
    """Test _save_agent_to_registry creates new agent."""
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None
    mock_db_session.execute.return_value = mock_result

    await factory._save_agent_to_registry(
        name="new_agent",
        description="New agent",
        steps={"script": "print('new')"},
    )

    mock_db_session.add.assert_called_once()
    mock_db_session.commit.assert_called_once()


def test_factory_no_db_session():
    """Test factory can be created without a DB session."""
    factory = DynamicAgentFactory()
    assert factory.db is None

```

### 📄 `backend/tests/test_agent_orchestrator.py`

```py
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from core.orchestration.agent_orchestrator import (
    AgentCircuitBreaker,
    AsyncTaskManager,
    SmartSemanticRouter,
    budget_aware_route,
    route_request,
)


@pytest.fixture
def circuit_breaker():
    return AgentCircuitBreaker(agent_name="test_agent")


def test_circuit_breaker_initialization(circuit_breaker):
    assert circuit_breaker.agent_name == "test_agent"
    assert circuit_breaker.max_iterations == 5
    assert circuit_breaker.max_tokens == 5000
    assert circuit_breaker._iteration_count == 0
    assert circuit_breaker._token_count == 0
    assert circuit_breaker._locked is False


def test_circuit_breaker_increment_iteration_allowed(circuit_breaker):
    assert circuit_breaker.increment_iteration() is True
    assert circuit_breaker._iteration_count == 1


def test_circuit_breaker_increment_iteration_exceeded(circuit_breaker):
    for _ in range(5):
        assert circuit_breaker.increment_iteration() is True
    assert circuit_breaker.increment_iteration() is False
    assert circuit_breaker._locked is True
    assert "Max iterations" in circuit_breaker._lock_reason


def test_circuit_breaker_add_tokens_allowed(circuit_breaker):
    assert circuit_breaker.add_tokens(1000) is True
    assert circuit_breaker._token_count == 1000


def test_circuit_breaker_add_tokens_exceeded(circuit_breaker):
    assert circuit_breaker.add_tokens(5000) is True
    assert circuit_breaker.add_tokens(1) is False
    assert circuit_breaker._locked is True
    assert "Max tokens" in circuit_breaker._lock_reason


def test_circuit_breaker_check_limits_when_locked(circuit_breaker):
    circuit_breaker._locked = True
    circuit_breaker._lock_reason = "test lock"
    result = circuit_breaker.check_limits()
    assert result["blocked"] is True
    assert result["reason"] == "test lock"


def test_circuit_breaker_check_limits_when_unlocked(circuit_breaker):
    result = circuit_breaker.check_limits()
    assert result["blocked"] is False


def test_circuit_breaker_reset(circuit_breaker):
    circuit_breaker._iteration_count = 10
    circuit_breaker._token_count = 9999
    circuit_breaker._locked = True
    circuit_breaker._lock_reason = "limit exceeded"
    circuit_breaker.reset()
    assert circuit_breaker._iteration_count == 0
    assert circuit_breaker._token_count == 0
    assert circuit_breaker._locked is False
    assert circuit_breaker._lock_reason is None


def test_circuit_breaker_get_status(circuit_breaker):
    circuit_breaker.add_tokens(100)
    circuit_breaker.increment_iteration()
    status = circuit_breaker.get_status()
    assert status["agent_name"] == "test_agent"
    assert status["iterations_used"] == 1
    assert status["tokens_used"] == 100
    assert status["locked"] is False


@pytest.mark.parametrize(
    "prompt,task_type,expected_intent,tier",
    [
        ("code a python function", "general", "coding", 1),
        ("build a react component", "general", "coding", 1),
        ("debug my code", "general", "coding", 1),
        ("refactor the class", "general", "coding", 1),
        ("algorithm optimization", "general", "coding", 1),
        ("reason about the logic", "general", "reasoning", 1),
        ("analyze the math problem", "general", "reasoning", 1),
        ("prove the theorem", "general", "reasoning", 1),
        ("calculate the integral", "general", "reasoning", 1),
        ("search for documentation", "general", "search", 2),
        ("find the best practice", "general", "search", 2),
        ("research the topic", "general", "search", 2),
        ("lookup the API", "general", "search", 2),
        ("query the database", "general", "search", 2),
        ("summarize the article", "general", "search", 2),
        ("translate to spanish", "general", "search", 2),
        ("sentiment analysis", "general", "search", 2),
        ("image recognition task", "general", "vision", 3),
        ("ocr scan this document", "general", "vision", 3),
        ("analyze the photo", "general", "reasoning", 1),
        ("visualize the chart", "general", "vision", 3),
        ("code this file.png", "general", "vision", 3),
    ],
)
def test_route_request_keyword_routing(prompt, task_type, expected_intent, tier):
    result = route_request(prompt, task_type)
    assert isinstance(result, SmartSemanticRouter)
    assert result.intent == expected_intent
    assert result.tier == tier


def test_route_request_explicit_code_task():
    result = route_request("do something", task_type="code")
    assert result.intent == "coding"
    assert result.requires_expensive is True
    assert result.tier == 1


def test_route_request_explicit_reasoning_task():
    result = route_request("do something", task_type="reasoning")
    assert result.intent == "reasoning"
    assert result.requires_expensive is True
    assert result.tier == 1


def test_route_request_vision_task():
    result = route_request("do something", task_type="vision")
    assert result.intent == "vision"
    assert result.requires_expensive is True
    assert result.tier == 3


def test_route_request_file_extension_vision():
    result = route_request("check out this .jpg file")
    assert result.intent == "vision"
    assert result.requires_expensive is True


def test_route_request_translation_task():
    result = route_request("translate this text", task_type="translation")
    assert result.intent == "search"
    assert result.requires_expensive is False
    assert result.tier == 2


def test_route_request_image_task():
    result = route_request("show me an image", task_type="image")
    assert result.intent == "vision"
    assert result.requires_expensive is True
    assert result.tier == 3


def test_route_request_default_fallback():
    result = route_request("random unrelated prompt", task_type="general")
    assert result.intent == "general"
    assert result.requires_expensive is False
    assert result.tier == 5


def test_async_task_manager_create_and_get():
    mgr = AsyncTaskManager()
    task_id = mgr.create_task("test_type", {"key": "value"})
    assert task_id in mgr._tasks
    task = mgr.get_task(task_id)
    assert task is not None
    assert task["type"] == "test_type"
    assert task["status"] == "pending"
    assert task["progress"] == 0


def test_async_task_manager_get_unknown():
    mgr = AsyncTaskManager()
    assert mgr.get_task("nonexistent") is None


def test_async_task_manager_get_stats_empty():
    mgr = AsyncTaskManager()
    stats = mgr.get_stats()
    assert stats["total_tasks"] == 0
    assert stats["by_status"]["pending"] == 0


def test_async_task_manager_get_stats_with_tasks():
    mgr = AsyncTaskManager()
    t1 = mgr.create_task("type_a", {})
    t2 = mgr.create_task("type_b", {})
    mgr._tasks[t1]["status"] = "completed"
    mgr._tasks[t2]["status"] = "failed"
    stats = mgr.get_stats()
    assert stats["total_tasks"] == 2
    assert stats["by_status"]["completed"] == 1
    assert stats["by_status"]["failed"] == 1


def test_async_task_manager_simulate_video():
    mgr = AsyncTaskManager()
    task_id = mgr.create_task("video_generation", {"prompt": "video"})
    task = mgr.get_task(task_id)
    assert task["status"] == "processing"
    assert task["progress"] == 50


def test_async_task_manager_simulate_image():
    mgr = AsyncTaskManager()
    task_id = mgr.create_task("image_generation", {"prompt": "image"})
    task = mgr.get_task(task_id)
    assert task["status"] == "processing"
    assert task["progress"] == 50


def test_smart_semantic_router_model():
    router = SmartSemanticRouter(intent="test_intent", requires_expensive=True, tier=2, reasoning="test")
    assert router.intent == "test_intent"
    assert router.requires_expensive is True
    assert router.tier == 2
    assert router.reasoning == "test"


def test_smart_semantic_router_defaults():
    router = SmartSemanticRouter()
    assert router.intent == "general"
    assert router.requires_expensive is False
    assert router.tier == 5
    assert router.reasoning == ""


def test_budget_aware_route_no_free_tier():
    with patch("core.agent_orchestrator._free_tier_available", False):
        result = budget_aware_route("some prompt", task_type="general")
    assert result["intent"] == "general"
    assert result["requires_expensive"] is False
    assert result["tier"] == 5
    assert "best_provider" in result


def test_budget_aware_route_free_tier_available():
    mock_tracker = MagicMock()
    mock_tracker.get_best_provider.return_value = "groq"
    with patch("core.agent_orchestrator._free_tier_available", True):
        with patch("core.agent_orchestrator.get_tracker", return_value=mock_tracker):
            result = budget_aware_route("some prompt", task_type="general")
    assert result["best_provider"] == "groq"
    mock_tracker.get_best_provider.assert_called_once()


def test_budget_aware_route_free_tier_exhausted():
    mock_tracker = MagicMock()
    mock_tracker.get_best_provider.return_value = None
    with patch("core.agent_orchestrator._free_tier_available", True):
        with patch("core.agent_orchestrator.get_tracker", return_value=mock_tracker):
            result = budget_aware_route("some prompt", task_type="general")
    assert result["best_provider"] is None

```

### 📄 `backend/tests/test_agent_tools.py`

```py
"""
Tests for tools/agent_tools.py — SupremeAI Tools
"""

from __future__ import annotations

import pytest

from tools.agent_tools import (
    SUPREME_TOOLS,
    check_system_health,
    execute_python_code,
    search_database,
)


class TestSearchDatabase:
    @pytest.mark.asyncio
    async def test_search_database_returns_result(self):
        result = await search_database("test query")
        assert isinstance(result, str)
        assert "matching records" in result

    @pytest.mark.asyncio
    async def test_search_database_includes_query(self):
        result = await search_database("deployment status")
        assert "deployment" in result


class TestCheckSystemHealth:
    def test_returns_status_string(self):
        result = check_system_health()
        assert isinstance(result, str)
        assert "ONLINE" in result

    def test_includes_resource_metrics(self):
        result = check_system_health()
        assert "CPU" in result
        assert "RAM" in result
        assert "Redis" in result


class TestExecutePythonCode:
    def test_returns_execution_result(self):
        result = execute_python_code("print('hello')")
        assert isinstance(result, str)
        assert "Execution successful" in result

    def test_includes_sandbox_reference(self):
        result = execute_python_code("print('test')")
        assert "SupremeAI Sandbox" in result


class TestSupremeTools:
    def test_tools_list_contains_all_tools(self):
        assert len(SUPREME_TOOLS) == 3
        assert search_database in SUPREME_TOOLS
        assert check_system_health in SUPREME_TOOLS
        assert execute_python_code in SUPREME_TOOLS

    def test_tools_are_callable(self):
        for tool in SUPREME_TOOLS:
            assert callable(tool)

```


---

## 4. 🐛 Identified Vulnerabilities & Edge Cases

*Run external AI prompt against Section 3 above to populate.*

---

## 5. 🛠️ Recommended Delta Patches & Actions

*Pending audit execution.*

---
*Generated automatically by SupremeAI 2.0 Audit Generator Script.*
