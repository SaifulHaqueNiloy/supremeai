"""Tests for api/routes/websocket_agent.py (DistributedConnectionManager + WS chat endpoint).

Direct-call technique (same as test_api_keys.py): route/manager methods are driven with
minimal stand-ins instead of a full WebSocket transport, so every DoS-protection guard,
the Redis fallback ladder, the preference-analysis pipeline and the chat endpoint loop
run under plain pytest-asyncio.

Also pins two regression guards:
* the DistributedConnectionManager.connect duplicate-definition defect must stay fixed
  (Python silently keeps the LAST def, which used to resurrect the unlocked copy);
* SupabaseDB/llm_gateway/task_queue are patched at the MODULE namespace because the
  endpoint imports them at module level.
"""

import asyncio
import inspect
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from fastapi import WebSocketDisconnect

import api.routes.websocket_agent as ws_agent
import core.config as core_config
from api.routes.websocket_agent import (
    DistributedConnectionManager,
    analyze_and_save_preferences,
    handle_analyze_preferences,
)


class FakeWebSocket:
    """Minimal WebSocket stand-in: scripted inbound messages, recorded outbound."""

    def __init__(self, incoming=None, fail_sends=False):
        self._incoming = list(incoming or [])
        self.sent: list[str] = []
        self.closed: list[tuple[int, str | None]] = []
        self.accepted = False
        self.fail_sends = fail_sends
        self.on_send = None  # optional async callback

    async def accept(self):
        self.accepted = True

    async def close(self, code=1000, reason=None):
        self.closed.append((code, reason))

    async def send_text(self, text):
        if self.fail_sends:
            raise RuntimeError("socket gone")
        self.sent.append(text)
        if self.on_send is not None:
            await self.on_send(text)

    async def receive_text(self):
        if not self._incoming:
            raise WebSocketDisconnect(code=1000)
        item = self._incoming.pop(0)
        if isinstance(item, Exception):
            raise item
        return item

    async def receive_json(self):
        if not self._incoming:
            raise WebSocketDisconnect(code=1000)
        item = self._incoming.pop(0)
        if isinstance(item, Exception):
            raise item
        if isinstance(item, str):
            return json.loads(item)
        return item


@pytest_asyncio.fixture
async def manager():
    instance = DistributedConnectionManager()
    # ru_maxrss of the pytest process routinely exceeds the 100MB default —
    # shadow the memory ceiling so acceptance tests are deterministic.
    instance.MAX_MEMORY_MB = 10**9
    yield instance
    # hygiene: connect() starts the background cleanup task; cancel it so no
    # pending task leaks into the session-loop teardown (Task 18 lesson).
    await instance.shutdown()


@pytest_asyncio.fixture(autouse=True)
async def _shutdown_module_manager():
    """The endpoint tests drive the MODULE-level manager; keep its memory guard
    deterministic and cancel the 60s cleanup task spawned by connect()."""
    ws_agent.manager.MAX_MEMORY_MB = 10**9
    yield
    await ws_agent.manager.shutdown()


def make_request(host="203.0.113.9"):
    return SimpleNamespace(client=SimpleNamespace(host=host))


# ============================================================
# REGRESSION: connect must be defined exactly once (locked copy)
# ============================================================


def test_connect_is_defined_exactly_once():
    """Python keeps the LAST def; a duplicate used to resurrect the unlocked copy."""
    source = inspect.getsource(DistributedConnectionManager)
    assert source.count("    async def connect(") == 1
    # the surviving definition must be the owner's race-condition fix (locked)
    assert "async with self._connection_lock:" in source


# ============================================================
# connect(): accept + bookkeeping
# ============================================================


@pytest.mark.asyncio
async def test_connect_accepts_and_tracks_state(manager):
    ws = FakeWebSocket()
    ok = await manager.connect(ws, "user-1", "10.1.1.1")
    assert ok is True
    assert ws.accepted is True
    assert ws.closed == []
    assert manager.active_connections["user-1"] == [ws]
    assert manager._ip_connections["10.1.1.1"] == 1
    assert manager._connection_ips[id(ws)] == "10.1.1.1"
    assert id(ws) in manager._last_activity


