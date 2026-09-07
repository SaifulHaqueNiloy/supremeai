from __future__ import annotations

from dataclasses import dataclass, field
from threading import RLock
from typing import Any


@dataclass(frozen=True)
class EffectivePolicy:
    rules: dict[str, Any]
    features: dict[str, bool]
    sources: dict[str, str] = field(default_factory=dict)


class ConfigurablePolicyStore:
    """Small canonical policy store; replace persistence without changing callers."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._admin_rules: dict[str, Any] = {
            "task_mode": "approval_first",
            "allow_read_only": True,
            "allow_submissions": True,
            "allow_uploads": True,
            "manual_only_terms": ["payment", "pay", "password", "security setting", "delete account", "wire transfer"],
            "approval_terms": ["post", "publish", "send", "submit", "upload", "book"],
        }
        self._features: dict[str, bool] = {
            "browser_tasks": True,
            "social_tasks": True,
            "dashboard_mutations": True,
        }
        self._user_rules: dict[str, dict[str, Any]] = {}

    def snapshot(self, user_id: str | None = None) -> EffectivePolicy:
        with self._lock:
            rules = dict(self._admin_rules)
            features = dict(self._features)
            sources = {key: "admin" for key in rules}
            if user_id and user_id in self._user_rules:
                for key, value in self._user_rules[user_id].items():
                    rules[key] = value
                    sources[key] = "user"
            return EffectivePolicy(rules=rules, features=features, sources=sources)

    def update_admin(self, rules: dict[str, Any] | None = None, features: dict[str, bool] | None = None) -> EffectivePolicy:
        with self._lock:
            if rules:
                self._admin_rules.update(rules)
            if features:
                self._features.update({key: bool(value) for key, value in features.items()})
            return self.snapshot()

    def update_user(self, user_id: str, rules: dict[str, Any]) -> EffectivePolicy:
        with self._lock:
            self._user_rules[user_id] = dict(rules)
            return self.snapshot(user_id)


policy_store = ConfigurablePolicyStore()


def get_effective_policy(user_id: str | None = None) -> EffectivePolicy:
    return policy_store.snapshot(user_id)


__all__ = ["EffectivePolicy", "ConfigurablePolicyStore", "policy_store", "get_effective_policy"]
