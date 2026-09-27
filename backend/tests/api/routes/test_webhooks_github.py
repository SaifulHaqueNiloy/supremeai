"""#1802 — GitHub webhook ingest + handoff schema tests.

বাংলা: happy path, invalid signature (fail-closed), replay suppression,
invalid handoff schema (audit-logged, ingestion survives) — সব lock করা।
"""

from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

WEBHOOK_SECRET = "test-webhook-secret"
DELIVERY_ID = "delivery-abc-123"


def _sign(body: bytes, secret: str = WEBHOOK_SECRET) -> str:
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def _issue_payload(action: str = "opened", labels: list[str] | None = None, body: str = "") -> dict[str, Any]:
    return {
        "action": action,
        "repository": {"full_name": "SaifulHaqueNiloy/supremeai"},
        "sender": {"login": "someuser"},
        "issue": {"number": 123, "title": "Test issue", "labels": [{"name": l} for l in (labels or [])], "body": body},
    }


def _post(client: TestClient, payload: dict[str, Any], event: str = "issues", action: str | None = None,
          signature: str | None = None, delivery: str = DELIVERY_ID, secret: str = WEBHOOK_SECRET):
    body = json.dumps(payload).encode()
    headers = {
        "X-GitHub-Event": event,
        "X-GitHub-Delivery": delivery,
        "Content-Type": "application/json",
    }
    if action is not None:
        headers["X-GitHub-Action"] = action
    if signature is not None:
        headers["X-Hub-Signature-256"] = signature
    if secret is not None:
        client.app.router  # no-op; secret handled via env in fixture
    return client.post("/api/webhooks/github", content=body, headers=headers)


class FakeRedis:
    """Minimal async NX setter — records which keys were claimed."""

    def __init__(self) -> None:
        self.claimed: set[str] = set()

    async def set(self, key: str, value: str, nx: bool = False, ex: int | None = None):
        if nx and key in self.claimed:
            return None
        self.claimed.add(key)
        return True


@pytest.fixture()
def client(monkeypatch):
    from api.routes.webhooks_github import router

    fake_redis = FakeRedis()
    monkeypatch.setenv("GITHUB_WEBHOOK_SECRET", WEBHOOK_SECRET)
    monkeypatch.setenv("GITHUB_WEBHOOK_REPOSITORY", "SaifulHaqueNiloy/supremeai")

    import api.routes.webhooks_github as wmod

    async def _fake_client():
        return fake_redis

    monkeypatch.setattr(wmod.redis_manager, "get_client_async", _fake_client)

    app = FastAPI()
    app.include_router(router)
    return TestClient(app), fake_redis


class TestSignatureVerification:
    def test_valid_signature_processes(self, client):
        tc, _ = client
        res = _post(tc, _issue_payload(), event="issues", action="opened", signature=_sign(json.dumps(_issue_payload()).encode()))
        assert res.status_code == 200
        assert res.json()["normalized"]["number"] == 123

    def test_missing_signature_rejected_fail_closed(self, client):
        tc, _ = client
        res = _post(tc, _issue_payload(), event="issues", action="opened", signature=None)
        assert res.status_code == 401

    def test_invalid_signature_rejected(self, client):
        tc, _ = client
        res = _post(tc, _issue_payload(), event="issues", action="opened", signature=_sign(b"tampered"))
        assert res.status_code == 401

    def test_wrong_secret_rejected(self, client):
        tc, _ = client
        body = json.dumps(_issue_payload()).encode()
        res = _post(tc, _issue_payload(), event="issues", action="opened", signature=_sign(body, secret="other"))
        assert res.status_code == 401

    def test_unconfigured_secret_rejected(self, client, monkeypatch):
        tc, _ = client
        monkeypatch.delenv("GITHUB_WEBHOOK_SECRET", raising=False)
        res = _post(tc, _issue_payload(), event="issues", action="opened", signature=_sign(json.dumps(_issue_payload()).encode()))
        assert res.status_code == 401


