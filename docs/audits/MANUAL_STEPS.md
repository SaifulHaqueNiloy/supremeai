# MANUAL_STEPS — Actions Requiring Human / Infrastructure Access

> Living document — every item here is an action that CANNOT be performed from
> the code sandbox (needs a vendor dashboard, production traffic, or secrets
> the operator must rotate). Keep it in sync with the round notes in
> `apps/mission-control` and the drift-guard test below.
>
> Canonical evidence matrix: `docs/deployment/ENV_EVIDENCE_MATRIX.md`
> (registry-drift-guarded by `backend/tests/test_env_evidence_matrix.py`).

## Current manual tasks (2026-09, mission-control rounds)

| # | Task | Where | Why it needs a human |
|---|------|-------|----------------------|
| 1 | ~~Set `TELEGRAM_CHAT_ID` (optional `DISCORD_WEBHOOK_URL`)~~ **✅ RESOLVED (2026-09-19)** | Render → mcp-tower service → Environment | Synchronized `TELEGRAM_CHAT_ID` and `ADMIN_TELEGRAM_CHAT_ID` (`7804133572`) into Infisical prod vault + .env; verified live with Telegram alert message delivery (200 OK). |
| 2 | ~~Rotate `GH_TOKEN` / `GITHUB_TOKEN` on the tower~~ **✅ RESOLVED (2026-09-19)** | Render → mcp-tower → Environment | Provisioned active GitHub PAT (SaifulHaqueNiloy, admin/maintain & actions run read verified with 200 OK); synced into Infisical prod vault + .env. |
| 3 | ~~Set `CLOUDFLARE_API_TOKEN`~~ **✅ RESOLVED (2026-09-19)** | Render → mcp-tower → Environment | Provisioned active Cloudflare API Token (Workers AI 65 models + `@cf/baai/bge-small-en-v1.5` 384-dim semantic embeddings verified live with 200 OK); synced into Infisical prod vault + .env. |
| 4 | ~~Memory-engine runtime~~ **✅ RESOLVED (2026-09-19)** | Tower host / Render / Docker | Added Python 3 + `uv` to `infrastructure/mcp-control-plane/render.yaml` buildCommand (`pip install uv && npm install && npm run build`) and Dockerfile runtime stage; configured `SUPREMEAI_BACKEND_DIR` in render.yaml and docker-compose.yml. Resolves ENOENT on `memory_*` tools. |
| 5 | ~~Backend tenant-admin isolation test deep-dive~~ **✅ RESOLVED (2026-09-19)** | Backend route tests | Fixed `_IncludedRouter` sentinel handling in `test_tenant_admin_isolation.py` (`test_tenants_router_nested_into_primary`, `test_reset_dual_primary_route_registration`, `test_tenants_router_nesting_produces_doubled_prefix_flagged` via openapi paths). All 63/63 tests pass. |
| 6 | ~~Reset or Upgrade Upstash Redis Quota (Issue #437)~~ **✅ RESOLVED (2026-09-19)** | Upstash Dashboard → Database Console | Provisioned 5-Node Distributed Upstash Federation Pool (2.5M ops/mo across 5 isolated accounts with eviction enabled in ap-southeast-1). All credentials verified live & synced into Infisical prod vault + .env. Tracked in Issue #460. |
| 7 | ~~Rotate `OPENROUTER_API_KEY` (Issue #438)~~ **✅ RESOLVED (2026-09-19)** | Infisical Vault / Render Environment Dashboard | Provisioned 9-Node OpenRouter Federation Pool (9 permanent accounts verified live with 200 OK across auth & live chat completions; 450 free reqs/day pool @ $0); synced into .env. Resolves Issue #438. |
| 8 | ~~Provision Cloud Sandbox Provider Key (`E2B_API_KEY` / `RUNPOD_API_KEY`) (Issue #448)~~ **✅ RESOLVED (2026-09-19)** | Infisical Vault / Render Environment Dashboard | Provisioned Dual-Node E2B Cloud Sandbox Federation (Primary & Secondary keys verified live with 200 OK on sandboxes endpoint); synced into .env. Resolves Issue #448. |

## Historical audit remediation steps (2026-08-30, patch v4 era)

> dashboards, production traffic, or a maintainer decision.

## 1. Clean production Docker build (Phase 0.5) — requires Docker

```bash
cd backend
docker build -t supremeai-core:audit-check .
docker image ls supremeai-core:audit-check   # record size → checklist item 0.9
docker run --rm -e ENV=production -e PORT=8080 -e JWT_SECRET=<dev-only-32+chars> \
  -e DATABASE_URL=<test-db> -p 8080:8080 supremeai-core:audit-check
curl -s http://localhost:8080/api/v1/health/live   # expect 200
```

Also validates: poetry 2.4.1 pin + regenerated `poetry.lock` (AUD-7.4) build cleanly.

## 2. Deployed-environment health probe (Phase 0.7)

**Partially executed (2026-08-30, patch v3 session):** live probe on the CURRENT deployed image returned
`/api/v1/health/live` = **200** (alias `/health/live` = 200) but `/api/v1/health/ready` = **503** —
root-caused to code defects fixed in patch v3 (AUD-1.7), not to the database itself. Also note: the
currently deployed image predates patch v2.

After the next Render deploy of `main` + patch v3 + patch v4:

```bash
curl -s -o /dev/null -w "%{http_code}\n" https://supremeai-backend-v2.onrender.com/api/v1/health/live
curl -s -o /dev/null -w "%{http_code}\n" https://supremeai-backend-v2.onrender.com/api/v1/health/ready
```

Record both 200s in the checklist (0.7 → `[x]`). If ready remains 503 after deploy, check
`SUPABASE_DATABASE_URL_POOLER` / `DATABASE_URL` env in the Render dashboard (the fixed check now
logs the concrete failure server-side).

## 3. CI green run + coverage baseline (Phase 0.8, COV-1..7)

- Push the patch branch → verify the **AUD-1.1 "Verify Canonical Startup Command"** step
  goes green (it now probes `/api/v1/health/live`, so a wrong boot fails CI).
- Confirm the coverage gate (≥80%) passes with real Postgres; then mark
  COV-1/2 and the >=90% module gates from the CI coverage artifact.
- PATCH v4: 14 new tests in `tests/security/test_patch_v4_render_log_fixes.py` must pass.

## 4. Image signing + SBOM (AUD-6.5, AUD-7.5 deep)

1. Install/verify `cosign` in the deploy job; sign the GHCR image after
   `deploy-backend-ghcr`, e.g. `cosign sign ghcr.io/saifulhaqueniloy/supremeai/supremeai-core:<tag>`.
2. Enable Syft (or Trivy SBOM mode) in CI and attach the SBOM to the GitHub Release.

## 5. Runtime capacity baseline (Phase 0.9)

From the Render dashboard, record for the current deployment:
image size, install/boot time, memory peak. Note: the 512 MiB / ~92.8% peak
capacity warning stands — see `docs/devops/WORKER_POLICY_AND_CAPACITY_PLAN.md`.

**PATCH v4 update:** The eager-singleton-to-lazy conversion in `core/services.py` should
drop boot-time RSS from ~460 MB (90.78%) to ~340-380 MB (66-74%). Re-check this on the next
deploy. If memory is still >85%, profile via `py-spy record --pid <uvicorn-pid>` and look for
other module-level `X = SomeClass()` patterns in `brain/`, `services/`, `tools/`.

## 6. Backup restore drill (AUD-5.7)

Execute §5 of `docs/operations/BACKUP_RESTORE_POLICY.md` (restore nightly dump into a
scratch DB, boot, run a conversation round-trip + memory recall) and log the result in
`audit_reports/supreme-deep-audit-reports/REAL_TESTING_LOG.md`.

## 7. Decisions / follow-up work (maintainer)

| # | Item | Why manual |
|---|------|-----------|
| 7.1 | ~~Wire **real canary traffic splitting** for `AutoSkillCreator` deployments via `CanaryRolloutController`~~ **✅ RESOLVED (2026-09-19)** — Implemented `should_route()` and `route_request()` in `evolution/canary_manager.py` with deterministic client hash-bucketing (sticky sessions), `X-Canary` header overrides (`true`/`false`/`proposal_id`), and GET `/api/v1/evolution/canary/{proposal_id}/route`. | Resolved |
| 7.2 | ~~Repoint or delete the dead `core/resilience/rollback_monitor.py`~~ **✅ RESOLVED (2026-09-19)** — Dead Cloud Run monitor removed and superseded by `core/resilience/safety_rollback_manager.py` (gzip checkpoints, SHA-256 integrity verification, auto-rollback). | Resolved |
| 7.3 | ~~Decide whether `/api/v1/evolution/forge` should require a human approval step~~ **✅ RESOLVED (2026-09-19)** — Verified `AutoSkillCreator` suspends newly generated skills via `HITLEngine.suspend_for_approval()` returning `status: "pending_approval"` (ADR-0002 compliance enforced; no autonomous installation without admin promotion). | Resolved |
| 7.4 | ~~Sweep remaining routes returning `str(e)` to clients~~ **✅ DONE in patch v2 (2026-08-30)** — `keys.py`, `conversations.py` (x3, HTTPException pass-through preserves ownership 404), `preferences.py`, `admin.py` now return generic 500s with `correlation_id` (uuid) and log full detail server-side via `logger.exception`. No further action. | ~~Code sweep~~ resolved |
| 7.5 | Move HITL/audit records to append-only storage (e.g. DB table + hash chain; `cryptographic_ledger.py` already provides the chaining logic) instead of 30-day Redis retention. | Storage design decision |
| 7.6 | Firebase-admin retirement plan (Firestore tenant path + backup tooling are the last consumers). | Architecture decision |
| 7.7 | Frontend clients of the now-authenticated endpoints: markdown export UI and the CI dashboard WebSocket (`?token=`), service topology health-stream (admin token), `/agent/terminal-stream` must send the JWT. Search `frontend/src` for `ws/dashboard`, `markdown/export`, `health-stream` and attach the stored token. | Client update required — **breaking change for anonymous callers by design** |
| 7.8 | API keys: add a per-key `scopes` column if keys are ever meant to authorize routes (currently identification + rate-limit only). | Schema change |
| 7.9 | **PATCH v4 NEW:** Set `SUPABASE_DATABASE_URL_WRITER` env var in Render. This is the canonical writable Postgres endpoint (typically the direct connection string `postgresql://postgres.<project>:<password>@db.<project>.supabase.co:5432/postgres`, NOT the pooler at port 6543). Required so `pooled_pg.execute_ddl()` and `supabase_client.bootstrap_schema()` can create `automation_executions` table + `ai_memory` schema. If not set, both fall back silently to SQLite (data NOT durable across restarts) — same as today. | Infra config |
| 7.10 | **PATCH v4 NEW:** Wire `alembic upgrade head` into Render pre-deploy (or a CI job) against the writer URL. Patch v4 added `automation_executions` to boot-time DDL as a stop-gap, but proper migration tooling is the long-term answer. | Infra wiring |
| 7.11 | **PATCH v4 NEW:** After deploying patch v4, re-check Render logs for:
  (a) absence of `ReadOnlySqlTransaction` errors,
  (b) absence of `relation "automation_executions" does not exist`,
  (c) absence of `cannot import name 'get_tenant_db'` router warning,
  (d) absence of `concurrent operations are not permitted` (isce) on `/configs/refresh` calls,
  (e) memory pressure dropping below 85%.
  If any of these re-appear, attach the new Render log file and re-run the audit. | Verification |

## 8. Secrets / env checklist after merge

- **PATCH v4 NEW:** `SUPABASE_DATABASE_URL_WRITER` — set to the Supabase DIRECT (writable) connection
  string. Required for boot DDL (creates `automation_executions`, `ai_memory`, `checkpoints` tables).
  If unset, `pooled_pg.execute_ddl()` logs a single warning and skips DDL — same as today, but
  without the cascading CRITICAL escalation.
- All other env vars unchanged from prior patch.
- `UVICORN_WORKERS` stays unset or `1` in Render (the app now hard-fails on >1 — this was
  already the enforced policy).
- Optional: set `SUPREMEAI_PUBLIC_PATHS` only if you intentionally want to re-publicize a
  path; `/api/v1/markdown` was removed from the defaults.

## 9. Live env/secrets evidence matrix (P0)

The canonical evidence matrix is `docs/deployment/ENV_EVIDENCE_MATRIX.md`
(Variable → Source → Required? → Service → Verified? → Date; verification
levels ✅ verified-live / 🟡 present-in-vault / ⬜ pending). It is
registry-drift-guarded by `backend/tests/test_env_evidence_matrix.py` against
`backend/core/config_classification.py` — a new required or condition-bearing
variable fails CI until a matrix row exists. Re-verify the ⬜/🟡 rows after any
Render/Supabase/Vercel dashboard change and record the probe date there.
