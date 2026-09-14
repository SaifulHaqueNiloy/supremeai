# Operational Contracts — Single Source of Truth

> Task: production contract closure (`final-test/production-contract-closure`), 2026-09-14.
> This file is the **single source of truth** for the runtime/deployment contracts fixed
> in this branch. If code and this doc disagree, fix the code or update this doc in the
> same PR — never let them drift silently.
>
> Related: `docs/deployment/PRODUCTION_ENV_EVIDENCE.md` (live env verification),
> `docs/operations/SLO_AND_ALERTS.md` (targets), `docs/operations/BACKUP_RESTORE_AND_ROLLBACK.md` (recovery).

---

## 1. Canonical Health Contract

**Rule.** The canonical health surface is:

| Endpoint | Meaning | Response |
|---|---|---|
| `GET /health` | Full health — runs **all** registered checks, per-check latency/errors | `200` healthy / `503` degraded or unhealthy |
| `GET /health/live` | Liveness — is the process alive? (k8s restarts on failure) | `200` alive / `503` dead |
| `GET /health/ready` | Readiness — all **critical** checks pass; safe to receive traffic | `200` ready / `503` not_ready |

`/api/v1/health/*` remains mounted **only as a legacy alias** for older monitors.
All operational configuration (Docker HEALTHCHECK, k8s probes, keepalive workflow,
CI smoke, frontend probes) must point at `/health/*`. New tooling must never use
`/api/v1/health/*`.

**Where enforced.**

| Consumer | Path used | Location |
|---|---|---|
| Router mounting (canonical + legacy alias) | — | `backend/core/app_builder.py` (CANONICAL HEALTH CONTRACT block) |
| Probe implementations | — | `backend/core/health_routes.py` |
| Docker HEALTHCHECK | `/health/live` | `backend/Dockerfile` |
| k8s liveness / readiness / startup probes | `/health/live`, `/health/ready` | `infrastructure/kubernetes/namespace.yaml` |
| Keep-alive pinger | `/health/live` | `.github/workflows/keepalive.yml` |
| Frontend service-health probes | `/health/*` | `frontend/src/utils/api.ts`, `frontend/src/components/auth/ServiceHealthBar.tsx` |

**Env vars.** None (contract is path-level). `PORT` selects the listen port (default 8080).

**How to verify.**

```bash
curl -s -o /dev/null -w "%{http_code}\n" https://<backend>/health          # 200 or 503 (full)
curl -s -o /dev/null -w "%{http_code}\n" https://<backend>/health/live     # 200
curl -s -o /dev/null -w "%{http_code}\n" https://<backend>/health/ready    # 200
```

A `404` on any of the three means the deployment is running a stale image — redeploy.

---

## 2. API Docs Exposure Policy (P0)

**Rule.** `/docs`, `/redoc` and the OpenAPI schema are **DISABLED by default in
staging/production**. They are:

- enabled by default in local dev only;
- opt-in outside local via `SUPREMEAI_DOCS_ENABLED=true` (or legacy `DOCS_ENABLED`);
- when enabled in a non-local env, **always** protected by HTTP Basic auth
  (`SUPREMEAI_DOCS_USERNAME` / `SUPREMEAI_DOCS_PASSWORD`);
- password must be **≥ 12 characters**; the old public default `dev_password_only`
  (also `admin`, `password`) is **hard-rejected and boot fails** in staging/production;
- if docs are enabled without a password in staging/prod, boot **fails fast** (no
  silent auto-generation for explicit opt-ins; auto-generated only when docs were
  never explicitly enabled).

**Where enforced.**

- `backend/core/config_fields.py` — real `docs_enabled` / `docs_auth_enabled` /
  `docs_username` / `docs_password` fields (previously `docs_enabled` did not exist,
  so `getattr(…, True)` silently exposed docs everywhere).
- `backend/core/config_validation.py` — `validate_docs_password` (forbidden defaults)
  and `validate_all` (disable-by-default outside local, fail-fast on weak/missing password).
