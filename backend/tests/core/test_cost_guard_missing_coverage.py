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


# ========================== cost_guard.py ==========================


class TestCostGuardMissingBranches:
    @pytest.mark.asyncio
    async def test_sync_get_branch_when_not_coroutine(self):
        from core.cost_guard import CostGuard

        guard = CostGuard(MagicMock())
        doc_ref = MagicMock()
        snapshot = MagicMock()
        snapshot.exists = True
        snapshot.to_dict.return_value = {"monthly_limit": 10.0, "spent_amount": 1.0}
        doc_ref.get = MagicMock(return_value=snapshot)
        guard._db.collection.return_value.document.return_value = doc_ref

        result = await guard.check_budget("t1", 1.0)
        assert result is True

    @pytest.mark.asyncio
    async def test_validate_budget_accepts_known_tiers(self):
        from core.cost_guard import CostGuard

        guard = CostGuard()
        with patch(
            "core.cache.redis_manager.redis_manager.get_cache",
            new_callable=AsyncMock,
            return_value="0.0",
        ):
            for tier in ("free", "economy", "premium"):
                assert await guard.validate_budget("t1", tier) is True

    @pytest.mark.asyncio
    async def test_validate_budget_returns_true_for_unknown_tier(self):
        from core.cost_guard import CostGuard

        guard = CostGuard()
        assert await guard.validate_budget("t1", "unknown") is True

    @pytest.mark.asyncio
    async def test_check_budget_bypasses_when_no_db(self):
        from core.cost_guard import CostGuard

        guard = CostGuard(db=None)
        result = await guard.check_budget("any-tenant", 999.0)
        assert result is True


