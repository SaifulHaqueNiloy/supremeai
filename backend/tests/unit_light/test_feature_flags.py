"""Tests for core.feature_flags — pure env-var + percentage rollout logic (no DB required)."""

import pytest

from core import feature_flags as ff_module
from core.feature_flags import FeatureFlags, feature_flags


@pytest.fixture(autouse=True)
def clear_cache():
    feature_flags.reset_cache()
    yield
    feature_flags.reset_cache()


def test_env_flag_truthy(monkeypatch):
    monkeypatch.setenv("SUPREMEAI_MEM0_ENABLED", "true")
    assert ff_module._env_flag("SUPREMEAI_MEM0_ENABLED") is True
    monkeypatch.setenv("SUPREMEAI_MEM0_ENABLED", "1")
    assert ff_module._env_flag("SUPREMEAI_MEM0_ENABLED") is True


def test_env_flag_falsy_and_default(monkeypatch):
    monkeypatch.delenv("SUPREMEAI_MEM0_ENABLED", raising=False)
    assert ff_module._env_flag("SUPREMEAI_MEM0_ENABLED") is False
    assert ff_module._env_flag("SUPREMEAI_MEM0_ENABLED", default=True) is True
    monkeypatch.setenv("SUPREMEAI_MEM0_ENABLED", "no")
    assert ff_module._env_flag("SUPREMEAI_MEM0_ENABLED") is False


def test_mem0_enabled_reads_env(monkeypatch):
    monkeypatch.setenv("SUPREMEAI_MEM0_ENABLED", "yes")
    assert feature_flags.mem0_enabled() is True


def test_all_flag_accessors(monkeypatch):
    monkeypatch.delenv("SUPREMEAI_GRAPHITI_ENABLED", raising=False)
    monkeypatch.delenv("SUPREMEAI_BROWSER_USE_ENABLED", raising=False)
    monkeypatch.delenv("SUPREMEAI_E2B_ENABLED", raising=False)
    monkeypatch.delenv("SUPREMEAI_OPENHANDS_ENABLED", raising=False)
    assert feature_flags.graphiti_enabled() is False
    assert feature_flags.browser_use_enabled() is False
    assert feature_flags.e2b_enabled() is False
    assert feature_flags.openhands_enabled() is False


def test_cache_is_used(monkeypatch):
    monkeypatch.setenv("SUPREMEAI_MEM0_ENABLED", "true")
    assert feature_flags.mem0_enabled() is True
    # Flip env; cached value should still be returned until reset.
    monkeypatch.setenv("SUPREMEAI_MEM0_ENABLED", "false")
    assert feature_flags.mem0_enabled() is True
    feature_flags.reset_cache()
    assert feature_flags.mem0_enabled() is False


def test_db_flag_true_path(monkeypatch):
    monkeypatch.delenv("SUPREMEAI_MEM0_ENABLED", raising=False)
    feature_flags.reset_cache()
    monkeypatch.setattr(ff_module, "_db_flag", lambda name, user_id=None: True)
    assert feature_flags.mem0_enabled(user_id="u1") is True


def test_db_flag_unreachable_returns_none(monkeypatch):
    monkeypatch.delenv("SUPREMEAI_MEM0_ENABLED", raising=False)
    feature_flags.reset_cache()
    monkeypatch.setattr(ff_module, "_db_flag", lambda name, user_id=None: None)
    assert feature_flags.mem0_enabled() is False


def test_is_enabled_full_and_off():
    assert FeatureFlags.is_enabled("adv.i18n_ai_translate") is True
    assert FeatureFlags.is_enabled("nonexistent.flag") is False


def test_is_enabled_partial_rollout(monkeypatch):
    monkeypatch.setattr(FeatureFlags, "ADV_FLAGS", {"adv.x": {"enabled": True, "pct": 0}})
    assert FeatureFlags.is_enabled("adv.x") is False
    monkeypatch.setattr(FeatureFlags, "ADV_FLAGS", {"adv.y": {"enabled": True, "pct": 40}})
    # With pct=40, bucket = abs(hash(user_id)) % 100 < 40 — exercise deterministic path.
    result_a = FeatureFlags.is_enabled("adv.y", user_id="alpha")
    result_b = FeatureFlags.is_enabled("adv.y", user_id="alpha")
    assert result_a == result_b  # deterministic


def test_status_structure():
    status = feature_flags.status()
    assert set(status) == {
        "mem0",
        "graphiti",
        "browser_use",
        "e2b",
        "openhands",
        "advanced_rollout",
    }
