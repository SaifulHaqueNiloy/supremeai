# Render Deploy Failure — Root Cause & TODO
**Service:** `supremeai-backend-v2` (srv-da666f8u01pc739bm3t0), workspace `tea-d747ms1aae7s73bcasu0`
**Repo:** github.com/SaifulHaqueNiloy/supremeai (main) → Admin Backend (separate Render account)
**Date audited:** 2026-08-29
**Failed deploys checked:** dep-da8vqbpsrm7s73aof5p0, dep-da8voetg1s2s738o0ocg, dep-da8vkvh5efls73a740qg, dep-da8vedaioggs73de9tp0 (all `update_failed`)

---

## Root Cause (Primary — blocks deploy)

**CORS_ORIGINS validation is inconsistent across 3 code paths**, and one of them hard-crashes the process on boot when `USER_CORS_ORIGINS` / `ADMIN_CORS_ORIGINS` are unset in production:

| Layer | File | Behavior when unset |
|---|---|---|
| Soft (warn + fallback) | `core/config_validation.py::validate_production_completeness` | WARNING, uses default CORS list |
| **Hard crash** | pydantic `Settings` validator (config.py) | Raises `ValidationError` → process exits |
| Hard refuse (log only, no raise seen) | `core/app_builder.py::create_app` | ERROR log: "Refusing to fall back to localhost" |

Evidence from logs (instance `srv-da666f8u01pc739bm3t0-qfvxw`, 21:25:29 UTC):
```
pydantic_core._pydantic_core.ValidationError: 1 validation error for Settings
Value error, ❌ Production CORS origins not explicitly configured.
Must set USER_CORS_ORIGINS and/or ADMIN_CORS_ORIGINS.
```
Meanwhile a sibling instance (`-k5xk8`) booted "successfully" with only a WARNING and defaulted CORS. This inconsistency is exactly the kind of thing the project's "keep everything dynamic (ALLOWED_HOSTS etc.)" principle is meant to prevent — dynamic/auto-populate fallback needs to be the **same behavior everywhere**, not soft in two places and hard-fail in a third.

## Root Cause (Secondary — degrades health, may not be why deploy itself fails, but worth fixing same session)

1. **Supabase Postgres SSL failure**: `[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: self-signed certificate in certificate chain` on `_init_db_pool` — likely a stale/incorrect CA bundle or a proxy/pooler URL issue (asyncpg/SSL context mismatch, same class of bug as an earlier asyncpg version mismatch found 2026-08-16).
2. **No `NEON_DATABASE_URL` fallback available** → after primary DB fails, fallback also fails → `DB Pool Init Failed`.
3. **`SUPABASE_DATABASE_URL` / `SUPABASE_DATABASE_URL_POOLER` missing** → schema bootstrap aborts.
4. **`DailyLearner` fails to start**: `FATAL: ephemeral SQLite disallowed in production` — needs `EVOLUTION_DB_PATH=/mnt/gcs/evolution.db` or `EVOLUTION_STORAGE=supabase`.
5. Agent heartbeat warnings (`sentinel`, `swarm-cache`, `task-queue-worker`, `system-telemetry` — no heartbeat for 90s+) are a *symptom* of the DB pool being down, not a separate root cause.

---

## TODO

- [ ] **[Critical]** Make CORS_ORIGINS handling consistent: either (a) all three layers hard-fail with a clear one-line error, or (b) all three soft-fallback to a safe default with a loud WARNING — pick one project-wide policy and apply it everywhere. Given the "zero breakage / self-healing" principle, (b) with a loud warning is probably right, matching how `ALLOWED_HOSTS` already auto-populates.
- [ ] **[Critical]** Set `USER_CORS_ORIGINS` and `ADMIN_CORS_ORIGINS` explicitly in Render env vars for this service regardless of the above fix — don't rely on fallback for a value this security-sensitive.
- [ ] **[High]** Fix Supabase Postgres SSL cert verification failure — check whether `SUPABASE_DATABASE_URL_POOLER` needs `sslmode=require` vs `verify-full`, or whether the CA bundle used by asyncpg/psycopg is stale.
- [ ] **[High]** Set `SUPABASE_DATABASE_URL` / `SUPABASE_DATABASE_URL_POOLER` in Render env vars (currently missing → schema bootstrap fails).
- [ ] **[Medium]** Fix `DailyLearner`: set `EVOLUTION_STORAGE=supabase` (preferred, matches "no local device" direction) or `EVOLUTION_DB_PATH=/mnt/gcs/evolution.db`.
- [ ] **[Medium]** Audit all "dynamic config" fallback points (ALLOWED_HOSTS, CORS_ORIGINS, and any others) for the same soft-vs-hard inconsistency pattern — this is likely to recur elsewhere given the project's stated "everything dynamic" direction.
- [ ] **[Low]** `BugProphet` warning: `No module named 'scripts.devops.bug_prophet'` — dead import, either restore the module or remove the startup call.

---

## Suggested immediate fix order
1. Set the two CORS env vars in Render dashboard (unblocks deploy fastest, no code change).
2. Fix Supabase DB URL env vars + SSL issue (unblocks real DB connectivity).
3. Then do the code-level consistency fix for CORS validation across the 3 layers (prevents this class of bug recurring).
