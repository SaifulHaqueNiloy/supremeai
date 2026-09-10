# Legacy SQL Migration Scripts

> **⚠️ This directory contains legacy hand-written SQL scripts.**
> 
> The **primary migration system** for SupremeAI is **Alembic**, located at
> `backend/alembic_migrations/`. All new schema changes should be made as Alembic
> migrations (`alembic revision --autogenerate`), not as raw SQL files here.

## Ownership boundary

Alembic is the only migration system allowed to change deployed schemas. The SQL files in this directory, including `legacy/` and `manual/`, are immutable historical references and must not receive new migrations. Queue/task state, tenant scope, idempotency, audit records, and provider adapter state must all be introduced through Alembic revisions under `backend/alembic_migrations/versions/`.

The application queue boundary is `core.queue.task_queue_enhanced`. Celery may supervise/consume work where configured, but it does not own task contracts, tenant policy, retries, or audit semantics; those remain centralized in the application control plane.

## History

The SQL files in this directory (`01_initial_setup.sql` through `10_*.sql`) were the
original schema scripts used during early development before Alembic was adopted.
They are preserved for historical reference but are **not executed by any automated
deployment pipeline**.

## Which system to use?

| System | Path | Status | Use for |
|--------|------|--------|---------|
| **Alembic** | `backend/alembic_migrations/` | ✅ **Active** | All new schema migrations |
| Raw SQL | `backend/database/migrations/` | ⚠️ Legacy only | Historical reference |

## Running Alembic migrations

```bash
cd backend
alembic upgrade head          # apply all pending migrations
alembic revision --autogenerate -m "description"  # create new migration
alembic history               # view migration history
```

The Alembic environment (`alembic_migrations/env.py`) is configured to use
`SUPABASE_DATABASE_URL_WRITER` (or fall back to `settings.database_url`) and
autogenerate against `models.base.Base.metadata`.

---

**Do not add new SQL files to this directory.** Use Alembic instead.
