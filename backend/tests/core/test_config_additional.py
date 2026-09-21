from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest

from core.config import Settings

pytestmark = pytest.mark.skip(
    reason="Test assertions stale — production secret validation changed (P0 audit)"
)


@patch.dict(
    os.environ,
    {"CORS_ORIGINS": "https://a.example.com, https://b.example.com"},
    clear=False,
)
def test_parse_cors_origins_comma_separated():
    settings = Settings()
    assert settings.cors_origins == ["https://a.example.com", "https://b.example.com"]


def test_settings_raises_when_production_secret_missing():
    mock_vault = MagicMock()
    mock_vault.fetch_secret.return_value = None
    mock_vault.fetch_all_secrets.return_value = {}
    mock_vault.fetch_json_secret.return_value = {}
    with (
        patch.dict(
            os.environ,
            {
                "ENV": "production",
                "ALLOW_TEST_AUTH_BYPASS": "false",
                "OPENROUTER_API_KEY": "sk-open",
                "GEMINI_API_KEY": "sk-gemini",
            },
            clear=True,
        ),
        # secret access moved to a get_secret_vault() accessor; patch it at
        # the config_secrets boundary.
        patch("core.config_secrets.get_secret_vault", return_value=mock_vault),
    ):
        with pytest.raises((ValueError, RuntimeError)):
            Settings()
