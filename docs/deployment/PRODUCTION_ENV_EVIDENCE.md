# Production Environment Evidence Matrix

> Task: production contract closure (`final-test/production-contract-closure`), 2026-09-14.
> Companion to `docs/audits/MANUAL_STEPS.md` (§8 "Secrets / env checklist after merge"),
> which is the **historical input** for this file — MANUAL_STEPS records what had to be
> done per patch; this file tracks what is *actually configured in the live environment*.

## Status: ⬜ NOT VERIFIED — every `Verified?` cell is pending

The lead agent cannot verify live secrets from the repo (they live in Infisical, the
Render dashboard and GitHub secret storage). An operator with dashboard access must
walk the matrix below once per deployment change and fill in the two right-hand columns.

## How to verify (per row)

Run this 5-step checklist for each variable before ticking `✅ verified`:

1. **Value present** — the variable is non-empty in the declared source
   (Infisical path, Render service → Environment, or GitHub → Settings → Secrets).
2. **Format valid** — spot-check the shape WITHOUT printing the full value:
   - `SUPREMEAI_JWT_SECRET` ≥ 64 chars; `ENCRYPTION_KEY` = 44-char Fernet url-safe base64
   - `REDIS_URL` = `rediss://…` (TLS) for Upstash; `SUPABASE_DATABASE_URL_POOLER` on port `6543`
   - `STRIPE_API_KEY` starts `sk_live_` (or `sk_test_` in staging); `SENTRY_DSN` = `https://…ingest…sentry.io/…`
   - `USER_CORS_ORIGINS` / `ADMIN_CORS_ORIGINS` are JSON lists of https origins; `ALLOWED_HOSTS` is comma-separated hosts
3. **Service restarts clean** — after saving, trigger a deploy; the boot must show no
   CRITICAL validation error (boot fails fast on `dev_password_only` docs password,
   missing docs password with docs enabled, `debug=true` in prod, etc.).
4. **Health green** — `curl -s -o /dev/null -w "%{http_code}" https://<backend>/health/ready`
   returns `200` (canonical path — see `docs/operations/OPERATIONAL_CONTRACTS.md` §1).
5. **One authenticated request works** — login → `GET /api/v1/auth/me` succeeds, one
   `X-Admin-Secret` call to an `/internal/*` endpoint succeeds (or returns 403 only for a
   *wrong* secret), and `/docs` is either 404 (disabled) or Basic-auth challenged (enabled).

> Do not paste secret values into this file, PRs, issues, or chat. Record only the date
> and the initials of who verified.

## Evidence matrix — secrets and credentials

