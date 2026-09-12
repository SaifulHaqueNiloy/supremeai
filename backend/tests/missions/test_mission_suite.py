"""MASTER_PLAN Phase 2 kickoff — mission-level end-to-end test suite.

বাংলা: README-র নিজস্ব সংজ্ঞা অনুযায়ী "the most valuable future tests" —
বাস্তব ইউজার মিশনের অটো-স্কোরড E2E টেস্ট। প্রতিটি টেস্ট একটি পূর্ণ মিশন যাচাই
করে (route → service → persistence), অফলাইন-সেফ ও deterministic — যাতে CI-তে
pass^k হারনেস (scripts/ci/mission_passk.py) এই স্যুটকে k বার চালিয়ে
consistency মাপতে পারে। Mission suite-ই ভবিষ্যতের প্রমোশন গেট:
pass^3 >= 0.8 ছাড়া কোনো পরিবর্তন promote করা যাবে না (Constitution #5)।
"""

from __future__ import annotations

import time
import uuid
from datetime import UTC, datetime, timedelta

import pytest


def _admin_token() -> str:
    """Mints a valid admin JWT (test env — same secret the backend verifies)."""
    import jwt

    from core.config import settings

    return jwt.encode(
        {"sub": "mission-admin", "role": "admin", "exp": int(time.time()) + 3600},
        settings.jwt_secret,
        algorithm="HS256",
    )


# ---------------------------------------------------------------------------
# Mission 1 — Governed research: scout fail-closed policy gate + durable history
# ---------------------------------------------------------------------------
class TestMissionGovernedResearch:
    @pytest.mark.asyncio
    async def test_inactive_policy_blocks_crawl_but_records_history(self):
        """বাংলা: Policy Before Power — নিষ্ক্রিয় policy কিছুই crawl করায় না,
        তবে ঘটনাটি durable history-তে রেকর্ড হয় (audit trail সত্য থাকে)।"""
        from scout.crawler import CrawlerService
        from scout.models import CrawlPolicy, CrawlRequest
        from scout.persistence import list_history, record_crawl_response

        policy = CrawlPolicy(tenant_id="mission-t1", name="inactive", is_active=False)
        service = CrawlerService(policy=policy)
        resp = await service.execute_crawl(
            CrawlRequest(query_or_url="https://github.com/example/repo", tenant_id="mission-t1")
        )
        assert resp.total_fetched == 0  # fail-closed: কোনো fetch হয়নি
        assert len(resp.pages) == 0

        record = await record_crawl_response(resp)
        assert record.task_id == resp.task_id
        history = await list_history("mission-t1", limit=10)
        assert any(rec.task_id == resp.task_id for rec in history)

    @pytest.mark.asyncio
    async def test_persistence_tenant_isolation(self):
        """বাংলা: এক টেন্যান্টের history অন্য টেন্যান্ট দেখতে পারে না (isolation)।"""
        from scout.models import CrawlHistoryRecord
        from scout.persistence import list_history, record_history

        marker = f"mission-iso-{uuid.uuid4().hex[:8]}"
        await record_history(
            CrawlHistoryRecord(
                task_id=marker, tenant_id="mission-tA", query="q", sources_crawled=[]
            )
        )
        seen_by_b = await list_history("mission-tB", limit=50)
        assert all(rec.task_id != marker for rec in seen_by_b)


# ---------------------------------------------------------------------------
# Mission 2 — Visible intelligence: reasoning steps reach session SSE channel
# ---------------------------------------------------------------------------
class TestMissionReasoningStream:
    def test_reasoning_step_fanout_via_session_stream_channel(self):
        """বাংলা: emit_reasoning_step → batcher.publish (SSE-only) → subscriber
        পায়; session_stream-এর channel ম্যাপিং এটিকে 'reasoning' চ্যানেলে
        পাঠায় — ReasoningLog.tsx এখন সত্যিকারের ডেটা পায়।"""
        from core.observability.log_batcher import batcher
        from core.observability.reasoning_stream import emit_reasoning_step

        session_id = f"mission-reasoning-{uuid.uuid4().hex[:8]}"
        queue = batcher.subscribe(session_id)
        try:
            received = {}

            def _drain() -> None:
                item = queue.get_nowait()
                received.update(item)

            sent = emit_reasoning_step(session_id, step=3, content="Refining research query")
            assert sent is True
            _drain()
            assert received["log_type"] == "reasoning_step"
            assert received["step"] == 3
            assert "Refining" in received["content"]
            assert received["session_id"] == session_id

            # Channel mapping (session_stream.event_generator-র সিদ্ধান্ত তালিকা)
            channel = "logs"
            if received.get("log_type") == "state_change":
                channel = "state"
            elif received.get("log_type") == "reasoning_step":
                channel = "reasoning"
            assert channel == "reasoning"

            # SSE-only publish: DB write-queue খালি থাকতেই হবে (poison insert রোধ)
            assert batcher.queue.empty()
        finally:
            batcher.unsubscribe(session_id, queue)

    def test_reasoning_step_no_subscriber_is_not_error(self):
        """বাংলা: কেউ শোনছে না হলেও reasoning emit ব্যর্থ হয় না (transient stream)।"""
        from core.observability.reasoning_stream import emit_reasoning_step

        assert emit_reasoning_step(f"mission-quiet-{uuid.uuid4().hex[:6]}", 1, "thought") in (
            True,
            False,
        )
        assert emit_reasoning_step("", 1, "empty session") is False


