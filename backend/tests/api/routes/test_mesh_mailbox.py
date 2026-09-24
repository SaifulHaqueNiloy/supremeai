"""MESH-3 (issue #927) — /api/v1/mesh/* Agent Mailbox REST endpoints tests.

বাংলা সারসংক্ষেপ:
------------------
Tower agent-to-agent messaging-এর REST contract যাচাই:
1. POST /messages → 201 direct send; inbox-এ কেবল প্রকৃত recipient পায়
2. GET /messages/inbox → unread_only filter + limit
3. POST /messages/{id}/ack → 200 idempotent; 403 wrong recipient; 404 unknown id
4. reply_to threading → 201; অজানা reply_to → 422; cross-tenant reply_to → 422
5. TTL expiry → inbox-এ আর আসে না; POST /messages/purge → purged count
6. Tenant isolation → একই agent id দুই tenant-এ পৃথক inbox; header/payload mismatch → 403
7. Role broadcast (to_agent="*") → শুধু নির্দিষ্ট role পায়
8. Topic pub/sub → subscribe না করলে broadcast দৃশ্যমান নয়
9. Validation → 422 (invalid role / TTL out-of-range / oversize body)
10. GET /subscriptions + GET /messages/stats

কোনো fake/mock নেই — আসল AgentMailbox (in-memory) + FastAPI TestClient দিয়ে।
"""

from __future__ import annotations

import time
import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routes.mesh_mailbox import router as mailbox_router
from core.agent_mailbox import (
    AgentMailbox,
    get_agent_mailbox,
    reset_agent_mailbox_for_tests,
)

BASE = "/api/v1/mesh"


def _make_app(mailbox: AgentMailbox) -> tuple[FastAPI, TestClient]:
    """নতুন FastAPI app — mailbox router + fresh instance (test isolation)।"""
    app = FastAPI()
    app.include_router(mailbox_router)
    app.dependency_overrides[get_agent_mailbox] = lambda: mailbox
    return app, TestClient(app)


