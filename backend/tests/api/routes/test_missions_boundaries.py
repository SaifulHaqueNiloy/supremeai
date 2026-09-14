"""Mission Orchestration API — error-path & boundary contracts.

Complement to tests/missions/test_mission_orchestration.py (which covers the
happy-path lifecycle over HTTP). This suite pins the routes' FAILURE contracts
against the real app (same ASGITransport + dependency-override pattern):

- principal hardening: an authenticated token WITHOUT any subject claim is a
  403 (identity is ALWAYS derived from the principal, never the body)
- malformed mission ids are 404 — never 500 from uuid parsing
- cross-user access is 404 (existence not leaked) on EVERY endpoint family,
  while admins may operate cross-owner
- the illegal-transition 409 mapping for every transition endpoint
- the fail endpoint's reason contract (body reason vs 'unspecified failure')
- cancel legality from PLANNED and illegality from SUCCEEDED
- repair exhaustion surfaces as 409 over HTTP once strategy options are gone
- the trace endpoint's shape (mission_id echo, sorted seqs)
- the SSE stream's auth/ownership gate BEFORE streaming + event framing
- pagination validation bounds (ge/le on skip/limit)

Fixtures mirror the sibling suite: conftest ``client`` (real app) + the two
missions tables created once on the app engine + a per-test principal factory
via dependency override (AuthMiddleware's test bypass short-circuits before
JWT decode, so the override is the only multi-principal mechanism).
"""

from __future__ import annotations

import uuid

import pytest
import pytest_asyncio

_api_tables_ready = False


@pytest_asyncio.fixture
async def missions_tables(client):
    """Create the missions tables on the app engine (once per process).

    Engine-agnostic by design: locally the conftest app fixture points at a
    sqlite test.db, while the CI api/security matrix jobs point at the real
    postgres test service — the missions tables compile on BOTH (JSON columns
    use JSON().with_variant(JSONB, "postgresql"), mirroring missions/models.py).
    """
    global _api_tables_ready
    if not _api_tables_ready:
        import database.session as dbs
        from missions.models import Mission, MissionTraceEvent
        from models.base import Base

        dbs.init_engine()
        async with dbs.engine.begin() as conn:
            await conn.run_sync(
                lambda sync_conn: Base.metadata.create_all(
                    sync_conn,
                    tables=[Mission.__table__, MissionTraceEvent.__table__],
                )
            )
        _api_tables_ready = True
    yield


@pytest_asyncio.fixture
async def principal(client):
    """Per-test principal factory (same mechanism as the sibling suite)."""
    from api.dependencies import get_current_user_token
    from core.app import app as application

    def install(sub: str, role: str = "user") -> str:
        application.dependency_overrides[get_current_user_token] = lambda: {
            "sub": sub,
            "role": role,
            "tenant_id": "test-tenant",
        }
        return sub

    yield install
    application.dependency_overrides.pop(get_current_user_token, None)