- `backend/core/middleware/docs_auth.py` — `DocsAuthMiddleware` issues the Basic-auth
  challenge (401 + `WWW-Authenticate`) for `/docs`, `/redoc`, `/openapi.json`
  (incl. the `/api/v1/openapi.json` mount).
- `backend/core/app_builder.py` — mounts docs only when the policy allows; registers
  the middleware after `AuthMiddleware` so it runs outermost.

**Env vars.**

| Variable | Effect |
|---|---|
| `SUPREMEAI_DOCS_ENABLED` | `true` re-enables docs outside local (still Basic-auth gated) |
| `SUPREMEAI_DOCS_AUTH_ENABLED` | default `true`; docs auth cannot be safely turned off outside local |
| `SUPREMEAI_DOCS_USERNAME` | Basic-auth user (default `admin`) |
| `SUPREMEAI_DOCS_PASSWORD` | ≥ 12 chars in staging/prod; `dev_password_only` refused (boot failure) |

**How to verify.**

```bash
# Docs disabled (default in prod): expect 404
curl -s -o /dev/null -w "%{http_code}\n" https://<backend>/docs
curl -s -o /dev/null -w "%{http_code}\n" https://<backend>/api/v1/openapi.json

# Docs explicitly enabled: expect 401 without credentials, 200 with
curl -s -o /dev/null -w "%{http_code}\n" https://<backend>/docs
curl -s -o /dev/null -w "%{http_code}\n" -u "$SUPREMEAI_DOCS_USERNAME:$SUPREMEAI_DOCS_PASSWORD" https://<backend>/docs
```

CI/pytest contexts are exempt from the middleware (keeps test suites deterministic).

---

## 3. Admin Secret Contract (`/internal/*`)

**Rule.** Automation calling `/internal/*` endpoints (e.g. `POST /internal/run-daily-evolution`)
must authenticate with the **dedicated** `SUPREMEAI_ADMIN_SECRET` via the `X-Admin-Secret`
header. The old `docs_password` fallback is **removed** — the publicly-known
`dev_password_only` default can no longer act as an admin key.

Behavior:

- `SUPREMEAI_ADMIN_SECRET` unset on server → `500` ("internal automation endpoints are locked");
- wrong secret → `403 Forbidden`;
- comparison is constant-time (`secrets.compare_digest`).

**Where enforced.**

- `backend/api/routes/internal.py` — `_require_admin()` (fallback removed, FINAL-TEST P0).
- `backend/core/config_fields.py` — `supremeai_admin_secret` field (empty default).
- `backend/core/config_validation.py` — logs a critical warning at boot in
  staging/production when the secret is missing, so the gap is visible before automation breaks.

**Env vars.** `SUPREMEAI_ADMIN_SECRET` (long random string; store in Infisical + Render).

**How to verify.**

```bash
# Expect 403 (or 500 if unset server-side — also actionable):
curl -s -o /dev/null -w "%{http_code}\n" -X POST https://<backend>/internal/run-daily-evolution \
  -H "X-Admin-Secret: wrong-value" -H "Content-Type: application/json" -d '{}'
# Expect 200:
curl -s -X POST https://<backend>/internal/run-daily-evolution \
  -H "X-Admin-Secret: $SUPREMEAI_ADMIN_SECRET" -H "Content-Type: application/json" -d '{}'
```

---

## 4. DB Degradation Policy (P1)

**Rule.** Database failure policy is **role-based**:

| Service role (`SUPREMEAI_SERVICE_ROLE`) | DB failure ⇒ readiness |
|---|---|
| `core` / `monolith` / `user` | **NOT READY — always.** `SUPABASE_ALLOW_DB_DEGRADATION=true` is *ignored* and a warning is logged. |
| `worker` / `scraper` / `mcp` | May be ready without DB; `SUPABASE_ALLOW_DB_DEGRADATION=true` is honored (DB check registered non-critical). |

