"""Test Data Factories for SupremeAI Test Suite.

Provides lightweight, zero-cost, reusable factory classes and fixtures
for testing users, agents, tasks, and auth tokens without database hits.
"""

import uuid
from datetime import UTC, datetime, timezone
from typing import Any


class UserFactory:
    """Factory for creating mock user entities and auth payloads."""

    @staticmethod
    def create(
        user_id: str | None = None,
        email: str = "testuser@supremeai.app",
        role: str = "user",
        tier: str = "free",
        is_active: bool = True,
        **extra: Any,
    ) -> dict[str, Any]:
        uid = user_id or f"usr_{uuid.uuid4().hex[:12]}"
        return {
            "id": uid,
            "user_id": uid,
            "email": email,
            "role": role,
            "tier": tier,
            "is_active": is_active,
            "created_at": datetime.now(UTC).isoformat(),
            **extra,
        }

    @classmethod
    def create_admin(cls, **extra: Any) -> dict[str, Any]:
        return cls.create(
            email="admin@supremeai.app",
            role="admin",
            tier="enterprise",
            **extra,
        )


class AgentFactory:
    """Factory for generating mock agent configs and payloads."""

    @staticmethod
    def create(
        agent_id: str | None = None,
        name: str = "Test Agent",
        model: str = "gemini-1.5-flash",
        system_prompt: str = "You are a test assistant.",
        **extra: Any,
    ) -> dict[str, Any]:
        aid = agent_id or f"agt_{uuid.uuid4().hex[:12]}"
        return {
            "id": aid,
            "name": name,
            "model": model,
            "system_prompt": system_prompt,
            "status": "active",
            "created_at": datetime.now(UTC).isoformat(),
            **extra,
        }
