"""
Tests for services/escrow_service.py
State-machine and caching contract tests.
"""

from __future__ import annotations

import time

import pytest

from services.escrow_service import (
    ESCROW_TTL,
    RELEASE_TIMEOUT,
    Escrow,
    EscrowService,
    EscrowStatus,
    get_escrow_service,
)


# ── Helpers ───────────────────────────────────────────────────────────────────


class FakeCache:
    def __init__(self):
        self.store: dict[str, dict] = {}
        self.ttls: dict[str, float] = {}

    async def get(self, key: str):
        if key not in self.store:
            return None
        return self.store[key]

    async def set(self, key: str, value, ttl: int | None = None):
        self.store[key] = value
        if ttl:
            self.ttls[key] = time.time() + ttl

    async def delete(self, key: str):
        self.store.pop(key, None)
        self.ttls.pop(key, None)


# ── EscrowService lifecycle ────────────────────────────────────────────────────


@pytest.mark.anyio
async def test_create_escrow_returns_id_and_persists():
    fake_cache = FakeCache()
    svc = EscrowService()
    svc.cache = fake_cache

    escrow_id = await svc.create_escrow(
        payer_id="p1",
        payee_id="p2",
        amount=100.0,
        currency="USD",
        conditions=["delivered", "accepted"],
    )

    assert isinstance(escrow_id, str)
    assert escrow_id.startswith("escrow_")

    data = await fake_cache.get(f"escrow:{escrow_id}")
    assert data["status"] == EscrowStatus.PENDING.value
    assert data["amount"] == 100.0
    assert data["conditions"] == ["delivered", "accepted"]


@pytest.mark.anyio
async def test_fund_escrow_transitions_to_funded():
    fake_cache = FakeCache()
    svc = EscrowService()
    svc.cache = fake_cache

    escrow_id = await svc.create_escrow("p1", "p2", 50.0)
    ok = await svc.fund_escrow(escrow_id, payment_reference="pay_123")
    assert ok is True

    data = await fake_cache.get(f"escrow:{escrow_id}")
    assert data["status"] == EscrowStatus.FUNDED.value


@pytest.mark.anyio
async def test_fund_escrow_missing_id_returns_false():
    svc = EscrowService()
    svc.cache = FakeCache()
    assert await svc.fund_escrow("missing", "ref") is False


@pytest.mark.anyio
async def test_mark_condition_met_requires_funded():
    fake_cache = FakeCache()
    svc = EscrowService()
    svc.cache = fake_cache

    escrow_id = await svc.create_escrow("p1", "p2", 10.0)
    # Cannot mark condition met on pending escrow
    assert await svc.mark_condition_met(escrow_id, 0) is False


@pytest.mark.anyio
async def test_mark_condition_met_sets_condition_met_when_all_satisfied():
    fake_cache = FakeCache()
    svc = EscrowService()
    svc.cache = fake_cache

    escrow_id = await svc.create_escrow("p1", "p2", 10.0, conditions=["c1", "c2"])
    await svc.fund_escrow(escrow_id, "pay_1")
    assert await svc.mark_condition_met(escrow_id, 0) is True
    assert await svc.mark_condition_met(escrow_id, 1) is True

    data = await fake_cache.get(f"escrow:{escrow_id}")
    assert data["status"] == EscrowStatus.CONDITION_MET.value


@pytest.mark.anyio
async def test_release_funds_only_when_condition_met():
    fake_cache = FakeCache()
    svc = EscrowService()
    svc.cache = fake_cache

    escrow_id = await svc.create_escrow("p1", "p2", 10.0)
    assert await svc.release_funds(escrow_id, "admin") is False

    await svc.fund_escrow(escrow_id, "pay_1")
    await svc.mark_condition_met(escrow_id, 0)
    assert await svc.release_funds(escrow_id, "admin") is True

    data = await fake_cache.get(f"escrow:{escrow_id}")
    assert data["status"] == EscrowStatus.RELEASED.value
    assert "released_at" in data
    assert data["released_by"] == "admin"


@pytest.mark.anyio
async def test_dispute_sets_status():
    fake_cache = FakeCache()
    svc = EscrowService()
    svc.cache = fake_cache

    escrow_id = await svc.create_escrow("p1", "p2", 10.0)
    assert await svc.dispute(escrow_id, "not delivered", "p1") is True

    data = await fake_cache.get(f"escrow:{escrow_id}")
    assert data["status"] == EscrowStatus.DISPUTED.value
    assert data["dispute_reason"] == "not delivered"


@pytest.mark.anyio
async def test_get_escrow_returns_none_for_missing():
    svc = EscrowService()
    svc.cache = FakeCache()
    assert await svc.get_escrow("missing") is None


@pytest.mark.anyio
async def test_get_escrow_returns_dataclass():
    fake_cache = FakeCache()
    svc = EscrowService()
    svc.cache = Fake_cache = fake_cache

    escrow_id = await svc.create_escrow("p1", "p2", 10.0)
    escrow = await svc.get_escrow(escrow_id)
    assert isinstance(escrow, Escrow)
    assert escrow.payer_id == "p1"
    assert escrow.status == EscrowStatus.PENDING


@pytest.mark.anyio
async def test_list_escrows_filters_by_role():
    fake_cache = FakeCache()
    svc = EscrowService()
    svc.cache = fake_cache

    e1 = await svc.create_escrow("payer1", "payee1", 10.0)
    e2 = await svc.create_escrow("payer2", "payee1", 20.0)

    payee_escrows = await svc.list_escrows("payee1", role="payee")
    payer_escrows = await svc.list_escrows("payer1", role="payer")

    assert len(payee_escrows) == 2
    assert len(payer_escrows) == 1


@pytest.mark.anyio
async def test_auto_release_check_returns_expired_condition_met():
    fake_cache = FakeCache()
    svc = EscrowService()
    svc.cache = fake_cache

    escrow_id = await svc.create_escrow("p1", "p2", 10.0, expires_in_days=8)
    # Work around: write back clean dataclass-compatible data.
    from datetime import datetime, UTC, timedelta

    data = await fake_cache.get(f"escrow:{escrow_id}")
    data["status"] = EscrowStatus.CONDITION_MET.value
    data["expires_at"] = datetime.now(UTC) - timedelta(days=10)
    data.pop("payment_reference", None)
    await fake_cache.set(f"escrow:{escrow_id}", data)

    ready = await svc.auto_release_check()
    assert escrow_id in ready


# ── Singleton ─────────────────────────────────────────────────────────────────


def test_get_escrow_service_returns_same_instance():
    a = get_escrow_service()
    b = get_escrow_service()
    assert a is b


# ── Constants ─────────────────────────────────────────────────────────────────


def test_escrow_constants():
    assert ESCROW_TTL == 30 * 24 * 3600
    assert RELEASE_TIMEOUT == 7 * 24 * 3600
