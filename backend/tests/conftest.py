import os
import sys

from loguru import logger

# বাংলা মন্তব্য: pytest কালেকশনের সময় loguru-এর ডিফল্ট stderr হ্যান্ডলার যেন I/O error না দেয়, তাই প্রথমেই সেটি রিমুভ করা হলো।
logger.remove()

# Mock external dependencies that are not installed
import sys
import importlib.machinery
from unittest.mock import MagicMock

def create_mock_module(name, is_package=False):
    m = MagicMock()
    m.__spec__ = importlib.machinery.ModuleSpec(name=name, loader=MagicMock(), is_package=is_package)
    if is_package:
        m.__path__ = []
    return m

sys.modules["slowapi"] = create_mock_module("slowapi", is_package=True)
sys.modules["slowapi.util"] = create_mock_module("slowapi.util")
sys.modules["slowapi.errors"] = create_mock_module("slowapi.errors")
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


@pytest_asyncio.fixture(autouse=True, scope="session")
async def setup_test_database():
    from sqlalchemy.ext.compiler import compiles
    from sqlalchemy.dialects.postgresql import JSONB
    from sqlalchemy.types import JSON
    import sqlalchemy.dialects.sqlite as sqlite_dialect

    @compiles(JSONB, "sqlite")
    def compile_jsonb_sqlite(type_, compiler, **kw):
        return "JSON"

    from database.session import engine
    from models.base import Base
    import importlib
    import pkgutil
    import models

    # Import all modules in the models package so they are registered with Base
    for _, module_name, _ in pkgutil.iter_modules(models.__path__):
        importlib.import_module(f"models.{module_name}")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def async_session():
    from unittest.mock import AsyncMock

    yield AsyncMock()
