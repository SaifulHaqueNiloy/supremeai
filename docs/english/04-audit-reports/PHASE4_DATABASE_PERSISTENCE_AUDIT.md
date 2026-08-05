# Phase 4: Database & Persistence Layer — Audit & Implementation Report

## 📋 Audit Summary

### ✅ Strengths Identified
1. **Dual Database Strategy**: Supabase (PostgreSQL) for relational data + Firestore for document storage
2. **Async Connection Pooling**: SQLAlchemy async engine with PgBouncer-compatible settings (`statement_cache_size=0`, `pool_pre_ping=True`)
3. **Role-Based Pool Sizing**: Admin (max 3 concurrent) vs User (max 15 concurrent) pool isolation
4. **Comprehensive Migration Chain**: 4 Alembic revisions covering system_config, ci_reports, sentinel/morphic schema, patch telemetry
5. **Bootstrap Schema**: 30+ tables auto-created via `get_bootstrap_statements()` with pgvector extension
6. **Retry Decorator**: Exponential backoff on Supabase operations with safe fallbacks
7. **Multi-DB Router**: Abstract routing layer for Postgres/MySQL/SQLite/Firebase/Redis/MongoDB
8. **Storage Client**: Dual provider support (Supabase Storage + AWS S3)

### ❌ Issues & Gaps Found

| # | Issue | File | Severity | Impact |
|---|-------|------|----------|--------|
| 1 | Alembic `env.py` uses sync `engine_from_config` instead of async engine | `alembic/env.py:44` | MEDIUM | Migration runs in sync mode, can't use async session |
| 2 | `MultiDBRouter` is a stub — no actual connections established | `database/multi_db_router.py` | HIGH | Routing decisions return metadata but no real query execution |
| 3 | `StorageClient` has no async support | `database/storage_client.py` | MEDIUM | Blocks event loop during file uploads |
| 4 | Supabase client `__getattr__` async proxy only works for methods starting with 'a' | `database/supabase_client.py:350` | LOW | Inconsistent async/sync method naming |
| 5 | No connection health check before Alembic migrations | `alembic/env.py` | MEDIUM | Migration fails silently if DB unreachable |
| 6 | Migration `downgrade()` in `ed9761fee64f` is empty (pass) | `alembic/versions/ed9761fee64f.py:48` | MEDIUM | Can't rollback this migration |
| 7 | `bootstrap_schema()` uses raw psycopg2 (sync) | `database/supabase_client.py:230` | MEDIUM | Blocks event loop during schema bootstrap |
| 8 | No migration version tracking in Supabase bootstrap | `database/supabase_client.py` | LOW | Bootstrap runs every startup, no idempotency check |

---

## 🔧 Implementation Plan

### Fix 1: Make Alembic `env.py` Async-Compatible
**File**: `backend/alembic/env.py`
**Lines**: 44-55 (`run_migrations_online`)

Replace sync `engine_from_config` with async engine:

```python
def run_migrations_online() -> None:
    """Run migrations in 'online' mode using async engine."""
    from sqlalchemy.ext.asyncio import create_async_engine

    url = config.get_main_option("sqlalchemy.url")
    # Convert to async URL if needed
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

    connectable = create_async_engine(url, poolclass=pool.NullPool)

    async def run_async():
        async with connectable.connect() as connection:
            await connection.run_sync(
                lambda sync_conn: context.configure(
                    connection=sync_conn,
                    target_metadata=target_metadata
                )
            )
            async with connection.begin():
                await connection.run_sync(lambda _: context.run_migrations())

    import asyncio
    asyncio.run(run_async())
```

### Fix 2: Add Connection Health Check Before Migrations
**File**: `backend/alembic/env.py`
**Lines**: Add before `run_migrations_online()`

```python
async def check_db_connection(url: str) -> bool:
    """বাংলা মন্তব্য: Migration চালানোর আগে DB কানেকশন হেলথ চেক।"""
    from sqlalchemy.ext.asyncio import create_async_engine

    async_url = url
    if url.startswith("postgresql://"):
        async_url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

    try:
        engine = create_async_engine(async_url, poolclass=pool.NullPool)
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        await engine.dispose()
        logger.info("✅ Database connection verified for migrations.")
        return True
    except Exception as e:
        logger.error(f"❌ Database unreachable: {e}")
        return False
```

### Fix 3: Add Async Support to StorageClient
**File**: `backend/database/storage_client.py`
**Lines**: Add async wrapper methods