async def _create(client, principal, *, sub: str | None = None, **overrides) -> str:
    """Create a mission over HTTP; returns its id."""
    sub = sub or f"user-{uuid.uuid4().hex[:10]}"
    principal(sub)
    payload = {
        "title": "Boundary mission",
        "goal_text": "Probe the contract",
        "strategy_options": ["plan-a", "plan-b"],
        "phases": [{"name": "phase-1"}, {"name": "phase-2"}],
    }
    payload.update(overrides)
    resp = await client.post("/api/v1/missions", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


# ------------------------------------------------------------- identity ------


@pytest.mark.asyncio
async def test_missing_principal_claims_403(client, missions_tables, principal):
    """A token payload with no sub/user_id/email cannot create missions —
    ownership MUST be derivable (403, not an anonymous-owned row)."""
    from api.dependencies import get_current_user_token
    from core.app import app as application

    application.dependency_overrides[get_current_user_token] = lambda: {"role": "user"}
    try:
        resp = await client.post(
            "/api/v1/missions",
            json={"title": "t", "goal_text": "g"},
        )
        assert resp.status_code == 403, resp.text
        assert "Authenticated principal required" in resp.json()["detail"]
    finally:
        application.dependency_overrides.pop(get_current_user_token, None)


@pytest.mark.asyncio
async def test_bad_uuid_is_404_not_500(client, missions_tables, principal):
    """Malformed mission ids parse-fail into 404 across endpoint families."""
    principal("user-baduuid")
    for method, path in (
        ("GET", "/api/v1/missions/not-a-uuid"),
        ("POST", "/api/v1/missions/not-a-uuid/approve"),
        ("GET", "/api/v1/missions/not-a-uuid/trace"),
        ("GET", "/api/v1/missions/not-a-uuid/trace/stream"),
    ):
        resp = await client.request(method, path)
        assert resp.status_code == 404, f"{method} {path} -> {resp.status_code}"
        assert resp.json()["detail"] == "Mission not found"


# --------------------------------------------------------- cross-user 404 ----


@pytest.mark.asyncio
async def test_foreign_mission_404_on_approve_and_trace(client, missions_tables, principal):
    """Ownership gate covers every route family — operations and audit reads
    must not be usable against a foreign mission either."""
    owner_sub = f"owner-{uuid.uuid4().hex[:8]}"
    mid = await _create(client, principal, sub=owner_sub)

    stranger = f"stranger-{uuid.uuid4().hex[:8]}"
    principal(stranger)
    for method, path in (
        ("GET", f"/api/v1/missions/{mid}"),
        ("POST", f"/api/v1/missions/{mid}/approve"),
        ("GET", f"/api/v1/missions/{mid}/trace"),
        ("GET", f"/api/v1/missions/{mid}/trace/stream"),
    ):
        resp = await client.request(method, path)
        assert resp.status_code == 404, f"{method} {path} -> {resp.status_code}: {resp.text}"


@pytest.mark.asyncio
async def test_admin_reads_and_operates_cross_owner(client, missions_tables, principal):
    """Admins are the ONLY cross-owner principals: read + transition must work
    against a user-owned mission (404 for users, 200 for admin)."""
    owner_sub = f"owner-{uuid.uuid4().hex[:8]}"
    mid = await _create(client, principal, sub=owner_sub)

    principal("the-admin", role="admin")
    got = await client.get(f"/api/v1/missions/{mid}")
    assert got.status_code == 200, got.text
    assert got.json()["owner_id"] == owner_sub

    approved = await client.post(f"/api/v1/missions/{mid}/approve")
    assert approved.status_code == 200, approved.text
    assert approved.json()["state"] == "assigned"


# ------------------------------------------------- transition error maps -----


@pytest.mark.asyncio
async def test_illegal_transitions_map_to_409(client, missions_tables, principal):
    """Every transition endpoint funnels IllegalTransition -> 409."""
    mid = await _create(client, principal)  # planned
    cases = (
        ("POST", f"/api/v1/missions/{mid}/start"),  # planned -> start illegal
        ("POST", f"/api/v1/missions/{mid}/advance"),  # planned -> advance illegal
        ("POST", f"/api/v1/missions/{mid}/repair"),  # planned -> repair illegal
    )
    for method, path in cases:
        resp = await client.request(method, path)
        assert resp.status_code == 409, f"{method} {path} -> {resp.status_code}: {resp.text}"

    # approve on RUNNING (approve again after the first approve -> assigned;
    # approve from assigned is illegal too).
    await client.post(f"/api/v1/missions/{mid}/approve")
    again = await client.post(f"/api/v1/missions/{mid}/approve")
    assert again.status_code == 409, again.text


@pytest.mark.asyncio
async def test_cancel_from_planned_ok_but_from_succeeded_409(client, missions_tables, principal):
    """cancel is legal from planned/approved/assigned/running and terminal
    states reject it."""
    mid1 = await _create(client, principal)
    cancelled = await client.post(
        f"/api/v1/missions/{mid1}/cancel", json={"reason": "changed mind"}
    )
    assert cancelled.status_code == 200, cancelled.text
    assert cancelled.json()["state"] == "cancelled"

    # Drive one to SUCCEEDED then try to cancel it.
    mid2 = await _create(client, principal, phases=[{"name": "only"}])
    await client.post(f"/api/v1/missions/{mid2}/approve")
    await client.post(f"/api/v1/missions/{mid2}/start")
    await client.post(f"/api/v1/missions/{mid2}/advance")  # last phase -> succeeded
    late = await client.post(f"/api/v1/missions/{mid2}/cancel")
    assert late.status_code == 409, late.text


@pytest.mark.asyncio
async def test_fail_reason_from_body_and_default(client, missions_tables, principal):
    """fail stamps the body's reason; with NO body it stamps the documented
    'unspecified failure' default."""
    mid1 = await _create(client, principal)
    await client.post(f"/api/v1/missions/{mid1}/approve")
    await client.post(f"/api/v1/missions/{mid1}/start")
    failed = await client.post(f"/api/v1/missions/{mid1}/fail", json={"reason": "sandbox exploded"})
    assert failed.status_code == 200, failed.text
    body = failed.json()
    assert body["state"] == "failed"
    assert body["failure_reason"] == "sandbox exploded"

    mid2 = await _create(client, principal)
    await client.post(f"/api/v1/missions/{mid2}/approve")
    await client.post(f"/api/v1/missions/{mid2}/start")
    failed2 = await client.post(f"/api/v1/missions/{mid2}/fail")
    assert failed2.status_code == 200, failed2.text
    assert failed2.json()["failure_reason"] == "unspecified failure"


@pytest.mark.asyncio
async def test_repair_exhaustion_409_over_http(client, missions_tables, principal):
    """After MAX_REPAIRS rotations the next repair request is a 409 — the
    mission is terminally failed."""
    from missions.state_machine import MAX_REPAIRS

    mid = await _create(client, principal, options=("a", "b"))
    await client.post(f"/api/v1/missions/{mid}/approve")
    await client.post(f"/api/v1/missions/{mid}/start")
    for _ in range(MAX_REPAIRS):
        await client.post(f"/api/v1/missions/{mid}/fail", json={"reason": "again"})
        repaired = await client.post(f"/api/v1/missions/{mid}/repair")
        assert repaired.status_code == 200, repaired.text
        assert repaired.json()["state"] == "running"

    await client.post(f"/api/v1/missions/{mid}/fail", json={"reason": "final"})
    exhausted = await client.post(f"/api/v1/missions/{mid}/repair")
    assert exhausted.status_code == 409, exhausted.text
    assert "repair" in exhausted.json()["detail"].lower()


# ----------------------------------------------------------------- trace -----


@pytest.mark.asyncio
async def test_trace_shape_and_mission_id_echo(client, missions_tables, principal):
    mid = await _create(client, principal)
    await client.post(f"/api/v1/missions/{mid}/approve")

    trace = await client.get(f"/api/v1/missions/{mid}/trace")
    assert trace.status_code == 200, trace.text
    body = trace.json()
    assert body["mission_id"] == mid
    assert body["count"] >= 2  # created + approved
    seqs = [e["seq"] for e in body["items"]]
    assert seqs == sorted(seqs) and seqs[0] == 1
    assert all(e["mission_id"] == mid for e in body["items"])


# ------------------------------------------------------------------- SSE -----


@pytest.mark.asyncio
async def test_sse_stream_frames_events(client, missions_tables, principal):
    """The stream emits 'event: mission_trace' SSE frames for existing events;
    the client disconnect close is a normal exit (CancelledError re-raised
    inside the generator)."""
    mid = await _create(client, principal)
    await client.post(f"/api/v1/missions/{mid}/approve")

    async with client.stream("GET", f"/api/v1/missions/{mid}/trace/stream") as resp:
        assert resp.status_code == 200, await resp.aread()
        assert resp.headers["content-type"].startswith("text/event-stream")
        assert resp.headers["cache-control"] == "no-cache"
        frames = []
        async for line in resp.aiter_lines():
            frames.append(line)
            if len([f for f in frames if f.startswith("event: mission_trace")]) >= 2:
                break  # got the existing events; close early (bounded loop)
    data_lines = [f for f in frames if f.startswith("data: ")]
    assert data_lines, "SSE frames must carry data payloads"


@pytest.mark.asyncio
async def test_sse_stream_gated_before_streaming(client, missions_tables, principal):
    """Authz happens BEFORE the stream opens: bad id and foreign mission both
    get a plain 404 response, not a half-open event stream."""
    owner_sub = f"owner-{uuid.uuid4().hex[:8]}"
    mid = await _create(client, principal, sub=owner_sub)

    principal(f"other-{uuid.uuid4().hex[:8]}")
    foreign = await client.get(f"/api/v1/missions/{mid}/trace/stream")
    assert foreign.status_code == 404, foreign.text


# ------------------------------------------------------------ list bounds ----


@pytest.mark.asyncio
async def test_list_pagination_bounds_422(client, missions_tables, principal):
    principal(f"user-{uuid.uuid4().hex[:8]}")
    for query in ("limit=0", "limit=101", "skip=-1"):
        resp = await client.get(f"/api/v1/missions?{query}")
        assert resp.status_code == 422, f"{query} -> {resp.status_code}"


@pytest.mark.asyncio
async def test_list_limit_caps_at_100(client, missions_tables, principal):
    sub = f"user-{uuid.uuid4().hex[:8]}"
    principal(sub)
    listed = await client.get("/api/v1/missions?limit=100&skip=0")
    assert listed.status_code == 200, listed.text
    body = listed.json()
    assert body["limit"] == 100 and body["skip"] == 0
    assert set(body.keys()) == {"items", "count", "skip", "limit"}