@pytest.mark.asyncio
async def test_connect_rejects_on_memory_pressure(manager):
    ws = FakeWebSocket()
    manager._is_memory_pressure = lambda: True
    ok = await manager.connect(ws, "user-1")
    assert ok is False
    assert ws.accepted is False
    assert ws.closed == [(1013, "Server overloaded")]
    assert "user-1" not in manager.active_connections


@pytest.mark.asyncio
async def test_connect_rejects_total_limit(manager):
    manager.MAX_TOTAL_CONNECTIONS = 0
    ws = FakeWebSocket()
    ok = await manager.connect(ws, "user-1")
    assert ok is False
    assert ws.closed == [(1013, "Too many connections")]


@pytest.mark.asyncio
async def test_connect_rejects_per_user_limit(manager):
    manager.MAX_PER_USER = 1
    first, second = FakeWebSocket(), FakeWebSocket()
    assert await manager.connect(first, "user-1") is True
    assert await manager.connect(second, "user-1") is False
    assert second.closed == [(1013, "Too many connections for user")]
    assert manager.active_connections["user-1"] == [first]


@pytest.mark.asyncio
async def test_connect_rejects_per_ip_limit(manager):
    manager.MAX_PER_IP = 1
    ws_a, ws_b = FakeWebSocket(), FakeWebSocket()
    assert await manager.connect(ws_a, "user-a", "10.9.9.9") is True
    assert await manager.connect(ws_b, "user-b", "10.9.9.9") is False
    assert ws_b.closed == [(1013, "IP limit exceeded")]


# ============================================================
# disconnect() + tracking bookkeeping
# ============================================================


@pytest.mark.asyncio
async def test_disconnect_removes_socket_and_user_entry(manager):
    ws = FakeWebSocket()
    await manager.connect(ws, "user-1", "10.0.0.1")
    manager.disconnect(ws, "user-1", "10.0.0.1")
    assert "user-1" not in manager.active_connections
    assert manager._ip_connections.get("10.0.0.1") in (None, 0)
    assert id(ws) not in manager._connection_ips
    assert id(ws) not in manager._last_activity


@pytest.mark.asyncio
async def test_disconnect_keeps_other_sockets_of_same_user(manager):
    ws1, ws2 = FakeWebSocket(), FakeWebSocket()
    await manager.connect(ws1, "user-1")
    await manager.connect(ws2, "user-1")
    manager.disconnect(ws1, "user-1")
    assert manager.active_connections["user-1"] == [ws2]


def test_disconnect_unknown_socket_is_safe(manager):
    ws = FakeWebSocket()
    manager.disconnect(ws, "ghost-user")  # must not raise


def test_remove_connection_tracking_is_idempotent(manager):
    ws = FakeWebSocket()
    manager._connection_ips[id(ws)] = "10.0.0.5"
    manager._ip_connections["10.0.0.5"] = 1
    manager._last_activity[id(ws)] = 123.0
    manager._remove_connection_tracking(ws)
    manager._remove_connection_tracking(ws)  # second call must not raise / go negative
    assert id(ws) not in manager._last_activity
    assert "10.0.0.5" not in manager._ip_connections


# ============================================================
# IP auth rate limiting
# ============================================================


def test_check_ip_rate_limit_allows_fresh_ip(manager):
    assert manager._check_ip_rate_limit("10.5.5.5") is True


def test_check_ip_rate_limit_blocks_after_max_attempts(manager):
    for _ in range(manager.MAX_AUTH_ATTEMPTS_PER_IP):
        manager._record_auth_attempt("10.5.5.5")
    assert manager._check_ip_rate_limit("10.5.5.5") is False


def test_check_ip_rate_limit_window_drops_old_attempts(manager):
    import time

    stale = time.time() - manager.AUTH_ATTEMPT_WINDOW - 1
    manager._auth_attempts["10.5.5.5"] = [stale] * manager.MAX_AUTH_ATTEMPTS_PER_IP
    assert manager._check_ip_rate_limit("10.5.5.5") is True


# ============================================================
# _authenticate()
# ============================================================