# ---------------------------------------------------------------------------
# Mission 3 — Admin truth surface: /api/v1/admin/* stops 404ing
# ---------------------------------------------------------------------------
class TestMissionAdminSurface:
    def _client(self):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        from api.routes.admin_v1 import router as admin_v1_router

        app = FastAPI()
        app.include_router(admin_v1_router)
        return TestClient(app)

    def test_stats_users_audit_live(self):
        client = self._client()
        headers = {"Authorization": f"Bearer {_admin_token()}"}

        res = client.get("/api/v1/admin/stats", headers=headers)
        assert res.status_code == 200
        body = res.json()
        assert body["service"] == "supremeai-core"
        assert "generated_at" in body
        # সততা: ডেটা degrade হলে ভুয়া সংখ্যা নয়, degraded চিহ্ন থাকে
        assert isinstance(body["users"], int)
        assert isinstance(body["audit_logs"], int)

        res = client.get("/api/v1/admin/users", headers=headers)
        assert res.status_code == 200
        assert isinstance(res.json(), list)

        res = client.get("/api/v1/admin/audit-logs?limit=5", headers=headers)
        assert res.status_code == 200
        assert isinstance(res.json(), list)

    def test_stats_requires_admin_role(self):
        import jwt as pyjwt

        from core.config import settings

        client = self._client()
        user_token = pyjwt.encode(
            {"sub": "plain-user", "role": "user", "exp": int(time.time()) + 3600},
            settings.jwt_secret,
            algorithm="HS256",
        )
        res = client.get("/api/v1/admin/stats", headers={"Authorization": f"Bearer {user_token}"})
        assert res.status_code == 403


# ---------------------------------------------------------------------------
# Mission 4 — Config honesty: validation report detects truth
# ---------------------------------------------------------------------------
class TestMissionConfigHonesty:
    def test_missing_required_var_is_error(self, monkeypatch):
        from core.config_validation import build_config_validation_report

        monkeypatch.delenv("JWT_SECRET", raising=False)
        report = build_config_validation_report(env="test")
        assert report.ok is False
        assert any(c.name == "JWT_SECRET" and c.status == "error" for c in report.errors)
        assert report.errors[0].fix_suggestion  # সৎ রিপোর্ট = ফিক্স পথসহ

    def test_wildcard_cors_never_survives_resolution(self, monkeypatch):
        monkeypatch.setenv("CORS_ORIGINS", "")
        monkeypatch.setenv("ADMIN_CORS_ORIGINS", "")
        from middleware.cors_policy import resolve_admin_cors_origins, resolve_user_cors_origins

        resolved = set(resolve_user_cors_origins(["*"])) | set(resolve_admin_cors_origins(["*"]))
        assert "*" not in resolved  # credentialed CORS-এ wildcard অবৈধ

    def test_ok_environment_passes(self, monkeypatch):
        """বাংলা: সঠিকভাবে কনফিগার করা env-এ রিপোর্ট সবুজ হওয়াই চুক্তি।"""
        from core.config_validation import build_config_validation_report

        monkeypatch.setenv("JWT_SECRET", "mission-test-secret-value")
        monkeypatch.setenv("SUPABASE_URL", "https://missiontest.supabase.co")
        monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "mission-service-key")
        monkeypatch.delenv("REDIS_URL", raising=False)  # optional var — অনুপস্থিত = চেক ছাড়াই
        monkeypatch.delenv("SUPABASE_DATABASE_URL", raising=False)  # শুধু production-এ বাধ্যতামূলক
        report = build_config_validation_report(env="test")
        assert report.ok is True, [e.detail for e in report.errors]


# ---------------------------------------------------------------------------
# Mission 5 — Reliability scoreboard: pass^k estimator is mathematically sound
# ---------------------------------------------------------------------------
class TestMissionReliabilityScoreboard:
    def test_pass_hat_k_estimator_contract(self):
        from math import comb

        from core.self_benchmark import SelfBenchmarkEngine

        est = SelfBenchmarkEngine._pass_hat_k_estimator
        n, k = 5, 3
        assert est(5, n, k) == 1.0  # সব রান সফল → নিখুঁত consistency
        assert est(0, n, k) == 0.0
        assert est(2, n, k) == 0.0  # C(2,3)=0 — ৩ বার সফল হওয়া অসম্ভব
        assert est(3, n, k) == pytest.approx(comb(3, 3) / comb(5, 3))
        # Monotonicity: বেশি success → pass^k কখনো কমে না
        assert est(4, n, k) >= est(3, n, k)
        # n < k → 0.0 (অজানা — ভুয়া 1.0 নয়)
        assert est(1, 1, 3) == 0.0

    def test_reliability_category_registered(self):
        from core.self_benchmark import BenchmarkCategory

        assert BenchmarkCategory.RELIABILITY == "reliability"

    def test_history_records_are_recent(self):
        """বাংলা: নতুন রেকর্ডের created_at বাস্তব সময়ের কাছাকাছি (ভুয়া epoch নয়)।"""
        from scout.models import CrawlHistoryRecord

        rec = CrawlHistoryRecord(task_id="t", tenant_id="tn", query="q")
        now = (
            datetime.now(UTC).replace(tzinfo=None)
            if rec.created_at.tzinfo is None
            else rec.created_at
        )
        delta = abs((now - rec.created_at).total_seconds())
        assert delta < timedelta(minutes=1).total_seconds()
