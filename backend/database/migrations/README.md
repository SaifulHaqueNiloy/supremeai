# Database Migration Directory

> **✅ ARCHIVED (Task 7-a, 2026-09-14): all legacy raw SQL now lives in `legacy/`.**
>
> This directory no longer contains any active or executable migration SQL at
> its top level. It is retained only as the home of the read-only archive
> subdirectories below.

## Canonical Migration System

**Alembic (`backend/alembic_migrations/`) is THE canonical migration path for
SupremeAI.** Every new table or schema change MUST ship as an Alembic
revision — raw SQL files are no longer an accepted way to change the schema.
See `backend/alembic_migrations/README` for the workflow.

## Directory Structure

```
backend/database/
├── migrations/
│   ├── README.md          ← This file
│   ├── legacy/            ← 📦 ARCHIVED legacy SQL (read-only; see legacy/README.md)
│   ├── archive/           ← Early-development scripts relocated from root migrations/
│   └── manual/            ← Manual DBA-operation scripts (DBA review only)
├── ../alembic_migrations/ ← ✅ CANONICAL — All new migrations go here
│   ├── env.py
│   ├── script.py.mako
│   └── versions/          ← Canonical Alembic migration files
└── contracts/
    └── schema_contract.yaml
```

## Ownership Boundary

Alembic is the only migration system allowed to change deployed schemas.
The SQL trees under `legacy/`, `archive/`, and `manual/` are historical or
DBA-reviewed material, are not wired into any automated runner, and must not
receive new production migrations.

## Running Alembic Migrations

```bash
cd backend
alembic upgrade head          # apply all pending migrations
alembic revision --autogenerate -m "description"  # create new migration
alembic history               # view migration history
alembic downgrade -1          # rollback one migration
```

---

**Do not add new SQL files to this directory or its subdirectories. Use Alembic instead.**
