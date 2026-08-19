# backend/tests/mcp/conftest.py
# বাংলা মন্তব্য: MCP টেস্ট-সাবপ্যাকেজের শেয়ার্ড ফিক্সচার (test_mcp_servers_integration.py থেকে স্থানান্তরিত)
import pytest


@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    env_vars = {
        "SUPABASE_DATABASE_URL": "postgres://localhost/mydb",
        "RENDER_API_KEY": "test-render-key",
        "RAILWAY_TOKEN": "test-railway-token",
        "ORACLE_CLOUD_API_KEY": "test-oracle-key",
        "ORACLE_REGION": "us-phoenix-1",
        "ADMIN_AUTHORIZED": "true",
        "GITHUB_TOKEN": "test-github-token",
    }
    from core.config import settings

    for k, v in env_vars.items():
        monkeypatch.setenv(k, v)
        try:
            if hasattr(settings, k.lower()):
                setattr(settings, k.lower(), v)
            elif hasattr(settings, k):
                setattr(settings, k, v)
            # Handle extra fields properly if Pydantic model allows it
            elif getattr(settings.model_config, "extra", "ignore") == "allow":
                setattr(settings, k.lower(), v)
        except AttributeError:
            pass
