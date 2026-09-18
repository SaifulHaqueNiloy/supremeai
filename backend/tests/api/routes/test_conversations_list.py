"""Wave-3 backend perf — GET /conversations/ limit contract tests.

বাংলা: আগে list route-এ কোনো .limit() ছিল না — ইউজারের সব conversation প্রতি
request-এ নামাত, অথচ একমাত্র frontend caller (UserDashboard) client-side-এ প্রথম
৩টা slice করত। Supabase sandbox-এ নেই, তাই route-এর postgrest builder-chain
contract fake দিয়ে lock করা হলো — test_tenant_admin_isolation.py-র FakeTable
স্টাইল অনুসরণ করে (প্রতিটি builder মেথড self ফেরত দেয়, FakeResult awaitable)।
"""

from __future__ import annotations

from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


class FakeResult:
    """Awaitable-once result — route-এর `await ...execute()` প্যাটার্নের জন্য।"""

    def __init__(self, data: list[dict[str, Any]]) -> None:
        self.data = data

    def __await__(self):
        async def _self() -> FakeResult:
            return self

        return _self().__await__()


class FakeTable:
    """Builder-chain recorder — কোন কোন filter/order/limit জারি হলো তা ধরে রাখে।"""

    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self._rows = rows
        self.ops: list[tuple] = []

    def select(self, *cols: str) -> FakeTable:
        self.ops.append(("select", cols))
        return self

    def eq(self, col: str, val: Any) -> FakeTable:
        self.ops.append(("eq", col, val))
        return self

    def order(self, col: str, desc: bool = False) -> FakeTable:
        self.ops.append(("order", col, desc))
        return self

    def limit(self, size: int) -> FakeTable:
        self.ops.append(("limit", size))
        return self

    def execute(self) -> FakeResult:
        return FakeResult(self._rows)


def _row(i: int) -> dict[str, Any]:
    return {
        "id": f"c{i}",
        "title": f"conv {i}",
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": f"2026-01-0{(i % 9) + 1}T00:00:00Z",
    }


@pytest.fixture()
def client(monkeypatch):
    import api.routes.conversations as cmod
    from api.routes.conversations import router as conversations_router

    captured: dict[str, FakeTable] = {}

    class FakeDB:
        def __init__(self) -> None:
            # route-এর `db.client.table(...)` chain-এর জন্য client attribute দরকার
            self.client = self

        def table(self, name: str) -> FakeTable:
            assert name == "conversations"
            tbl = FakeTable([_row(i) for i in range(6)])
            captured["table"] = tbl
            return tbl

    monkeypatch.setattr(cmod, "SupabaseDB", FakeDB)

    app = FastAPI()
    app.include_router(conversations_router, prefix="/api/v1")
    return TestClient(app), captured


class TestConversationsListLimit:
    def test_default_limit_is_issued_recent_first(self, client):
        import api.routes.conversations as cmod

        tc, captured = client
        res = tc.get("/api/v1/conversations/")
        assert res.status_code == 200
        ops = captured["table"].ops
        # বাংলা: default cap সহ .limit() জারি হয় + আগের মতোই recent-first ordering
        assert ("limit", cmod.DEFAULT_CONVERSATIONS_LIMIT) in ops
        assert ("order", "updated_at", True) in ops
        assert ("eq", "user_id", "test_admin@supremeai.com") in ops

    def test_explicit_limit_param_is_forwarded(self, client):
        tc, captured = client
        res = tc.get("/api/v1/conversations/", params={"limit": 10})
        assert res.status_code == 200
        assert ("limit", 10) in captured["table"].ops

    def test_limit_above_cap_rejected(self, client):
        tc, _ = client
        res = tc.get("/api/v1/conversations/", params={"limit": 101})
        assert res.status_code == 422

    def test_limit_zero_rejected(self, client):
        tc, _ = client
        res = tc.get("/api/v1/conversations/", params={"limit": 0})
        assert res.status_code == 422

    def test_response_shape_unchanged(self, client):
        # বাংলা: Consumer (UserDashboard) response shape-এর উপর নির্ভরশীল —
        # limit যোগ হলেও contract হুবহু একই থাকতে হবে
        tc, _ = client
        res = tc.get("/api/v1/conversations/")
        body = res.json()
        assert isinstance(body, list) and len(body) == 6  # fake server limit apply করে না
        assert set(body[0].keys()) == {"id", "title", "created_at", "updated_at"}
        assert body[0]["id"] == "c0"
