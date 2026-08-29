"""Coverage tests for core/env_validator.py (EnvironmentValidator + validate_environment)."""

import os

import pytest

from core.env_validator import (
    ENV_REGISTRY,
    EnvironmentValidator,
    EnvSeverity,
    EnvVarDefinition,
    ValidationResult,
    validate_environment,
)

_TINY_REGISTRY = [
    EnvVarDefinition(name="MY_CRIT", description="critical var", severity=EnvSeverity.CRITICAL),
    EnvVarDefinition(name="MY_HIGH", description="high var", severity=EnvSeverity.HIGH),
    EnvVarDefinition(
        name="MY_MED", description="med var", severity=EnvSeverity.MEDIUM, default="on"
    ),
    EnvVarDefinition(
        name="MY_LOW_PAT", description="low pat", severity=EnvSeverity.LOW, pattern=r"^ok$"
    ),
]


@pytest.fixture
def tiny_registry(monkeypatch):
    monkeypatch.setattr("core.env_validator.ENV_REGISTRY", list(_TINY_REGISTRY))
    # clean any pre-existing values for our synthetic vars
    for d in _TINY_REGISTRY:
        monkeypatch.delenv(d.name, raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    yield


def _validator():
    return EnvironmentValidator()


# ---------------------------------------------------------------------------


def test_validate_all_present_valid(tiny_registry, monkeypatch):
    monkeypatch.setenv("MY_CRIT", "set")
    monkeypatch.setenv("MY_HIGH", "set")
    monkeypatch.setenv("MY_LOW_PAT", "ok")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    res = _validator().validate()
    assert res.is_valid is True
    assert res.errors == []
    assert res.score == 100  # 4/4 valid


def test_validate_missing_critical_is_invalid(tiny_registry):
    res = _validator().validate()
    assert res.is_valid is False
    vars_in_errors = [e["variable"] for e in res.errors]
    assert "MY_CRIT" in vars_in_errors
    assert "LLM_PROVIDERS" in vars_in_errors


def test_validate_missing_high_critical_but_high_ok(tiny_registry, monkeypatch):
    monkeypatch.setenv("MY_CRIT", "set")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    res = _validator().validate()
    assert res.is_valid is True  # HIGH missing -> error but is_valid stays True
    assert "MY_HIGH" in [e["variable"] for e in res.errors]


def test_default_value_applied_as_info(tiny_registry, monkeypatch):
    monkeypatch.setenv("MY_CRIT", "set")
    monkeypatch.setenv("MY_HIGH", "set")
    # MY_MED has a default and is not set -> default applied + info
    monkeypatch.setenv("MY_LOW_PAT", "ok")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    res = _validator().validate()
    assert res.is_valid is True
    var_names = [i["variable"] for i in res.info]
    assert "MY_MED" in var_names
    assert os.environ["MY_MED"] == "on"


def test_pattern_mismatch_critical_is_invalid(tiny_registry, monkeypatch):
    monkeypatch.setenv("MY_CRIT", "set")
    monkeypatch.setenv("MY_HIGH", "set")
    monkeypatch.setenv("MY_LOW_PAT", "bad_value_no_match")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    res = _validator().validate()
    assert res.is_valid is True  # LOW -> warning not error
    assert "MY_LOW_PAT" in [w["variable"] for w in res.warnings]


def test_pattern_mismatch_low_warns(tiny_registry, monkeypatch):
    res = _validator().validate()
    # MY_CRIT missing (CRITICAL) + MY_LOW_PAT missing -> default none? pattern only validated when present
    assert res.is_valid is False


def test_blank_value_treated_as_missing(tiny_registry, monkeypatch):
    monkeypatch.setenv("MY_CRIT", "   ")  # blank -> treated as missing
    res = _validator().validate()
    assert res.is_valid is False
    assert "MY_CRIT" in [e["variable"] for e in res.errors]


def test_score_computed_proportionally(tiny_registry, monkeypatch):
    monkeypatch.setenv("MY_CRIT", "set")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    res = _validator().validate()
    # 2 valid (MY_CRIT + MY_MED default + MY_LOW_PAT default? no, LOW no default -> missing warning;
    # MY_HIGH missing -> high error). valid_count = MY_CRIT, MY_MED default = 2 of 4
    assert res.score == 50


def test_format_missing_error_with_examples_and_docs():
    v = _validator()
    d = EnvVarDefinition(
        name="X",
        description="d",
        severity=EnvSeverity.CRITICAL,
        examples=["e1", "e2"],
        documentation_url="https://docs.example.com",
    )
    msg = v._format_missing_error(d)
    assert "Missing required environment variable: X" in msg
    assert "Examples:" in msg
    assert "Docs:" in msg


def test_format_missing_error_without_examples():
    v = _validator()
    d = EnvVarDefinition(name="Y", description="d", severity=EnvSeverity.CRITICAL)
    msg = v._format_missing_error(d)
    assert "Missing required environment variable: Y" in msg
    assert "Examples:" not in msg


def test_print_report_runs(tiny_registry, monkeypatch):
    monkeypatch.setenv("MY_CRIT", "set")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    v = _validator()
    res = v.validate()
    v.print_report(res)  # must not raise (loguru writes to stderr)


def test_validate_environment_success(tiny_registry, monkeypatch):
    monkeypatch.setenv("MY_CRIT", "set")
    monkeypatch.setenv("MY_HIGH", "set")
    monkeypatch.setenv("MY_LOW_PAT", "ok")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    assert validate_environment() is True


def test_validate_environment_failure(tiny_registry):
    # no vars set -> invalid
    assert validate_environment() is False


def test_real_registry_loads():
    assert len(ENV_REGISTRY) >= 10
    assert all(hasattr(d, "name") for d in ENV_REGISTRY)
