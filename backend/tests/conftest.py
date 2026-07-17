import os
import sys

from loguru import logger

# বাংলা মন্তব্য: pytest কালেকশনের সময় loguru-এর ডিফল্ট stderr হ্যান্ডলার যেন I/O error না দেয়, তাই প্রথমেই সেটি রিমুভ করা হলো।
logger.remove()

# Mock external dependencies that are not installed
import sys
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

os.environ["SUPREMEAI_ENCRYPTION_KEY"] = "9llmzMU2XSRhbAS-R__JMW1XLZzc0ll7obD_RqaVwno="
os.environ["ENCRYPTION_KEY"] = "9llmzMU2XSRhbAS-R__JMW1XLZzc0ll7obD_RqaVwno="
os.environ["STRIPE_API_KEY"] = "dummy_stripe_key"
os.environ["STRIPE_WEBHOOK_SECRET"] = "whsec_dummy"
os.environ["OPENROUTER_API_KEY"] = "sk-or-v1-dummy"
os.environ["GEMINI_API_KEY"] = "AIzaSy_dummy"
os.environ["CI_WEBHOOK_SECRET"] = "dummy_ci"
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
    sys.path.insert(0, REPO_ROOT)
if os.path.isdir(SCRIPTS_DIR) and SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)
os.environ.setdefault("OPENROUTER_API_KEY", "mock-key-value")

# বাংলা মন্তব্য: টেস্ট রান করার সময় রিয়াল ডাটাবেস এড়াতে এবং লক হওয়া রোধ করতে ইন-মেমোরি ডাটাবেস সেট করা হলো
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["SUPABASE_DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["SUPABASE_DATABASE_URL_POOLER"] = "sqlite+aiosqlite:///:memory:"

# বাংলা মন্তব্য: env var সেট হওয়ার পরে settings._cached_secrets ক্লিয়ার করা হচ্ছে।
# এটা না করলে settings.supabase_url পুরানো ক্যাশড মান return করতে পারে,
# যার ফলে create_client() রিয়াল Supabase URL-এ নেটওয়ার্ক রিকোয়েস্ট পাঠাবে।
try:
    from core.config import settings, secret_vault
    settings._cached_secrets.clear()
    secret_vault.invalidate_cache()
except Exception as e:
    import warnings
    warnings.warn(f"Failed to clear settings caches during test setup: {e}", UserWarning)




# Mock Google Auth credentials and services globally during tests
from unittest.mock import MagicMock


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

import contextlib

import pytest

from core.security.rbac import RoleBasedAccessControl


_TEST_ENV_DEFAULTS = {
    "ENV": "test",
    "OPENROUTER_API_KEY": "mock_openrouter",
    "HF_API_KEY": "mock_hf",
    "GEMINI_API_KEY": "mock_gemini",
    "DEEPSEEK_API_KEY": "mock_deepseek",
    "GROQ_API_KEY": "mock_groq",
    "NVIDIA_API_KEY": "mock_nvidia",
    "FIRECRAWL_API_KEY": "mock_firecrawl",
    "OLLAMA_URL": "http://127.0.0.1:11434",
    "SUPREMEAI_API_TOKEN": "",
    "SENTRY_DSN": "",
    "GCP_PROJECT_ID": "",
    "GCP_REGION": "",
    "SUPABASE_DATABASE_URL": "sqlite+aiosqlite:///:memory:",
    "SUPABASE_DATABASE_URL_POOLER": "sqlite+aiosqlite:///:memory:",
    "GITHUB_TOKEN": "mock_dummy_token",
    "RENDER_API_KEY": "mock_render_key",
    "ADMIN_AUTHORIZED": "false",
    "RAILWAY_TOKEN": "mock_railway_token",
    "ORACLE_CLOUD_API_KEY": "mock_oracle_key",
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
    from core.app import app
    from api.dependencies import get_current_user_token
    from api.dependencies import verify_autonomous_agent_token

    app.dependency_overrides[get_current_user_token] = lambda: {"sub": "test_admin@supremeai.com", "role": "admin"}
    app.dependency_overrides[verify_autonomous_agent_token] = lambda: {"sub": "test_admin@supremeai.com", "role": "admin"}
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
    from sqlalchemy.ext.compiler import compiles
    from sqlalchemy.dialects.postgresql import JSONB
    from sqlalchemy.types import JSON  # noqa: F401
    import sqlalchemy.dialects.sqlite as sqlite_dialect  # noqa: F401

    @compiles(JSONB, "sqlite")
    def compile_jsonb_sqlite(type_, compiler, **kw):
        return "JSON"

    from database.session import engine
    from models.base import Base

    # বাংলা মন্তব্য: সব মডেল স্পষ্টভাবে ইম্পোর্ট করা হলো যাতে Base.metadata তে রেজিস্ট্রি হয়
    import models.admin
    import models.agent_session
    import models.api_key
    import models.byoc_payloads
    import models.ci_report
    import models.deployment_logs
    import models.dynamic_agent
    import models.error_remediation
    import models.evolution
    import models.execution_log
    import models.execution_policy
    import models.handoff_event
    import models.integration
    import models.local_model_handler
    import models.morphic
    import models.pending_tasks
    import models.selector_healing_event
    import models.sentinel
    import models.shared_workspace
    import models.system_config
    import models.target_platform_credential
    import models.voice_interaction
    # বাংলা: wallet.py তে UserWallet ও TransactionLedgerEntry (SQLAlchemy) আছে — সরাসরি ইম্পোর্ট করো
    import models.wallet  # UserWallet + TransactionLedgerEntry (SQLAlchemy) আছে এখানে

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)  # পরিষ্কার শুরু নিশ্চিত করতে
        await conn.run_sync(Base.metadata.create_all)  # সব টেবিল তৈরি
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
    from core.config import settings
    from core.config import secret_vault

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
    from unittest.mock import patch, MagicMock
    import os

    # নিশ্চিত করো env-এ URL/KEY নেই যাতে create_client কল না হয়
    old_url = os.environ.get("SUPABASE_URL", "")
    old_key = os.environ.get("SUPABASE_KEY", "")
    os.environ["SUPABASE_URL"] = ""
    os.environ["SUPABASE_KEY"] = ""

    with patch("database.supabase_client.create_client") as mock_create, \
         patch("database.supabase_client.SupabaseDB.__init__", return_value=None) as mock_init:
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
