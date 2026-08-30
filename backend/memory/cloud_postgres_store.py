"""
Cloud-native PostgreSQL store using Supabase/Cloud SQL.
Replaces local SQLite for production.
"""

import os
from typing import Any

import psycopg2
from psycopg2.extras import RealDictCursor

from core.config import settings
from core.logging_config import logger


class CloudPostgresStore:
    """
    Production-grade PostgreSQL store.
    Uses Supabase or Cloud SQL connection string.
    """

    # Tables this store depends on. Schema ownership lives ONLY in Alembic
    # migrations (backend/alembic_migrations/versions/) — this class must
    # never CREATE TABLE at runtime. Runtime DDL previously caused silent
    # drift between what the code expected and what production actually
    # had (see backend/database/contracts/schema_contract.yaml and the
    # 2026-08-30 incident where task_history was missing 5 columns that
    # save_task() wrote to, so every write failed silently).
    REQUIRED_TABLES = ("task_history", "conversation_context", "verification_queue")

    def __init__(self):
        self.conn_string = getattr(settings, "database_url", "")
        self._verify_schema()

    def _get_conn(self):
        return psycopg2.connect(self.conn_string, cursor_factory=RealDictCursor)

    def _verify_schema(self):
        """Verify required tables exist. Never creates or alters schema here.

        Schema changes must go through Alembic migrations so that
        production, staging, and CI stay on one source of truth. If a
        required table is missing, we log a loud warning (and, in
        production, raise) instead of silently creating a table that
        drifts from the canonical schema contract.
        """
        try:
            with self._get_conn() as conn, conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT table_name FROM information_schema.tables
                    WHERE table_schema = 'public' AND table_name = ANY(%s)
                    """,
                    (list(self.REQUIRED_TABLES),),
                )
                found = {row["table_name"] for row in cur.fetchall()}
        except Exception as exc:  # noqa: BLE001
            logger.error(f"CloudPostgresStore: could not verify schema: {exc}")
            return

        missing = set(self.REQUIRED_TABLES) - found
        if missing:
            msg = (
                f"CloudPostgresStore: missing required tables {sorted(missing)}. "
                "Run `alembic upgrade head` (see backend/alembic_migrations/) "
                "before starting the app. Refusing to auto-create tables at "
                "runtime to avoid schema drift."
            )
            if getattr(settings, "environment", "development") == "production":
                raise RuntimeError(msg)
            logger.warning(msg)
        else:
            logger.info("CloudPostgresStore: schema verified OK")

    def save_task(self, task_data: dict[str, Any]) -> int:
        """Save task execution record."""
        with self._get_conn() as conn, conn.cursor() as cur:
            cur.execute(
                """
                    INSERT INTO task_history
                    (task_type, prompt, result, provider, cost, latency_ms, success)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """,
                (
                    task_data.get("task_type"),
                    task_data.get("prompt"),
                    task_data.get("result"),
                    task_data.get("provider"),
                    task_data.get("cost", 0.0),
                    task_data.get("latency_ms", 0),
                    task_data.get("success", True),
                ),
            )
            result = cur.fetchone()
            conn.commit()
            return result["id"]

    def get_conversation(self, session_id: str) -> dict[str, Any] | None:
        """Get conversation context by session."""
        with self._get_conn() as conn, conn.cursor() as cur:
            cur.execute(
                """
                    SELECT * FROM conversation_context
                    WHERE session_id = %s
                    ORDER BY updated_at DESC
                    LIMIT 1
                """,
                (session_id,),
            )
            result = cur.fetchone()
            return dict(result) if result else None

    def update_conversation(self, session_id: str, messages: list[dict], summary: str = ""):
        """Update or create conversation context."""
        from psycopg2.extras import Json

        with self._get_conn() as conn, conn.cursor() as cur:
            cur.execute(
                """
                    INSERT INTO conversation_context (session_id, messages, summary)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (session_id) DO UPDATE SET
                        messages = EXCLUDED.messages,
                        summary = EXCLUDED.summary,
                        updated_at = CURRENT_TIMESTAMP
                """,
                (session_id, Json(messages), summary),
            )
            conn.commit()

    def get_stats(self) -> dict[str, Any]:
        """Get system statistics."""
        with self._get_conn() as conn, conn.cursor() as cur:
            cur.execute("""
                    SELECT
                        COUNT(*) as total_tasks,
                        AVG(cost) as avg_cost,
                        SUM(cost) as total_cost,
                        AVG(latency_ms) as avg_latency,
                        COUNT(CASE WHEN success THEN 1 END)::FLOAT / COUNT(*) * 100 as success_rate
                    FROM task_history
                """)
            result = cur.fetchone()
            return dict(result) if result else {}


# Keep SQLite fallback for local dev
class SQLiteStore:
    """Local SQLite store for development only."""

    def __init__(self, db_path: str = "data/supremeai.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        # ... existing SQLite implementation ...