@pytest.mark.asyncio
async def test_authenticate_rate_limited_closes_with_policy_violation(manager):
    for _ in range(manager.MAX_AUTH_ATTEMPTS_PER_IP):
        manager._record_auth_attempt("10.5.5.5")
    ws = FakeWebSocket(incoming=[json.dumps({"type": "auth", "token": "x"})])
    result = await manager._authenticate(ws, "10.5.5.5")
    assert result is None
    assert ws.closed == [(1008, "Rate limited")]


@pytest.mark.asyncio
async def test_authenticate_rejects_wrong_message_type(manager):
    ws = FakeWebSocket(incoming=[json.dumps({"type": "hello"})])
    result = await manager._authenticate(ws, "10.5.5.5")
    assert result is None
    assert ws.closed == [(1008, None)]
    assert len(manager._auth_attempts["10.5.5.5"]) == 1


@pytest.mark.asyncio
async def test_authenticate_rejects_missing_token(manager):
    ws = FakeWebSocket(incoming=[json.dumps({"type": "auth"})])
    result = await manager._authenticate(ws, "10.5.5.5")
    assert result is None
    assert ws.closed == [(1008, None)]


@pytest.mark.asyncio
async def test_authenticate_returns_verified_payload(monkeypatch, manager):
    payload = {"sub": "user-1", "tenant_id": "tenant-1"}
    monkeypatch.setattr(ws_agent, "verify_token_async", AsyncMock(return_value=payload))
    ws = FakeWebSocket(incoming=[json.dumps({"type": "auth", "token": "good"})])
    result = await manager._authenticate(ws, "10.5.5.5")
    assert result == payload


@pytest.mark.asyncio
async def test_authenticate_records_attempt_on_receive_failure(manager):
    ws = FakeWebSocket(incoming=[RuntimeError("malformed frame")])
    result = await manager._authenticate(ws, "10.5.5.5")
    assert result is None
    assert ws.closed == [(1008, None)]
    assert len(manager._auth_attempts["10.5.5.5"]) == 1


# ============================================================
# _get_redis(): graceful degradation ladder
# ============================================================


@pytest.mark.asyncio
async def test_get_redis_returns_existing_client(manager):
    sentinel = object()
    manager.redis = sentinel
    assert await manager._get_redis() is sentinel


@pytest.mark.asyncio
async def test_get_redis_returns_none_without_config(monkeypatch, manager):
    monkeypatch.setattr(
        core_config, "settings", SimpleNamespace(redis_url=None, REDIS_URL=None)
    )
    assert await manager._get_redis() is None


@pytest.mark.asyncio
async def test_get_redis_ignores_placeholder_url(monkeypatch, manager):
    monkeypatch.setattr(
        core_config,
        "settings",
        SimpleNamespace(redis_url="<your-redis-url>", REDIS_URL=None),
    )
    assert await manager._get_redis() is None


@pytest.mark.asyncio
async def test_get_redis_survives_connection_failure(monkeypatch, manager):
    monkeypatch.setattr(
        core_config,
        "settings",
        SimpleNamespace(redis_url="redis://localhost:6399/0", REDIS_URL=None),
    )

    class Boom:
        @staticmethod
        def from_url(*args, **kwargs):
            raise RuntimeError("connection refused")

    import redis.asyncio as aioredis

    monkeypatch.setattr(aioredis, "from_url", Boom.from_url)
    assert await manager._get_redis() is None
    assert manager.redis is None


# ============================================================
# broadcast_to_user(): redis publish vs local fan-out
# ============================================================


@pytest.mark.asyncio
async def test_broadcast_publishes_via_redis_when_available(manager):
    fake_redis = SimpleNamespace(publish=AsyncMock(return_value=1))
    manager._get_redis = AsyncMock(return_value=fake_redis)
    ws = FakeWebSocket()
    manager.active_connections["user-1"] = [ws]
    await manager.broadcast_to_user("user-1", "hello")
    fake_redis.publish.assert_awaited_once()
    assert ws.sent == []  # redis path never sends locally


