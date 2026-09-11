# Database Migration Directory

> **⚠️ This directory contains legacy migration SQL pending archival.**
>
> The repository still contains legacy and manual SQL files here. They are retained for historical and recovery purposes, but they are not an approved production migration path. Archival is intentionally tracked as a separate governance change so no deployment references are broken silently.

## Canonical Migration System

The **only active migration system** for SupremeAI is **Alembic**, located at `backend/alembic_migrations/`. All new schema changes must be made as Alembic migrations.

## Ownership Boundary

Alembic is the only migration system allowed to change deployed schemas. The SQL files currently under `backend/database/migrations/` are retained as historical or DBA-reviewed material and must not receive new production migrations until the archival move described below is completed. The `legacy/` and `manual/` trees are not active application migration paths.

## Directory Structure

```
backend/database/
├── migrations/
│   ├── README.md          ← This file
│   ├── *.sql              ← Historical SQL scripts pending archival
│   ├── legacy/            ← Earlier legacy scripts (historical only)
│   └── manual/            ← Manual migration scripts (DBA review only)
├── ../alembic_migrations/ ← ✅ CANONICAL — All new migrations go here
│   ├── env.py
│   ├── script.py.mako
│   └── versions/          ← 18 Alembic migration files
└── contracts/
    └── schema_contract.yaml
```

## Which System to Use?

| System | Path | Status | Use for |
|--------|------|--------|---------|
| **Alembic** | `backend/alembic_migrations/` | ✅ **Active** | All new schema migrations |
| Legacy SQL | `backend/database/migrations/archive/` | 📦 Archived | Historical reference only |
| Legacy SQL | `backend/database/migrations/legacy/` | 📦 Archived | Historical reference only |
| Manual | `backend/database/migrations/manual/` | 🔧 DBA only | Manual DBA operations |

## Running Alembic Migrations

```bash
cd backend
alembic upgrade head          # apply all pending migrations
alembic revision --autogenerate -m "description"  # create new migration
alembic history               # view migration history
alembic downgrade -1          # rollback one migration
```

## Migration History

The `archive/` directory contains 17 SQL scripts from early development (2026-08-19 to 2026-09-10). These scripts were the original schema definitions before Alembic was adopted. They are preserved for:

1. **Historical reference** — understanding schema evolution
2. **Disaster recovery** — if Alembic history is ever lost
3. **Audit trail** — documenting what changes were made and when

---

**Do not add new SQL files to this directory or its subdirectories. Use Alembic instead.**
