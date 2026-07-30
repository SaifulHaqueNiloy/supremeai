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
sys.modules["typer"] = create_mock_module("typer", is_package=True)
sys.modules["rich"] = create_mock_module("rich", is_package=True)
sys.modules["rich.console"] = create_mock_module("rich.console")
sys.modules["rich.table"] = create_mock_module("rich.table")
sys.modules["rich.panel"] = create_mock_module("rich.panel")
sys.modules["tools.code.image_to_code_react"] = create_mock_module("tools.code.image_to_code_react")

# Mock external SDKs
sys.modules["analytics"] = create_mock_module("analytics")
sys.modules["sentry_sdk"] = create_mock_module("sentry_sdk")
sys.modules["sentry_sdk.integrations"] = create_mock_module("sentry_sdk.integrations", is_package=True)
sys.modules["sentry_sdk.integrations.loguru"] = create_mock_module("sentry_sdk.integrations.loguru")
sys.modules["supabase"] = create_mock_module("supabase", is_package=True)
sys.modules["supabase.client"] = create_mock_module("supabase.client")
sys.modules["alembic"] = create_mock_module("alembic", is_package=True)
sys.modules["alembic.config"] = create_mock_module("alembic.config")
sys.modules["alembic.migration"] = create_mock_module("alembic.migration", is_package=True)
sys.modules["alembic.operations"] = create_mock_module("alembic.operations")
sys.modules["alembic.runtime"] = create_mock_module("alembic.runtime", is_package=True)
sys.modules["alembic.runtime.migration"] = create_mock_module("alembic.runtime.migration")
sys.modules["redis"] = create_mock_module("redis", is_package=True)
sys.modules["redis.asyncio"] = create_mock_module("redis.asyncio", is_package=True)
sys.modules["redis.exceptions"] = create_mock_module("redis.exceptions")
sys.modules["stripe"] = create_mock_module("stripe", is_package=True)
sys.modules["stripe.error"] = create_mock_module("stripe.error")
sys.modules["resend"] = create_mock_module("resend", is_package=True)
sys.modules["resend.emails"] = create_mock_module("resend.emails")
sys.modules["websockets"] = create_mock_module("websockets", is_package=True)
sys.modules["litellm"] = create_mock_module("litellm", is_package=True)
sys.modules["opentelemetry"] = create_mock_module("opentelemetry", is_package=True)
sys.modules["opentelemetry.sdk"] = create_mock_module("opentelemetry.sdk", is_package=True)
sys.modules["opentelemetry.sdk.trace"] = create_mock_module("opentelemetry.sdk.trace", is_package=True)
sys.modules["opentelemetry.instrumentation"] = create_mock_module("opentelemetry.instrumentation", is_package=True)
sys.modules["opentelemetry.instrumentation.fastapi"] = create_mock_module("opentelemetry.instrumentation.fastapi")
sys.modules["opentelemetry.exporter"] = create_mock_module("opentelemetry.exporter", is_package=True)
sys.modules["opentelemetry.exporter.otlp"] = create_mock_module("opentelemetry.exporter.otlp", is_package=True)
sys.modules["opentelemetry.exporter.otlp.proto"] = create_mock_module(
    "opentelemetry.exporter.otlp.proto", is_package=True
)
sys.modules["opentelemetry.exporter.otlp.proto.grpc"] = create_mock_module("opentelemetry.exporter.otlp.proto.grpc")
sys.modules["asyncpg"] = create_mock_module("asyncpg", is_package=True)
sys.modules["tenacity"] = create_mock_module("tenacity", is_package=True)
sys.modules["posthog"] = create_mock_module("posthog", is_package=True)
sys.modules["pandas"] = create_mock_module("pandas", is_package=True)
sys.modules["neo4j"] = create_mock_module("neo4j", is_package=True)