@pytest.mark.asyncio
async def test_broadcast_falls_back_to_local_sockets(manager):
    manager._get_redis = AsyncMock(return_value=None)
    ws1, ws2 = FakeWebSocket(), FakeWebSocket()
    manager.active_connections["user-1"] = [ws1, ws2]
    await manager.broadcast_to_user("user-1", "hello")
    assert ws1.sent == ["hello"]
    assert ws2.sent == ["hello"]


@pytest.mark.asyncio
async def test_broadcast_tolerates_dead_sockets(manager):
    manager._get_redis = AsyncMock(return_value=None)
    dead, alive = FakeWebSocket(fail_sends=True), FakeWebSocket()
    manager.active_connections["user-1"] = [dead, alive]
    await manager.broadcast_to_user("user-1", "hello")
    assert alive.sent == ["hello"]


# ============================================================
# _listen_to_redis(): fan-out + error resilience
# ============================================================


@pytest.mark.asyncio
async def test_redis_listener_delivers_messages_to_connected_user(manager):
    ws = FakeWebSocket()
    delivered = asyncio.Event()

    async def on_send(text):
        delivered.set()

    ws.on_send = on_send
    manager.active_connections["user-1"] = [ws]

    payload = json.dumps({"user_id": "user-1", "content": "broadcast!"})
    messages = [{"type": "message", "data": payload}, None, None]

    class FakePubSub:
        async def get_message(self, ignore_subscribe_messages=True, timeout=1.0):
            if messages:
                return messages.pop(0)
            await asyncio.sleep(3600)

    manager.pubsub = FakePubSub()
    listener = asyncio.create_task(manager._listen_to_redis())
    try:
        await asyncio.wait_for(delivered.wait(), timeout=3)
    finally:
        listener.cancel()
        await listener  # handler swallows CancelledError and exits cleanly
    assert ws.sent == ["broadcast!"]


@pytest.mark.asyncio
async def test_redis_listener_survives_malformed_payload(manager):
    """Bad JSON must not kill the listener — it backs off and keeps looping."""
    ws = FakeWebSocket()
    manager.active_connections["user-1"] = [ws]
    messages = [{"type": "message", "data": "{not json"}, None]

    class FakePubSub:
        async def get_message(self, ignore_subscribe_messages=True, timeout=1.0):
            if messages:
                return messages.pop(0)
            await asyncio.sleep(3600)

    manager.pubsub = FakePubSub()
    listener = asyncio.create_task(manager._listen_to_redis())
    await asyncio.sleep(0.1)
    assert listener.done() is False  # still looping after the malformed payload
    # cancel lands inside the backoff sleep (except-Exception block does not
    # re-catch CancelledError) — the task exits CANCELLED, which is the
    # documented shutdown behavior of the listener.
    listener.cancel()
    with pytest.raises(asyncio.CancelledError):
        await listener
    assert ws.sent == []


# ============================================================
# stale-connection cleanup + lifecycle
# ============================================================


@pytest.mark.asyncio
async def test_start_background_tasks_is_idempotent(manager):
    await manager.start_background_tasks()
    first = manager._cleanup_task
    await manager.start_background_tasks()
    assert manager._cleanup_task is first


@pytest.mark.asyncio
async def test_cleanup_closes_stale_and_keeps_fresh(manager):
    manager.CLEANUP_INTERVAL = 0.01
    manager.STALE_CONNECTION_TIMEOUT = 10  # generous window: load-proof, fresh must survive
    stale_ws, fresh_ws = FakeWebSocket(), FakeWebSocket()
    manager.active_connections["user-1"] = [stale_ws, fresh_ws]
    import time

    manager._last_activity[id(stale_ws)] = time.time() - 9999
    manager._last_activity[id(fresh_ws)] = time.time()

    task = asyncio.create_task(manager._cleanup_stale_connections())
    await asyncio.sleep(0.08)
    task.cancel()
    await task  # handler swallows CancelledError and exits cleanly

    assert stale_ws.closed and stale_ws.closed[0][0] == 1001
    assert manager.active_connections.get("user-1") == [fresh_ws]


@pytest.mark.asyncio
async def test_shutdown_closes_sockets_and_clears_state(manager):
    ws = FakeWebSocket()
    await manager.connect(ws, "user-1")
    await manager.start_background_tasks()
    await manager.shutdown()
    assert ws.closed and ws.closed[0][0] == 1001
    assert manager.active_connections == {}
    assert manager._cleanup_task is None


