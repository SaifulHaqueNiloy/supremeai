"""Tests for canonical production target resolution (issue #1132)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from scripts.ci.resolve_production_targets import (
    build_markdown_summary,
    main,
    resolve_targets,
    resolve_targets_from_env,
    write_to_github_env,
)


def test_explicit_overrides_have_highest_precedence():
    targets = resolve_targets(
        explicit_production_url="https://api.custom.example.com/",
        frontend_production_url="https://app.custom.example.com/",
        firebase_project_id="ignored-firebase-project",
        render_core_url="https://ignored-render.onrender.com",
    )
    assert targets.api_origin == "https://api.custom.example.com"
    assert "owner override" in targets.api_source
    assert targets.ui_origin == "https://app.custom.example.com"
    assert "owner override" in targets.ui_source
    assert targets.backend_health_url == "https://api.custom.example.com"
    assert targets.qa_base_url == "https://app.custom.example.com"
    assert targets.health_url == "https://api.custom.example.com/api/v1/health"


def test_firebase_ui_and_infisical_backend():
    targets = resolve_targets(
        firebase_project_id="supremeai-prod-123",
        render_core_url="https://supremeai-core.onrender.com/",
    )
    assert targets.ui_origin == "https://supremeai-prod-123.web.app"
    assert "FIREBASE_PROJECT_ID-derived" in targets.ui_source
    assert targets.api_origin == "https://supremeai-core.onrender.com"
    assert "RENDER_CORE_URL" in targets.api_source
    assert targets.qa_base_url == "https://supremeai-prod-123.web.app"
    assert targets.backend_health_url == "https://supremeai-core.onrender.com"


def test_missing_targets_fail_closed_without_localhost_fallback():
    targets = resolve_targets()
    assert targets.ui_origin == ""
    assert "unresolved" in targets.ui_source
    assert targets.api_origin == ""
    assert "unresolved" in targets.api_source
    assert targets.qa_base_url == ""
    assert targets.backend_health_url == ""
    assert targets.health_url == ""
    # Guarantees no silent localhost fallback
    assert "localhost" not in targets.ui_source
    assert "localhost" not in targets.api_source


def test_distinct_origins_prevent_silent_conflation():
    """Firebase Hosting does not proxy backend API; UI origin must not become API origin by default."""
    targets = resolve_targets(
        firebase_project_id="supremeai-app",
        render_core_url=None,
        allow_same_origin_fallback=False,
    )
    assert targets.ui_origin == "https://supremeai-app.web.app"
    assert targets.api_origin == ""
    assert "unresolved" in targets.api_source


def test_opt_in_same_origin_fallback():
    """Same-origin fallback is only allowed when explicitly requested."""
    targets = resolve_targets(
        frontend_production_url="https://app.supremeai.com",
        render_core_url=None,
        allow_same_origin_fallback=True,
    )
    assert targets.ui_origin == "https://app.supremeai.com"
    assert targets.api_origin == "https://app.supremeai.com"
    assert "same-origin fallback" in targets.api_source


def test_url_sanitization_and_whitespace():
    targets = resolve_targets(
        explicit_production_url="  https://api.example.com///  ",
        frontend_production_url="  https://app.example.com/  ",
    )
    assert targets.api_origin == "https://api.example.com"
    assert targets.ui_origin == "https://app.example.com"


def test_resolve_from_env_mapping():
    env = {
        "PRODUCTION_URL": "https://api.supremeai.com",
        "FIREBASE_PROJECT_ID": "supremeai-cloud",
    }
    targets = resolve_targets_from_env(env)
    assert targets.api_origin == "https://api.supremeai.com"
    assert targets.ui_origin == "https://supremeai-cloud.web.app"


def test_write_to_github_env(tmp_path: Path):
    targets = resolve_targets(
        explicit_production_url="https://api.example.com",
        frontend_production_url="https://app.example.com",
    )
    env_file = tmp_path / "github_env.txt"
    write_to_github_env(targets, str(env_file))

    content = env_file.read_text(encoding="utf-8")
    assert "UI_ORIGIN=https://app.example.com\n" in content
    assert "API_ORIGIN=https://api.example.com\n" in content
    assert "QA_BASE_URL=https://app.example.com\n" in content
    assert "BACKEND_HEALTH_URL=https://api.example.com\n" in content


def test_build_markdown_summary():
    targets = resolve_targets(
        explicit_production_url="https://api.example.com",
        frontend_production_url=None,
    )
    summary = build_markdown_summary(targets)
    assert "🎯 Production Target Resolution" in summary
    assert "✅ CONFIGURED" in summary
    assert "⚠️ UNVERIFIED" in summary


def test_cli_json_output(capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("PRODUCTION_URL", "https://api.example.com")
    monkeypatch.setenv("FIREBASE_PROJECT_ID", "demo-proj")

    exit_code = main(["--json"])
    assert exit_code == 0

    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["api_origin"] == "https://api.example.com"
    assert data["ui_origin"] == "https://demo-proj.web.app"