The core API must never serve traffic without its database. The escape hatch exists
only for roles whose function is not DB-backed.

**Where enforced.**

- `backend/core/app_builder.py` — `_check_database()` DB DEGRADATION POLICY block:
  degradation honored **only** for `worker|scraper|mcp`; core roles always return fail.
- `backend/core/app_builder.py` — `register_check("database", _check_database, critical=not is_standalone_microservice)`.
- `backend/database/session.py` + `backend/core/degraded_mode.py` — engine-level
  degradation and SQLite-fallback gates (`sqlite_fallback_allowed()` is fail-closed in
  production; per-feature CRITICAL warning fires once).

**Env vars.**

| Variable | Effect |
|---|---|
| `SUPREMEAI_SERVICE_ROLE` | `core` (default `monolith`), or `worker` / `scraper` / `mcp` |
| `SUPABASE_ALLOW_DB_DEGRADATION` | `true` accepts persistence-less operation — **worker/scraper/mcp only** |

**How to verify.**

```bash
# On the core node, stop/block the DB (or point DATABASE_URL at a dead host) and redeploy:
curl -s https://<backend>/health/ready     # expect 503 NOT_READY, never 200
curl -s https://<backend>/health           # expect "database" check unhealthy, critical=true
```

Regression tests: `backend/tests/database/test_session_degradation_regression.py`,
`backend/tests/security/test_database_readiness_regression.py`,
`backend/tests/security/test_p0_safety_regression.py`.

---

## 5. Rate Limit Authority (P1)

**Rule.** The **Redis-backed** `RateLimiter` (`backend/core/rate_limit.py`) is the
authoritative multi-instance rate limiter (tiered sliding window: anonymous 10/min,
authenticated 60/min, premium 300/min, admin 1000/min + endpoint overrides).

The in-memory `RequestValidationMiddleware` request log is a **per-process emergency
fallback only** — with 2+ instances the aggregate limit is per-instance and must not be
relied upon for cross-instance correctness. Its limits are env-driven (zero hardcode):

| Env var | Default | Governs |
|---|---|---|
| `SECURITY_MAX_BODY_BYTES` | `10485760` (10 MB) | max request body (`413` above) |
| `SECURITY_MAX_QUERY_LENGTH` | `2048` | max query-string length (`414` above) |
| `SECURITY_MAX_HEADER_SIZE` | `8192` | max header size |
| `SECURITY_FALLBACK_RATE_LIMIT` | `100` | fallback requests per window per client |
| `SECURITY_FALLBACK_RATE_WINDOW` | `60` | fallback window (seconds) |
| `RATE_LIMIT_ENABLED` | `true` | `false` disables the in-memory fallback entirely |

Auth-tier classification and both limiters skip health paths, metrics, and test contexts.

**Where enforced.**

- `backend/core/rate_limit.py` — `RateLimiter` (Redis sliding window, two-phase
  check-then-add so rejected requests never refill the window; bounded in-memory fallback).
- `backend/core/middleware/security.py` — `RequestValidationMiddleware` (env-driven
  limits; class-level constants kept only for test back-compat).
- `backend/core/config_fields.py` — `security_*` fields with the aliases above.

**How to verify.**

```bash
# Fallback limits are visible at boot: unset → logged defaults.
# Functional check (Redis down simulation): hammer one endpoint past the limit:
for i in $(seq 1 120); do curl -s -o /dev/null -w "%{http_code} " https://<backend>/api/v1/<endpoint>; done
# Expect 429s once the applicable limit is crossed; X-RateLimit-* headers present.
```

Multi-instance proof: with 2 replicas behind one LB, the Redis limiter's
`X-RateLimit-Limit`/`Remaining` must be consistent across instances (fallback would show
per-instance counters).

---

## 6. Frontend Build Contract (P0)