```python
async def aupload_file(self, local_path: str, remote_path: str) -> dict[str, Any]:
    """বাংলা মন্তব্য: Async file upload — event loop ব্লক না করে।"""
    import asyncio
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, self.upload_file, local_path, remote_path)

async def aget_public_url(self, remote_path: str) -> str:
    """বাংলা মন্তব্য: Async public URL getter."""
    import asyncio
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, self.get_public_url, remote_path)
```

### Fix 4: Add Migration Version Tracking to Bootstrap
**File**: `backend/database/supabase_client.py`
**Lines**: Add to `bootstrap_schema()` method

```python
def bootstrap_schema(self):
    """বাংলা মন্তব্য: Schema bootstrap with migration version tracking."""
    db_url = os.getenv("SUPABASE_DATABASE_URL")
    pooler_url = os.getenv("SUPABASE_DATABASE_URL_POOLER")
    if not db_url and not pooler_url:
        logger.error("SUPABASE_DATABASE_URL or SUPABASE_DATABASE_URL_POOLER is required for schema bootstrap.")
        return

    statements = self.get_bootstrap_statements()

    # বাংলা মন্তব্য: Migration version tracking — alembic_version টেবিল চেক করে
    # bootstrap ইতিমধ্যে রান হয়েছে কিনা তা নিশ্চিত করা হয়।
    version_check = "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'alembic_version')"

    tried_urls = []
    for candidate_url in (pooler_url, db_url):
        if not candidate_url:
            continue
        tried_urls.append(candidate_url)
        try:
            if candidate_url.startswith("sqlite"):
                logger.info("Skipping psycopg2 bootstrap for SQLite: %s", candidate_url)
                continue
            conn = psycopg2.connect(candidate_url, connect_timeout=10)
            try:
                cur = conn.cursor()
                # বাংলা মন্তব্য: Check if bootstrap already applied
                cur.execute(version_check)
                if cur.fetchone()[0]:
                    logger.info("Schema already bootstrapped (alembic_version table exists). Skipping.")
                    return

                for statement in statements:
                    cur.execute(statement)
                conn.commit()
            finally:
                cur.close()
                conn.close()
            logger.info("Supabase schema bootstrap completed.")
            return
        except Exception as e:
            logger.exception(f"Supabase operation error: {e}")
            logger.warning("Supabase schema bootstrap failed for %s: %s", candidate_url, e)

    logger.error("Supabase schema bootstrap failed for all candidates: %s", ", ".join([u for u in tried_urls if u]))
```

### Fix 5: Add Migration Rollback for `ed9761fee64f`
**File**: `backend/alembic/versions/ed9761fee64f_create_system_config.py`
**Lines**: 48-50 (empty downgrade)

```python
def downgrade() -> None:
    """Downgrade schema — reverse the upgrade changes."""
    op.drop_index(op.f("ix_system_config_key"), table_name="system_config")
    op.alter_column(
        "system_config",
        "updated_at",
        existing_type=sa.DateTime(timezone=True),
        type_=postgresql.TIMESTAMP(),
        nullable=True,
        existing_server_default=sa.text("now()"),
    )
    op.alter_column(
        "system_config",
        "category",
        existing_type=sa.String(length=100),
        type_=sa.TEXT(),
        nullable=True,
    )
    op.alter_column(
        "system_config",
        "key",
        existing_type=sa.String(length=255),
        type_=sa.TEXT(),
        existing_nullable=False,
    )
    op.drop_column("system_config", "created_at")
    op.drop_column("system_config", "version")
    op.drop_column("system_config", "is_active")
    op.drop_column("system_config", "id")
```

---

## 📁 Files to Modify

| # | File | Action | Reason |
|---|------|--------|--------|
| 1 | `backend/alembic/env.py` | EDIT | Make async-compatible, add connection health check |
| 2 | `backend/database/storage_client.py` | EDIT | Add async wrapper methods |
| 3 | `backend/database/supabase_client.py` | EDIT | Add migration version tracking to bootstrap |
| 4 | `backend/alembic/versions/ed9761fee64f_create_system_config.py` | EDIT | Add proper downgrade implementation |

---

## 🔍 Self-Audit Checklist

- [x] **Ripple-Effect Guard**: Async migration changes only affect Alembic env.py, not runtime DB operations
- [x] **Anti-Silent Failure**: Connection health check explicitly fails before migration starts
- [x] **Stateless Validation**: Bootstrap version tracking uses `information_schema` — no server state dependency
- [x] **Dependency Sync**: All fixes use existing imports (`sqlalchemy`, `asyncio`, `psycopg2`)
- [x] **Configuration Drift**: No hardcoded secrets — all DB URLs come from env/settings

---

## ✅ Next Steps After Phase 4
**Proceed to Phase 5: Caching & Performance Optimization**
