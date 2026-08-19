# বাংলা মন্তব্য: core module-এর কম-কভার লাইন কভার করার জন্য অতিরিক্ত টেস্টসমূহ
import asyncio
import contextlib
import json
import os
import sys
import time
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.messaging.event_bus import ErrorContext

# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _isolate_test_env(monkeypatch):
    monkeypatch.setenv("ENV", "test")
    monkeypatch.setenv("SUPREMEAI_JWT_SECRET", "test-secret-placeholder")
    monkeypatch.setenv("SUPREMEAI_ADMIN_PASSWORD_HASH", "")
    monkeypatch.delenv("ENCRYPTION_KEY", raising=False)
    yield
    return


# ========================== swarm_orchestrator.py (additional) ==========================


class TestSwarmOrchestratorCircuitBreakerIntegration:
    @pytest.mark.anyio
    async def test_execute_task_handles_circuit_breaker_open(self):
        from core.orchestration.swarm_orchestrator import SwarmOrchestrator
        from core.resilience.circuit_breaker import (
            CircuitBreakerOpenError,
            CircuitBreakerState,
        )

        orchestrator = SwarmOrchestrator()

        orchestrator.circuit_breaker.state = "OPEN"

        # Mock _synthesize_tool to avoid LLM call
        with (
            patch.object(
                orchestrator,
                "_synthesize_tool",
                new_callable=AsyncMock,
                return_value={"agent_name": "mocked"},
            ),
            patch.object(
                orchestrator.agents["architect"],
                "run",
                new_callable=AsyncMock,
                side_effect=CircuitBreakerOpenError("circuit open", state=CircuitBreakerState.OPEN),
            ),
            patch.object(
                orchestrator.agents["reflection"],
                "reflect_and_persist",
                new_callable=AsyncMock,
            ),
        ):
            # We verify that the circuit breaker error path is reached
            workspace = await orchestrator.execute_task("write a python script", "uid")
            # বাংলা মন্তব্য: সার্কিট ব্রেকার রিয়েল এক্সেপশন মেসেজ "circuit breaker" হ্যান্ডেল করার জন্য অ্যাসারশন আপডেট করা হলো।
            assert "circuit open" in workspace.errors[0] or "circuit breaker" in workspace.errors[0].lower()