**Rule.** A production frontend build **must not** ship without real backend URLs.
Vite inlines `VITE_*` at build time; a bundle built with a missing/localhost backend URL
silently ships in "degraded viewer mode".

- `frontend/scripts/validate-build-env.mjs` **hard-fails** the production build
  (`NODE_ENV=production` or `VITE_FORCE_CONTRACT_CHECK=true`) when:
  1. no user-backend variable is set (`VITE_USER_BACKEND` → `VITE_API_BASE` →
     `VITE_API_URL` → `VITE_BACKEND_URL`) **and** `VITE_USE_RELATIVE_PATH` ≠ `true`
     **and** `VITE_ALLOW_LOCAL_BACKEND` ≠ `true`;
  2. any resolved backend URL points at a loopback host (`localhost`, `127.0.0.1`,
     `0.0.0.0`, `[::1]`) unless `VITE_ALLOW_LOCAL_BACKEND=true`.
- `frontend/Dockerfile` no longer defaults `VITE_API_URL` to `http://localhost:8080`
  (ARG is empty; the guard runs before `pnpm run build`).
- Escape hatches:
  - `VITE_USE_RELATIVE_PATH=true` — same-host deployment (nginx/edge proxy serves `/api`);
  - `VITE_ALLOW_LOCAL_BACKEND=true` — **local Docker testing only**, never production.

Admin backend falls back to the user backend when `VITE_ADMIN_BACKEND` is unset.

**Where enforced.**

- `frontend/scripts/validate-build-env.mjs` (guard; exit code 1 blocks build/CI).
- `frontend/Dockerfile` (build args; runs the guard in the builder stage).
- `frontend/package.json` — build script wires the guard.
- `.github/workflows/ci.yml` — frontend build job passes `VITE_API_URL` /
  `VITE_BACKEND_URL` / `VITE_USER_BACKEND` / `VITE_ADMIN_BACKEND` from
  repo variables/secrets (chain ends at the known Render backend, never localhost).
- Runtime mirror of the URL resolution: `frontend/src/utils/api.ts`.

**Env vars (build-time).** `VITE_USER_BACKEND`, `VITE_ADMIN_BACKEND`, `VITE_API_URL`,
`VITE_BACKEND_URL`, `VITE_USE_RELATIVE_PATH`, `VITE_ALLOW_LOCAL_BACKEND`,
`VITE_FORCE_CONTRACT_CHECK` (force the guard in non-prod builds).

**How to verify.**

```bash
cd frontend
NODE_ENV=production node scripts/validate-build-env.mjs                                   # expect exit 1 (no URLs)
VITE_API_URL=https://supremeai-backend.onrender.com NODE_ENV=production \
  node scripts/validate-build-env.mjs                                                     # expect exit 0
docker build -f frontend/Dockerfile .   # without build-args → build FAILS (contract holds)
```

---

## 7. Related session contracts (pointers)

- **Coverage gates** (FINAL-TEST P1, staged baseline 2026-09-14): the backend
  gate lives in `scripts/ci/coverage_policy.yaml` (`overall.pr` **25 → 30**,
  enforced by `scripts/ci/coverage_quality_gate.py`) and is now ALSO wired to
  the declared `MIN_BACKEND_COVERAGE` (30) in `.github/workflows/ci.yml` —
  previously that env var was dead config. Frontend gate raised **16 → 20%**
  via the vitest CLI thresholds. Ladder: 30 → 40 → 50 → 60 (backend),
  20 → 25 → 30 (frontend). Raise one step only after CI stays green for a week.
- **Production smoke test**: `scripts/ci/production_smoke_test.py` —
  health → login → `/auth/me` → chat → logout. Env vars: `SMOKE_BASE_URL`,
  `SMOKE_EMAIL`, `SMOKE_PASSWORD`, `SMOKE_SKIP_AUTH`.
- Live-env verification: `docs/deployment/PRODUCTION_ENV_EVIDENCE.md` (update after
  each deployment change; CI does not enforce it yet).