@pytest.mark.asyncio
async def test_shutdown_handles_redis_resources(manager):
    closed = {"pubsub": False, "redis": False}

    class FakePubSub:
        async def unsubscribe(self, channel):
            assert channel == "ws_broadcast"

        async def close(self):
            closed["pubsub"] = True

    class FakeRedis:
        async def close(self):
            closed["redis"] = True

    manager.redis = FakeRedis()
    manager.pubsub = FakePubSub()
    await manager.shutdown()
    assert closed == {"pubsub": True, "redis": True}
    assert manager.redis is None
    assert manager.pubsub is None


def test_memory_pressure_guard(manager):
    manager.MAX_MEMORY_MB = 100000
    assert manager._is_memory_pressure() is False


# ============================================================
# preference tasks
# ============================================================


def test_track_and_cancel_pref_tasks(manager):
    class FakeTask:
        def __init__(self):
            self.cancelled = False

        def cancel(self):
            self.cancelled = True

    task = FakeTask()
    manager.track_pref_task("user-1", task)
    assert manager._pref_tasks["user-1"] == {task}
    manager.cancel_pref_tasks("user-1")
    assert task.cancelled is True
    assert "user-1" not in manager._pref_tasks


class FakeDB:
    def __init__(self, record=None):
        self.record = record or {}
        self.upserts = []

    def get_user_preferences(self, user_id):
        return self.record

    def upsert_user_preferences(self, data):
        self.upserts.append(data)
        return True


@pytest.mark.asyncio
async def test_analyze_preferences_merges_and_upserts(monkeypatch):
    db = FakeDB({"user_id": "user-1", "preferences": {"work_type": "debugging"}})
    monkeypatch.setattr(ws_agent, "SupabaseDB", lambda: db)
    monkeypatch.setattr(
        ws_agent,
        "llm_gateway",
        SimpleNamespace(
            acompletion=AsyncMock(return_value={"text": '{"preferred_stack": "Python"}'})
        ),
    )
    await analyze_and_save_preferences("user-1", 'He said "hello"')
    assert len(db.upserts) == 1
    merged = db.upserts[0]["preferences"]
    assert merged == {"work_type": "debugging", "preferred_stack": "Python"}
    assert db.upserts[0]["user_id"] == "user-1"


@pytest.mark.asyncio
async def test_analyze_preferences_strips_code_fence(monkeypatch):
    db = FakeDB()
    monkeypatch.setattr(ws_agent, "SupabaseDB", lambda: db)
    fenced = '```json\n{"answering_style": "concise"}\n```'
    monkeypatch.setattr(
        ws_agent, "llm_gateway", SimpleNamespace(acompletion=AsyncMock(return_value={"text": fenced}))
    )
    await analyze_and_save_preferences("user-1", "hi")
    assert db.upserts[0]["preferences"] == {"answering_style": "concise"}


@pytest.mark.asyncio
async def test_analyze_preferences_survives_invalid_json(monkeypatch):
    db = FakeDB()
    monkeypatch.setattr(ws_agent, "SupabaseDB", lambda: db)
    monkeypatch.setattr(
        ws_agent, "llm_gateway", SimpleNamespace(acompletion=AsyncMock(return_value={"text": "nope"}))
    )
    await analyze_and_save_preferences("user-1", "hi")  # must not raise
    assert db.upserts == []


@pytest.mark.asyncio
async def test_analyze_preferences_survives_llm_failure(monkeypatch):
    db = FakeDB()
    monkeypatch.setattr(ws_agent, "SupabaseDB", lambda: db)
    monkeypatch.setattr(
        ws_agent,
        "llm_gateway",
        SimpleNamespace(acompletion=AsyncMock(side_effect=RuntimeError("gateway down"))),
    )
    await analyze_and_save_preferences("user-1", "hi")  # must not raise
    assert db.upserts == []