class MeshMailboxEndpointTest(unittest.TestCase):
    """Agent Mailbox REST endpoints-এর ব্যাপক contract যাচাই।"""

    def setUp(self) -> None:
        self.mailbox = AgentMailbox()
        self.app, self.client = _make_app(self.mailbox)
        self.app.dependency_overrides[get_agent_mailbox] = lambda: self.mailbox

    def tearDown(self) -> None:
        self.app.dependency_overrides.clear()
        reset_agent_mailbox_for_tests()

    def _send(self, **overrides) -> dict:
        body = {"from_agent": "planner-1", "to_agent": "coder-1", "body": {"task": "build"}}
        body.update(overrides)
        res = self.client.post(f"{BASE}/messages", json=body)
        self.assertEqual(res.status_code, 201, res.text)
        return res.json()["message"]

    def _inbox(self, agent_id: str, **params) -> dict:
        res = self.client.get(f"{BASE}/messages/inbox", params={"agent_id": agent_id, **params})
        self.assertEqual(res.status_code, 200, res.text)
        return res.json()

    # ── 1. direct send + inbox ───────────────────────────────────────────────
    def test_send_201_and_recipient_inbox(self) -> None:
        msg = self._send()
        self.assertTrue(msg["message_id"].startswith("msg-"))
        self.assertEqual(msg["to_agent"], "coder-1")
        self.assertFalse(msg["acked"])

        inbox = self._inbox("coder-1")
        self.assertEqual(inbox["count"], 1)
        self.assertEqual(inbox["messages"][0]["message_id"], msg["message_id"])
        self.assertEqual(inbox["messages"][0]["body"], {"task": "build"})

    def test_inbox_hides_messages_for_other_agents(self) -> None:
        self._send()
        self.assertEqual(self._inbox("coder-2")["count"], 0)
        self.assertEqual(self._inbox("planner-1")["count"], 0)

    def test_inbox_unread_only_filter(self) -> None:
        msg = self._send()
        self.assertEqual(self._inbox("coder-1", unread_only="true")["count"], 1)
        res = self.client.post(
            f"{BASE}/messages/{msg['message_id']}/ack", json={"agent_id": "coder-1"}
        )
        self.assertEqual(res.status_code, 200, res.text)
        self.assertTrue(res.json()["acked"])
        self.assertEqual(self._inbox("coder-1", unread_only="true")["count"], 0)
        self.assertEqual(self._inbox("coder-1")["count"], 1, "acked message still visible")

    # ── 2. ack guards ────────────────────────────────────────────────────────
    def test_ack_idempotent_and_wrong_recipient_403(self) -> None:
        msg = self._send()
        first = self.client.post(
            f"{BASE}/messages/{msg['message_id']}/ack", json={"agent_id": "coder-1"}
        ).json()
        second = self.client.post(
            f"{BASE}/messages/{msg['message_id']}/ack", json={"agent_id": "coder-1"}
        ).json()
        self.assertTrue(first["acked"] and second["acked"])
        self.assertEqual(second["acked_at"], first["acked_at"], "idempotent re-ack")

        res = self.client.post(
            f"{BASE}/messages/{msg['message_id']}/ack", json={"agent_id": "intruder"}
        )
        self.assertEqual(res.status_code, 403, res.text)

    def test_ack_unknown_message_404(self) -> None:
        res = self.client.post(f"{BASE}/messages/msg-deadbeef/ack", json={"agent_id": "coder-1"})
        self.assertEqual(res.status_code, 404)

    # ── 3. reply threading ───────────────────────────────────────────────────
    def test_reply_to_threading(self) -> None:
        parent = self._send(to_agent="coder-1")
        reply = self._send(from_agent="coder-1", to_agent="planner-1", reply_to=parent["message_id"])
        self.assertEqual(reply["reply_to"], parent["message_id"])
        inbox = self._inbox("planner-1")
        self.assertEqual(inbox["count"], 1)
        self.assertEqual(inbox["messages"][0]["message_id"], reply["message_id"])

    def test_reply_to_unknown_422(self) -> None:
        res = self.client.post(
            f"{BASE}/messages",
            json={"from_agent": "a", "to_agent": "b", "reply_to": "msg-unknown"},
        )
        self.assertEqual(res.status_code, 422)

    # ── 4. TTL expiry + purge ────────────────────────────────────────────────
    def test_ttl_expiry_removes_message(self) -> None:
        self._send(ttl_seconds=1)
        self.assertEqual(self._inbox("coder-1")["count"], 1)
        time.sleep(1.1)
        # purge আগে চালাও — inbox poll নিজেই expired বার্তা বাদ দিয়ে দেয়
        res = self.client.post(f"{BASE}/messages/purge")
        self.assertEqual(res.status_code, 200, res.text)
        self.assertEqual(res.json()["purged"], 1)
        self.assertEqual(self._inbox("coder-1")["count"], 0, "TTL শেষ হলে বার্তা দৃশ্যমান নয়")

    def test_invalid_ttl_422(self) -> None:
        for bad in (0, -5, 8 * 24 * 3600):
            res = self.client.post(
                f"{BASE}/messages",
                json={"from_agent": "a", "to_agent": "b", "ttl_seconds": bad},
            )
            self.assertEqual(res.status_code, 422, f"ttl={bad} must be rejected")

    # ── 5. tenant isolation ──────────────────────────────────────────────────
    def test_tenant_isolation_partitioned_inbox(self) -> None:
        self._send(to_agent="coder-1")
        self._send(to_agent="coder-1", tenant_id="acme")
        self.assertEqual(self._inbox("coder-1")["count"], 1, "default tenant partition")
        self.assertEqual(self._inbox("coder-1", tenant_id="acme")["count"], 1)
        self.assertEqual(self._inbox("coder-1", tenant_id="globex")["count"], 0)

    def test_tenant_header_payload_mismatch_403(self) -> None:
        res = self.client.post(
            f"{BASE}/messages",
            json={"from_agent": "a", "to_agent": "b", "tenant_id": "acme"},
            headers={"x-tenant-id": "globex"},
        )
        self.assertEqual(res.status_code, 403)

    def test_cross_tenant_ack_403(self) -> None:
        msg = self._send(to_agent="coder-1")
        res = self.client.post(
            f"{BASE}/messages/{msg['message_id']}/ack",
            json={"agent_id": "coder-1", "tenant_id": "acme"},
        )
        self.assertEqual(res.status_code, 403)

    # ── 6. role broadcast ────────────────────────────────────────────────────
    def test_role_broadcast_only_matching_role_sees(self) -> None:
        self._send(to_agent="*", to_role="coder", body={"hello": "coders"})
        self.assertEqual(self._inbox("coder-9", role="coder")["count"], 1)
        self.assertEqual(self._inbox("tester-9", role="tester")["count"], 0, "role gate")
        self.assertEqual(self._inbox("coder-9", role="tester")["count"], 0, "claimed-role spoof")

    def test_invalid_role_422(self) -> None:
        res = self.client.post(
            f"{BASE}/messages",
            json={"from_agent": "a", "to_agent": "*", "to_role": "nobody"},
        )
        self.assertEqual(res.status_code, 422)

    def test_plain_broadcast_visible_to_all(self) -> None:
        self._send(to_agent="*", body={"ping": True})
        self.assertEqual(self._inbox("coder-9", role="coder")["count"], 1)
        self.assertEqual(self._inbox("observer-9", role="observer")["count"], 1)

    # ── 7. topic pub/sub ─────────────────────────────────────────────────────
    def test_topic_broadcast_requires_subscription(self) -> None:
        self._send(to_agent="*", topic="deploy-events", body={"env": "staging"})
        self.assertEqual(self._inbox("coder-1", role="coder")["count"], 0, "unsubscribed")

        res = self.client.post(
            f"{BASE}/subscriptions",
            json={"agent_id": "coder-1", "topics": ["deploy-events"]},
        )
        self.assertEqual(res.status_code, 200, res.text)
        self.assertEqual(res.json()["topics"], ["deploy-events"])
        self.assertEqual(self._inbox("coder-1", role="coder")["count"], 1, "subscribed")

        listing = self.client.get(f"{BASE}/subscriptions", params={"agent_id": "coder-1"})
        self.assertEqual(listing.json()["topics"], ["deploy-events"])

    def test_subscribe_requires_topics_422(self) -> None:
        res = self.client.post(f"{BASE}/subscriptions", json={"agent_id": "a", "topics": ["  "]})
        self.assertEqual(res.status_code, 422)

    # ── 8. validation + stats ────────────────────────────────────────────────
    def test_oversize_body_422(self) -> None:
        res = self.client.post(
            f"{BASE}/messages",
            json={"from_agent": "a", "to_agent": "b", "body": {"pad": "x" * 300_000}},
        )
        self.assertEqual(res.status_code, 422)

    def test_empty_from_agent_422(self) -> None:
        res = self.client.post(f"{BASE}/messages", json={"from_agent": " ", "to_agent": "b"})
        self.assertEqual(res.status_code, 422)

    def test_stats_reports_counts(self) -> None:
        self._send()
        self._send(to_agent="*", topic="t")
        data = self.client.get(f"{BASE}/messages/stats").json()
        self.assertEqual(data["total_messages"], 2)
        self.assertEqual(data["unacked_messages"], 2)
        self.assertEqual(data["per_tenant"]["default"], 2)


if __name__ == "__main__":
    unittest.main()


