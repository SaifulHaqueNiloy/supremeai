"""Tests for core.rules_mutator — IP blocklist logic with graceful Redis fallback."""

from unittest.mock import MagicMock

import pytest

from core import services as core_services
from core.rules_mutator import RulesMutator


@pytest.fixture(autouse=True)
def clear_redis(monkeypatch):
    monkeypatch.setattr(core_services, "redis_queue", None)


def test_is_ip_blocked_false_when_redis_unavailable():
    assert RulesMutator().is_ip_blocked("1.2.3.4") is False


def test_block_and_release_false_when_redis_unavailable():
    m = RulesMutator()
    assert m.block_ip("1.2.3.4") is False
    assert m.release_ip("1.2.3.4") is False


def test_is_ip_blocked_true_when_redis_returns_blocked(monkeypatch):
    fake_redis = MagicMock()
    fake_redis.configured = True
    fake_redis.get.return_value = "blocked:suspicious_activity"
    monkeypatch.setattr(core_services, "redis_queue", fake_redis)
    assert RulesMutator().is_ip_blocked("9.9.9.9") is True


def test_block_ip_true_when_redis_configured(monkeypatch):
    fake_redis = MagicMock()
    fake_redis.configured = True
    monkeypatch.setattr(core_services, "redis_queue", fake_redis)
    assert RulesMutator().block_ip("9.9.9.9", reason="x") is True
    fake_redis.set.assert_called_once()


def test_release_ip_true_when_redis_configured(monkeypatch):
    fake_redis = MagicMock()
    fake_redis.configured = True
    monkeypatch.setattr(core_services, "redis_queue", fake_redis)
    assert RulesMutator().release_ip("9.9.9.9") is True