| Variable | Source (Infisical path / Render env / GitHub secret) | Required? | Service(s) | Verified? | Last verified date |
|---|---|---|---|---|---|
| `DATABASE_URL` | Render env (core API) ← Infisical `prod/DATABASE_URL` | Required | core API | ⬜ pending | — |
| `SUPABASE_URL` | Render env ← Infisical `prod/SUPABASE_URL` | Required | core, worker, scraper, mcp | ⬜ pending | — |
| `SUPABASE_KEY` (anon) | Render env ← Infisical `prod/SUPABASE_KEY` | Required | core, worker, scraper, mcp | ⬜ pending | — |
| `SUPABASE_SERVICE_ROLE_KEY` | Render env (server-side only) ← Infisical `prod/SUPABASE_SERVICE_ROLE_KEY` | Required | core (never frontend) | ⬜ pending | — |
| `SUPABASE_DATABASE_URL_POOLER` | Render env ← Infisical `prod/SUPABASE_DATABASE_URL_POOLER` (port 6543) | Required — readiness gate | core | ⬜ pending | — |
| `SUPABASE_DATABASE_URL_WRITER` | Render env (direct connection, port 5432) | Recommended — boot DDL (see MANUAL_STEPS §7.9) | core | ⬜ pending | — |
| `REDIS_URL` | Render env ← Infisical `prod/REDIS_URL` (Upstash `rediss://`) | Required — rate limiting / cache | core, worker | ⬜ pending | — |
| `REDIS_PASSWORD` | Infisical `prod/REDIS_PASSWORD` (embedded in `REDIS_URL` for Upstash; standalone for k8s Secret) | Conditional | core (k8s), worker | ⬜ pending | — |
| `SUPREMEAI_JWT_SECRET` / `JWT_SECRET` | Render env ← Infisical `prod/SUPREMEAI_JWT_SECRET` (≥ 64 chars) | Required | core, worker, scraper, mcp | ⬜ pending | — |
| `ENCRYPTION_KEY` / `SUPREMEAI_ENCRYPTION_KEY` | Render env ← Infisical `prod/ENCRYPTION_KEY` (Fernet, 44 chars) | Required | core | ⬜ pending | — |
| `SUPREMEAI_ADMIN_SECRET` | Render env secret ← Infisical `prod/SUPREMEAI_ADMIN_SECRET` | Required for `/internal/*` automation (header `X-Admin-Secret`; **no** `docs_password` fallback anymore) | core | ⬜ pending | — |
| `SUPREMEAI_DOCS_ENABLED` | Render env — must be unset/false in prod unless docs are intentionally exposed | Required (policy flag) | core | ⬜ pending | — |
| `SUPREMEAI_DOCS_USERNAME` | Render env (default `admin`) | Conditional — only when docs enabled | core | ⬜ pending | — |
| `SUPREMEAI_DOCS_PASSWORD` | Render env secret — ≥ 12 chars when docs enabled; `dev_password_only` hard-rejected at boot | Conditional — only when docs enabled | core | ⬜ pending | — |
| `USER_CORS_ORIGINS` | Render env (JSON list; takes precedence over `CORS_ORIGINS`) | Required | core | ⬜ pending | — |
| `ADMIN_CORS_ORIGINS` | Render env (JSON list) | Required | core | ⬜ pending | — |
| `ALLOWED_HOSTS` | Render env (comma-separated) | Required | core | ⬜ pending | — |
| `FRONTEND_URL` / `BACKEND_URL` / `ADMIN_URL` | Render env ← Infisical `prod/*` (canonical portal endpoints) | Required | core | ⬜ pending | — |
| `USER_BACKEND_URL` | Render env + GitHub secret/variable (frontend probes + CI `VITE_USER_BACKEND` chain) | Required | core, frontend build | ⬜ pending | — |
| `ADMIN_BACKEND_URL` | Render env + GitHub secret/variable (CI `VITE_ADMIN_BACKEND` chain) | Required | admin portal, frontend build | ⬜ pending | — |
| `GEMINI_API_KEY` | Render env ← Infisical `prod/GEMINI_API_KEY` | Required (Stage-1 writer in the LLM router) | core, worker | ⬜ pending | — |
| `GROQ_API_KEY` | Render env ← Infisical `prod/GROQ_API_KEY` (+ `GROQ_RPM/RPD/TPM_LIMIT` companions) | Required (free-tier router) | core | ⬜ pending | — |
| `OPENROUTER_API_KEY` | Render env ← Infisical `prod/OPENROUTER_API_KEY` (+ `OPENROUTER_RPM/RPD_LIMIT`) | Required | core | ⬜ pending | — |
| `DEEPSEEK_API_KEY` | Render env ← Infisical `prod/DEEPSEEK_API_KEY` (+ `DEEPSEEK_BASE_URL`) | Optional — provider fallback | core | ⬜ pending | — |
| `OPENAI_API_KEY` | Render env ← Infisical `prod/OPENAI_API_KEY` | Optional — provider fallback | core | ⬜ pending | — |
| `STRIPE_API_KEY` | Infisical `prod/STRIPE_API_KEY` (`sk_live_` / `sk_test_`) | Required for billing | core | ⬜ pending | — |
| `STRIPE_WEBHOOK_SECRET` | Render env ← Infisical `prod/STRIPE_WEBHOOK_SECRET` | Required for billing webhooks | core | ⬜ pending | — |
| `SENTRY_DSN` | Render env ← Infisical `prod/SENTRY_DSN` | Recommended (SLO reporting, see `docs/operations/SLO_AND_ALERTS.md`) | core, worker, scraper | ⬜ pending | — |
| `TELEGRAM_BOT_TOKEN` | Render env ← Infisical `prod/TELEGRAM_BOT_TOKEN` | Required for the Telegram messaging face | core (bot role) | ⬜ pending | — |
| `RENDER_SERVICE_IDS` | GitHub secret / Render API (consumed by `scripts/deploy/check_render_svc.py`, `trigger_render_deploy.py`, `update_render_env2.py` automation) | Conditional — only if Render automation scripts are used | automation | ⬜ pending | — |
| `INFISICAL_CLIENT_ID` | GitHub secret `INFISICAL_CLIENT_ID` (ci.yml Infisical steps) | Required for CI secret sync | CI | ⬜ pending | — |
| `INFISICAL_CLIENT_SECRET` | GitHub secret `INFISICAL_CLIENT_SECRET` (+ `INFISICAL_PROJECT_SLUG`) | Required for CI secret sync | CI | ⬜ pending | — |

## Contract-critical policy flags (not secrets — must exist with the RIGHT value, not hidden)

| Variable | Expected value in production | Why it matters | Verified? | Last verified date |
|---|---|---|---|---|
| `SUPREMEAI_SERVICE_ROLE` | `core` (or `monolith`/`user`) on the main API node | `SUPABASE_ALLOW_DB_DEGRADATION` is ignored for these roles — DB failure ⇒ NOT READY | ⬜ pending | — |
| `SUPABASE_ALLOW_DB_DEGRADATION` | `false`/unset on core; `true` only on worker/scraper/mcp | DB-degradation escape hatch is role-gated (contract §4) | ⬜ pending | — |
| `SECURITY_MAX_BODY_BYTES` / `SECURITY_MAX_QUERY_LENGTH` / `SECURITY_MAX_HEADER_SIZE` | defaults 10MB / 2048 / 8192 unless tuned | RequestValidationMiddleware limits are env-driven (contract §5) | ⬜ pending | — |
| `SECURITY_FALLBACK_RATE_LIMIT` / `SECURITY_FALLBACK_RATE_WINDOW` | defaults 100 / 60 | In-memory emergency fallback only — Redis limiter is authoritative | ⬜ pending | — |
| `RATE_LIMIT_ENABLED` | `true` (unset = enabled) | `false` disables the in-process fallback limiter | ⬜ pending | — |
| `VITE_USER_BACKEND` / `VITE_ADMIN_BACKEND` / `VITE_API_URL` | real https backend origins at BUILD time | Production frontend builds hard-fail otherwise (contract §6) | ⬜ pending | — |
| `UVICORN_WORKERS` | unset or `1` | App hard-fails on >1 (long-standing policy) | ⬜ pending | — |

## Maintenance

- **Update this file after every deployment change**: new variable, rotation, provider
  move (Infisical ⇄ Render), or service addition ⇒ verify the affected rows and re-date them.
- **CI does not enforce this file yet.** Nothing fails if a row goes stale — a future
  task may add a drift check (`scripts/ci/`); until then this is a human-discipline contract.
- Historical checklist input: `docs/audits/MANUAL_STEPS.md` §7–§8 (retained as-is; do not
  merge back — that file is an audit artifact).
