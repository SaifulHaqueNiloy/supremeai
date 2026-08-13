"""NightlyChaosAuditor.execute_audit_sequence (workers/chaos_worker.py) এর ইউনিট টেস্ট।

বাংলা: অডিট সিকোয়েন্সের তিনটি ব্রাঞ্চ কভার করা হয়েছে —
(১) স্যান্ডবক্স নিরাপদ + রানটাইম 200 → PASSED (True),
(২) স্যান্ডবক্স বাইপাস শনাক্ত → LOCKED (False),
(৩) রানটাইম 500 → LOCKED (False)।
fuzz_sandbox ও httpx.AsyncClient মক করা হয়েছে; gate_ref=None (firestore নেই)।
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from workers import chaos_worker


def _make_auditor():
    with patch("workers.chaos_worker.get_firestore_db", return_value=None):
        return chaos_worker.NightlyChaosAuditor()


@pytest.mark.asyncio
async def test_audit_passes_when_safe():
    auditor = _make_auditor()
    payloads = [("print('hello')", {"risk": "low"}), ("x = 1", {})]
    fake_resp = MagicMock()
    fake_resp.status_code = 200
    async_client = AsyncMock()
    async_client.post.return_value = fake_resp

    with patch("workers.chaos_worker.generate_fuzz_payloads", return_value=payloads), patch(
        "workers.chaos_worker.run_sandbox_ast_check", return_value=False
    ), patch("workers.chaos_worker.httpx.AsyncClient", return_value=async_client):
        result = await auditor.execute_audit_sequence()

    assert result is True


@pytest.mark.asyncio
async def test_audit_locks_on_sandbox_breach():
    auditor = _make_auditor()
    # বাংলা: স্যান্ডবক্স যদি ম্যালিশিয়াস কোডকে Safe বলে (True রিটার্ন), তবে breach গণ্য হয়
    payloads = [("import os; os.system('rm -rf /')", {"risk": "high"})]
    async_client = AsyncMock()
    async_client.post.return_value = MagicMock(status_code=200)

    with patch("workers.chaos_worker.generate_fuzz_payloads", return_value=payloads), patch(
        "workers.chaos_worker.run_sandbox_ast_check", return_value=True
    ), patch("workers.chaos_worker.httpx.AsyncClient", return_value=async_client):
        result = await auditor.execute_audit_sequence()

    assert result is False


@pytest.mark.asyncio
async def test_audit_locks_on_runtime_server_error():
    auditor = _make_auditor()
    payloads = [("print('ok')", {})]
    fake_resp = MagicMock()
    fake_resp.status_code = 503  # SERVER_ERROR_THRESHOLD (500) এর ওপরে
    async_client = AsyncMock()
    async_client.post.return_value = fake_resp

    with patch("workers.chaos_worker.generate_fuzz_payloads", return_value=payloads), patch(
        "workers.chaos_worker.run_sandbox_ast_check", return_value=False
    ), patch("workers.chaos_worker.httpx.AsyncClient", return_value=async_client):
        result = await auditor.execute_audit_sequence()

    assert result is False


@pytest.mark.asyncio
async def test_audit_locks_when_fuzz_unavailable():
    auditor = _make_auditor()
    async_client = AsyncMock()
    async_client.post.return_value = MagicMock(status_code=200)

    # বাংলা: fuzz_sandbox আনঅভেইলেবল হলে ImportError → LOCKED (False)
    with patch("workers.chaos_worker.generate_fuzz_payloads", None), patch(
        "workers.chaos_worker.run_sandbox_ast_check", None
    ), patch("workers.chaos_worker.httpx.AsyncClient", return_value=async_client):
        result = await auditor.execute_audit_sequence()

    assert result is False
