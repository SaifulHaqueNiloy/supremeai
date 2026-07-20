"""
Tests for core/gcp_firestore.py
Focus: CRUD queue operations and document mapping.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from core.gcp_firestore import GCPFirestoreVerificationQueue


# ── Helpers ───────────────────────────────────────────────────────────────────


class FakeFirestoreClient:
    def __init__(self):
        self.collections: dict[str, dict[str, dict]] = {}

    def collection(self, name):
        return FakeCollection(self.collections.setdefault(name, {}))


class FakeCollection:
    def __init__(self, data):
        self.data = data

    def document(self, doc_id):
        return FakeDocument(self.data.setdefault(doc_id, {}))


class FakeDocument:
    def __init__(self, data):
        self.data = data

    def get(self):
        doc = MagicMock()
        doc.exists = bool(self.data)
        doc.to_dict.return_value = self.data.copy()
        return doc

    def set(self, value, merge=False):
        self.data.update(value)

    def delete(self):
        self.data.clear()


# ── GCPFirestoreVerificationQueue ─────────────────────────────────────────────


@pytest.mark.anyio
async def test_enqueue_adds_document():
    queue = GCPFirestoreVerificationQueue(project_id="test-project")
    mock_client = FakeFirestoreClient()
    with patch("core.gcp_firestore.get_firestore_client", return_value=mock_client):
        queue._client = mock_client
        await queue.enqueue("task_1", {"url": "http://example.com"}, priority=1, metadata={})

    # Verify task persisted
    tasks = await queue.get_pending(limit=10)
    assert len(tasks) == 1
    assert tasks[0]["task_id"] == "task_1"


@pytest.mark.anyio
async def test_peek_does_not_remove():
    queue = GCPFirestoreVerificationQueue(project_id="test-project")
    mock_client = FakeFirestoreClient()
    with patch("core.gcp_firestore.get_firestore_client", return_value=mock_client):
        queue._client = mock_client
        await queue.enqueue("task_1", {}, priority=1, metadata={})
        peeked = await queue.peek(limit=1)
        again = await queue.peek(limit=1)

    assert len(peeked) == 1
    assert len(again) == 1


@pytest.mark.anyio
async def test_mark_verified_updates_status():
    queue = GCPFirestoreVerificationQueue(project_id="test-project")
    mock_client = FakeFirestoreClient()
    with patch("core.gcp_firestore.get_firestore_client", return_value=mock_client):
        queue._client = mock_client
        await queue.enqueue("task_1", {}, priority=1, metadata={})
        ok = await queue.mark_verified("task_1")
        assert ok is True


@pytest.mark.anyio
async def test_delete_removes_task():
    queue = GCPFirestoreVerificationQueue(project_id="test-project")
    mock_client = FakeFirestoreClient()
    with patch("core.gcp_firestore.get_firestore_client", return_value=mock_client):
        queue._client = mock_client
        await queue.enqueue("task_1", {}, priority=1, metadata={})
        await queue.delete("task_1")
        tasks = await queue.get_pending(limit=10)
        assert len(tasks) == 0


@pytest.mark.anyio
async def test_stats_returns_counts():
    queue = GCPFirestoreVerificationQueue(project_id="test-project")
    mock_client = FakeFirestoreClient()
    with patch("core.gcp_firestore.get_firestore_client", return_value=mock_client):
        queue._client = mock_client
        await queue.enqueue("t1", {}, priority=1, metadata={})
        await queue.enqueue("t2", {}, priority=1, metadata={})
        stats = await queue.stats()
    assert "pending" in stats or "total" in stats


def test_provider_name():
    queue = GCPFirestoreVerificationQueue(project_id="test-project")
    assert "firestore" in queue.provider.lower()