@pytest.mark.asyncio
async def test_handle_analyze_preferences_skips_incomplete_payload():
    called = {"count": 0}

    async def fake_analyze(user_id, content):
        called["count"] += 1

    import api.routes.websocket_agent as mod

    original = mod.analyze_and_save_preferences
    mod.analyze_and_save_preferences = fake_analyze
    try:
        assert await handle_analyze_preferences({"payload": {"content": "hi"}}) is True
        assert await handle_analyze_preferences({"user_id": "u1"}) is True
        assert called["count"] == 0
        assert await handle_analyze_preferences({"user_id": "u1", "payload": {"content": "hi"}}) is True
        assert called["count"] == 1
    finally:
        mod.analyze_and_save_preferences = original


# ============================================================
# /ws/chat endpoint loop (direct call)
# ============================================================


def make_llm_stream(chunks):
    async def stream(*args, **kwargs):
        async def gen():
            for chunk in chunks:
                yield chunk

        return gen()

    return stream


@pytest.mark.asyncio
async def test_chat_endpoint_streams_text_and_json_payloads(monkeypatch):
    payload = {"sub": "user-1", "tenant_id": "tenant-1"}
    monkeypatch.setattr(
        ws_agent.manager, "_authenticate", AsyncMock(return_value=dict(payload))
    )
    db = FakeDB({"preferences": {"answering_style": "concise"}})
    monkeypatch.setattr(ws_agent, "SupabaseDB", lambda: db)
    monkeypatch.setattr(
        ws_agent, "llm_gateway", SimpleNamespace(acompletion=make_llm_stream(["hello", " world"]))
    )
    enqueue = AsyncMock(return_value=True)
    monkeypatch.setattr(ws_agent.task_queue, "enqueue", enqueue, raising=False)

    ws = FakeWebSocket(
        incoming=[
            "plain hello",
            json.dumps({"text": "json hi", "image_base64": "QUJD"}),
            WebSocketDisconnect(code=1000),
        ]
    )
    await ws_agent.websocket_chat_endpoint(ws, make_request("198.51.100.7"))

    # two complete streams + [DONE] sentinels, in order
    assert ws.sent == ["hello", " world", "[DONE]", "hello", " world", "[DONE]"]
    # preference analysis enqueued once per exchange
    assert enqueue.await_count == 2
    assert enqueue.call_args_list[0].kwargs["user_id"] == "user-1"
    # disconnected socket removed from the manager
    assert "user-1" not in ws_agent.manager.active_connections


@pytest.mark.asyncio
async def test_chat_endpoint_sends_error_frame_on_llm_failure(monkeypatch):
    monkeypatch.setattr(
        ws_agent.manager,
        "_authenticate",
        AsyncMock(return_value={"sub": "user-2", "tenant_id": "tenant-1"}),
    )
    monkeypatch.setattr(ws_agent, "SupabaseDB", lambda: FakeDB())
    monkeypatch.setattr(ws_agent, "llm_gateway", SimpleNamespace(acompletion=AsyncMock(side_effect=RuntimeError("llm down"))))
    monkeypatch.setattr(ws_agent.task_queue, "enqueue", AsyncMock(return_value=True), raising=False)

    ws = FakeWebSocket(incoming=["hi", WebSocketDisconnect(code=1000)])
    await ws_agent.websocket_chat_endpoint(ws, make_request())
    assert ws.sent == ["\n[Error: RuntimeError]\n[DONE]"]
    assert "user-2" not in ws_agent.manager.active_connections


@pytest.mark.asyncio
async def test_chat_endpoint_requires_tenant_context(monkeypatch):
    monkeypatch.setattr(
        ws_agent.manager,
        "_authenticate",
        AsyncMock(return_value={"sub": "user-3"}),
    )
    ws = FakeWebSocket()
    await ws_agent.websocket_chat_endpoint(ws, make_request())
    assert ws.closed == [(1008, "Tenant context required")]
    assert ws.accepted is False


@pytest.mark.asyncio
async def test_chat_endpoint_no_auth_returns_silently(monkeypatch):
    monkeypatch.setattr(ws_agent.manager, "_authenticate", AsyncMock(return_value=None))
    ws = FakeWebSocket()
    await ws_agent.websocket_chat_endpoint(ws, make_request())
    assert ws.accepted is False
    assert ws.sent == []
    assert ws.closed == []
