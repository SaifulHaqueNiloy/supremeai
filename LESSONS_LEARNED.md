# LESSONS_LEARNED.md — Backend Interconnection Audit

> Max 12KB per AGENTS.md Memory Protocol.

## Session outcome
Baseline import-graph audit of backend/ is complete and reproducible. The auditor
was pathologically slow (>30s, appearing to hang) for three independent reasons;
all are fixed and the run now completes in ~16s on the WSL /mnt/F mount.

## RCA — why it looked like a hang
The tool reported a 30s timeout, but _populate_index + audit_module +
build_internal_edges + reachable_closure are all pure in-memory over an AST
index. The real cost was filesystem stat I/O on the WSL NTFS mount
(`/mnt/F/.../supremeai backup/...` has spaces + /mnt indirection):

1. Per-file Path.resolve() in path_to_module. WSL /mnt resolves each path
   component via stat; 1,734x compounded. Fix: use Path.relative_to(root)
   (pure string when both absolute) with resolve() only as a fallback.
2. _count_lines re-opened every orphan file (re-read from disk). With ~1,594
   orphans this alone was several seconds of extra I/O. Fix: capture line count
   once during the single read in _populate_index (_MODULE_LINES), then delete
   _count_lines entirely.
3. rglob traversed into .venv/.kilo/node_modules (potential 100k+ files).
   Fix: os.walk(topdown) + dirnames[:] prune on _SKIP_DIRS.

Note: the run_commands 30s tool window sometimes returned "Command timed out"
even when the process had actually finished and flushed to a redirect file.
Treat empty tool output + a complete log file as SUCCESS (confirmed via
_t.log ending in DONE and _m.out ending in "JSON report written").

## Audit design notes (truth)
- Static AST only; no package import. No supabase/torch/loguru needed.
- is_internal uses precomputed _TOP_LEVEL -> O(1), no FS stat.
- module_to_path / module_symbols are dict.get -> O(1).
- Known blind spot: symbols exposed dynamically via module-level __getattr__
  (e.g. the core/error_bus.py deprecation shim delegating to
  core.errors.error_bus) appear as "not found" but resolve at runtime. This is
  static-analysis limitation, not a bug.

## Remediation clusters (51 live broken)
- core.error_bus.with_error_bus (14 live) — deprecated shim; canonical
  core.errors.error_bus exports with_error_bus (line 18, __all__ confirmed).
- core.pgbouncer_pool.get_db_pool (4); core.metrics_collector
  metrics_collector/record_cache_access (3); core.tenant_db
  TenantAwareFirestore (2); core.logging_config setup_logging/logger (live).
- core.idempotency_middleware.IdempotencyMiddleware (1).
- core.redis_manager module missing (core.cache `from . import redis_manager`).
- core.security missing: behavioral_analyzer, enhanced_ast_scanner (1 each).
- core.gcp_firestore.get_firestore_client / GCPFirestoreVerificationQueue.
- core.rate_limiter.AsyncRateLimiter + ADMIN/USER_ORIGIN_DENYLIST (live).
- services.* get_logger / timed (imported by live api.* / core.*).

Recommended order:
1. Migrate all `from core.error_bus import X` -> `from core.errors.error_bus
   import X` AND fix generator scripts/devops/wire_error_bus.py to emit the
   canonical path (stops new violations). Removes 14/51 live findings.
2. core.redis_manager: missing on disk — verify real target before fixing.
3. core.security missing sub-modules — confirm file exists or fix path.
4. Singleton symbol drifts — verify each target export; typical rename/drop.

Status: remediation NOT executed this session (100+ file migrations are large
and must be validated per-cluster by re-running the audit).