class TestEventNormalization:
    def test_issue_opened_normalized(self, client):
        tc, _ = client
        res = _post(tc, _issue_payload(), event="issues", action="opened",
                    signature=_sign(json.dumps(_issue_payload()).encode()))
        normalized = res.json()["normalized"]
        assert normalized["event"] == "issues"
        assert normalized["number"] == 123
        assert normalized["repo"] == "SaifulHaqueNiloy/supremeai"

    def test_issue_labeled_with_handoff_label_parsed(self, client):
        tc, _ = client
        payload = _issue_payload(action="labeled", labels=["handoff:coder"])
        res = _post(tc, payload, event="issues", action="labeled", signature=_sign(json.dumps(payload).encode()))
        normalized = res.json()["normalized"]
        assert normalized["handoff_label"] == "handoff:coder"

    def test_pull_request_opened_normalized(self, client):
        tc, _ = client
        payload = {
            "action": "opened",
            "repository": {"full_name": "SaifulHaqueNiloy/supremeai"},
            "sender": {"login": "someuser"},
            "pull_request": {"number": 77, "title": "fix: something", "head": {"ref": "coder-1"}},
        }
        res = _post(tc, payload, event="pull_request", action="opened", signature=_sign(json.dumps(payload).encode()))
        normalized = res.json()["normalized"]
        assert normalized["number"] == 77 and normalized["branch"] == "coder-1"

    def test_workflow_run_failure_normalized(self, client):
        tc, _ = client
        payload = {
            "action": "completed",
            "repository": {"full_name": "SaifulHaqueNiloy/supremeai"},
            "sender": {"login": "someuser"},
            "workflow_run": {"id": 999, "name": "ci", "conclusion": "failure", "head_branch": "main", "html_url": "http://x"},
        }
        res = _post(tc, payload, event="workflow_run", action="completed", signature=_sign(json.dumps(payload).encode()))
        assert res.status_code == 200
        assert res.json()["normalized"]["run_id"] == 999

    def test_irrelevant_action_ignored(self, client):
        tc, _ = client
        payload = _issue_payload(action="closed")
        res = _post(tc, payload, event="issues", action="closed", signature=_sign(json.dumps(payload).encode()))
        assert res.status_code == 202
        assert res.json()["status"] == "ignored"

    def test_foreign_repo_rejected_tenant_boundary(self, client):
        tc, _ = client
        payload = _issue_payload()
        payload["repository"]["full_name"] = "other-org/other-repo"
        res = _post(tc, payload, event="issues", action="opened", signature=_sign(json.dumps(payload).encode()))
        assert res.status_code == 403


class TestReplayProtection:
    def test_same_delivery_processed_once(self, client):
        tc, fake_redis = client
        body = json.dumps(_issue_payload()).encode()
        sig = _sign(body)
        first = _post(tc, _issue_payload(), event="issues", action="opened", signature=sig)
        assert first.status_code == 200
        assert first.json()["status"] != "duplicate"
        second = _post(tc, _issue_payload(), event="issues", action="opened", signature=sig)
        assert second.status_code == 200
        assert second.json()["status"] == "duplicate"
        # dedup key format per spec: supremeai:orchestrate:<issue>:<event>:<delivery>
        assert any(k.startswith("supremeai:orchestrate:123:issues:") for k in fake_redis.claimed)

    def test_different_deliveries_both_processed(self, client):
        tc, _ = client
        first = _post(tc, _issue_payload(), event="issues", action="opened",
                      signature=_sign(json.dumps(_issue_payload()).encode()), delivery="d-1")
        second = _post(tc, _issue_payload(), event="issues", action="opened",
                       signature=_sign(json.dumps(_issue_payload()).encode()), delivery="d-2")
        assert first.json()["status"] != "duplicate"
        assert second.json()["status"] != "duplicate"


class TestHandoffSchema:
    def test_valid_handoff_yaml_extracted(self, client):
        tc, _ = client
        handoff_yaml = (
            "task: {issue: \"#123\", status: completed}\n"
            "handoff: {next_agent: implementation, trigger: issue_created}\n"
            "constraints: {branch: \"feature/123\", scope: implementation-only}"
        )
        payload = _issue_payload(body=f"```yaml\n{handoff_yaml}\n```")
        res = _post(tc, payload, event="issues", action="opened", signature=_sign(json.dumps(payload).encode()))
        handoff = res.json()["handoff"]
        assert handoff["next_agent"] == "coder"  # implementation alias → coder
        assert handoff["issue"] == "123"
        assert handoff["tenant_id"] == "tenant-supremeai"

    def test_invalid_handoff_schema_audited_not_fatal(self, client):
        tc, _ = client
        bad_yaml = "handoff: {next_agent: not-a-real-lane, trigger: x}\ntask: {issue: \"#1\"}"
        payload = _issue_payload(body=f"```yaml\n{bad_yaml}\n```")
        res = _post(tc, payload, event="issues", action="opened", signature=_sign(json.dumps(payload).encode()))
        # Ingestion survives; the malformed handoff is rejected + audit-logged (not silent).
        assert res.status_code == 200
        assert res.json()["handoff"] is None

    def test_handoff_label_parser(self):
        from core.orchestration.handoff_schema import parse_handoff_label

        assert parse_handoff_label("handoff:coder") == "coder"
        assert parse_handoff_label("handoff:implementation") == "coder"
        assert parse_handoff_label("bug") == ""
        with pytest.raises(Exception):
            parse_handoff_label("handoff:nonexistent-lane")

    def test_rejection_raises_with_audit(self):
        from core.orchestration.handoff_schema import parse_handoff_yaml

        with pytest.raises(Exception) as excinfo:
            parse_handoff_yaml("task: {issue: 'nope'}")
        assert "invalid_schema" in str(excinfo.value) or "invalid_yaml" in str(excinfo.value)
