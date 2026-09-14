# Legacy SQL Migration Archive

> **📦 ARCHIVE — read-only. Do not add, edit, or execute files here.**
>
> Alembic (`backend/alembic_migrations/`) is THE canonical migration path for
> SupremeAI. Every new table/schema change MUST ship as an Alembic revision.
> The SQL files in this directory were moved here from
> `backend/database/migrations/*.sql` (Task 7-a, 2026-09-14) so that the live
> migrations directory contains no executable raw SQL. History is preserved
> via `git mv` — use `git log --follow <file>` to trace a file's past.

## Why these files are archived

- They were applied to the Supabase/PostgreSQL database **before** Alembic was
  adopted, or they are one-off Supabase SQL Editor scripts (RLS, RPCs, seeds)
  that never had Alembic wiring.
- None of them are wired into any automated runner — they were applied manually.
- Keeping them next to the live migrations directory implied a second, parallel
  migration path, which violates the "single source of truth" migration policy.

## Disposition map

| Legacy file | Disposition |
|---|---|
| `001_pgvector_match_fn.sql` | Superseded by Alembic revision `2026_09_13_100000_add_ai_memory_table.py` (ai_memory table + pgvector indexes + `match_ai_memory` RPC). |
| `01_initial_setup.sql` | Historical (github_repos / system_config / feature_flags). system_config superseded by Alembic revision `ed9761fee64f_create_system_config.py`; rest Supabase-managed baseline. |
| `02_phase2_setup.sql` | Historical / Supabase-managed (audit_logs, tools_registry, dynamic_skills). |
| `03_user_preferences_and_metrics.sql` | Historical / Supabase-managed (user_preferences, usage_metrics). |
| `04_schema_upgrade.sql` | Historical / Supabase-managed (admin-plan schema upgrade). |
| `05_seed_github_repos.sql` | Historical seed data (not schema); Supabase-managed. |
| `06_referral_system.sql` | Historical / Supabase-managed (referral_codes, referral_redemptions). |
| `07_tenant_config.sql` | Historical — superseded by `10_tenant_sso_offline.sql` (renumbered to avoid a migration conflict, see its header). |
| `08_sso_configs.sql` | Historical / Supabase-managed (sso_configs). |
| `09_offline_sync_logs.sql` | Historical / Supabase-managed (offline_sync_logs). |
| `10_tenant_sso_offline.sql` | Historical / Supabase-managed (rebuilt tenant_limits + tenant config). |
| `15_add_user_indexes.sql` | Superseded by Alembic revision `2f7b3c5f620e_add_missing_indexes.py`. |
| `16_add_match_experiences_rpc.sql` | Supabase-managed RPC (pgvector `match_experiences` similarity search). |
| `17_enable_rls.sql` | Supabase-managed RLS baseline. Contract regression-locked by `backend/tests/test_rls_policy_coverage.py`. |
| `18_fix_missing_rls_policies.sql` | Supabase-managed RLS policy fix (deny-all bug). Regression-locked by `backend/tests/test_rls_policy_coverage.py` (which reads this file from `legacy/`). |
| `19_harden_knowledge_base.sql` | Historical / Supabase-managed (knowledge_base long-term contract v1). |
| `20_create_browser_credentials.sql` | Historical / Supabase-managed (browser_credentials + strict RLS). |
| `21_render_account_preflight.sql` | Superseded by Alembic revision `2026_09_06_120000_add_render_account_state.py` (render account state + preflight audit events). |

Sibling archives (pre-existing, unchanged by the archival move):

- `../archive/` — early-development scripts relocated from the root `migrations/` tree.
- `../manual/` — DBA-reviewed manual operations (e.g. `20260907_canonical_control_plane.sql`), never executed by automation.

## Rules

1. **No new SQL files here.** New schema changes get Alembic revisions
   (`cd backend && alembic revision --autogenerate -m "..."`).
2. **Do not "run" this archive** against a fresh environment; a fresh
   environment is brought up with `alembic upgrade head` plus the
   Supabase-side objects documented in `docs/api-database/`.
3. These files are kept for audit trail and disaster recovery only.
