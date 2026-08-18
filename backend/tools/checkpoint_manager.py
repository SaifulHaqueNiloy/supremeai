import json
import sqlite3
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from loguru import logger

from core.persistence import pooled_pg
from core.persistence.write_behind import WriteBehindBatcher

# শেয়ার্ড ইউটিলিটি — Firestore ও টেস্ট এনভায়রনমেন্ট চেক কেন্দ্রীভূত
from utils.environment import is_test_environment
from utils.firestore_helpers import firestore, get_firestore_db

_PG_SCHEMA = """
    CREATE TABLE IF NOT EXISTS task_checkpoints (
        task_id TEXT PRIMARY KEY,
        step_index INTEGER,
        state TEXT,
        step_log TEXT,
        created_at TIMESTAMPTZ DEFAULT now(),
        resumed BOOLEAN DEFAULT FALSE
    )
"""

# বাংলা মন্তব্য: পুরনো টেবিলে step_log কলাম না থাকতে পারে — নিরাপদে যোগ করি।
_PG_ADD_STEP_LOG = """
    ALTER TABLE task_checkpoints ADD COLUMN IF NOT EXISTS step_log TEXT
"""

_UPSERT_SQL = """
    INSERT INTO task_checkpoints (task_id, step_index, state, step_log, resumed)
    VALUES (%s, %s, %s, %s, %s)
    ON CONFLICT (task_id) DO UPDATE SET
        step_index = EXCLUDED.step_index,
        state = EXCLUDED.state,
        step_log = EXCLUDED.step_log,
        created_at = now()
"""


@dataclass
class Checkpoint:
    task_id: str
    step_index: int
    state: dict[str, Any]
    created_at: str
    resumed: bool = False
    # বাংলা মন্তব্য: Event-sourced step log — প্রতিটি স্টেপের ইনপুট/আউটপুট/ts,
    # যাতে ক্র্যাশের পর ঠিক যে স্টেপে আটকেছিল সেখান থেকে resume করা যায় (Zero Redundant Work)।
    step_log: list[dict[str, Any]] = field(default_factory=list)


class CheckpointManager:
    """Persists task execution state in Postgres (preferred, durable across restarts),
    Google Cloud Firestore (Serverless & Stateful, unchanged fallback), or local SQLite
    (last-resort fallback / explicit test mode — NOT durable across restarts)."""

    _batcher: WriteBehindBatcher | None = None

    def __init__(self, db_path: str | None = None):
        self.collection_name = "checkpoints"
        self._db = None
        self.db_path = db_path

        # রিফ্যাক্টর: সরাসরি firestore.Client() এর বদলে শেয়ার্ড হেল্পার ব্যবহার
        if db_path or is_test_environment():
            self.mode = "sqlite"
            self.db_path = db_path or "checkpoints.db"
            self._init_sqlite()
            logger.info(f"Initialized SQLite CheckpointManager at {self.db_path}")
        elif pooled_pg.is_available():
            try:
                pooled_pg.execute(_PG_SCHEMA)
                pooled_pg.execute(_PG_ADD_STEP_LOG)
                if CheckpointManager._batcher is None:
                    CheckpointManager._batcher = WriteBehindBatcher(
                        name="task_checkpoints", flush_interval=1.0, max_batch=100
                    )
                self.mode = "pg"
                logger.info("Initialized Postgres CheckpointManager (write-behind batched).")
            except Exception as exc:
                logger.error(f"Postgres CheckpointManager init failed, falling back: {exc}")
                self._init_fallback()
        else:
            self._init_fallback()

    def _init_fallback(self) -> None:
        """Firestore, then local SQLite as a last resort — unchanged prior behavior."""
        self._db = get_firestore_db()
        if self._db is not None:
            self.mode = "firestore"
            logger.info("Initialized Firestore CheckpointManager")
        else:
            self.mode = "sqlite"
            self.db_path = "checkpoints.db"
            self._init_sqlite()
            logger.warning(f"Initialized SQLite CheckpointManager at {self.db_path} — NOT durable across restarts.")

    def _init_sqlite(self):
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS checkpoints (
                    task_id TEXT PRIMARY KEY,
                    step_index INTEGER,
                    state TEXT,
                    step_log TEXT,
                    created_at TEXT,
                    resumed INTEGER DEFAULT 0
                )
            """)
            # বাংলা মন্তব্য: পুরনো DB-তে step_log কলাম থাকতে পারে না — নিরাপদে যোগ করি।
            try:
                conn.execute("ALTER TABLE checkpoints ADD COLUMN step_log TEXT")
            except sqlite3.OperationalError:
                # Column already exists from a prior migration — idempotent no-op.
                logger.debug("checkpoints.step_log column already exists; skipping ALTER.")
            conn.commit()
        finally:
            conn.close()

    def save(
        self,
        task_id: str,
        step_index: int,
        state: dict[str, Any],
        step_log: list[dict[str, Any]] | None = None,
    ) -> bool:
        step_log = step_log or []
        if self.mode == "pg":
            try:
                # `resumed` intentionally not reset here — ON CONFLICT preserves
                # whatever value is already in the row, matching prior SQLite semantics
                # where an existing row's `resumed` flag was read-then-reused.
                CheckpointManager._batcher.submit(
                    _UPSERT_SQL,
                    (task_id, step_index, json.dumps(state), json.dumps(step_log), False),
                )
                return True
            except Exception as exc:
                logger.error(f"Failed to save Postgres checkpoint: {exc}")
                return False

        if self.mode == "sqlite":
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT resumed FROM checkpoints WHERE task_id = ?", (task_id,))
                row = cursor.fetchone()
                resumed = row[0] if row else 0

                cursor.execute(
                    """
                    INSERT OR REPLACE INTO checkpoints (task_id, step_index, state, step_log, created_at, resumed)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        task_id,
                        step_index,
                        json.dumps(state),
                        json.dumps(step_log),
                        datetime.now(UTC).isoformat(),
                        resumed,
                    ),
                )
                conn.commit()
                conn.close()
                return True
            except Exception as exc:
                logger.error(f"Failed to save SQLite checkpoint: {exc}")
                return False

        if not self._db:
            return False
        try:
            doc_ref = self._db.collection(self.collection_name).document(task_id)
            doc = doc_ref.get()
            resumed = doc.to_dict().get("resumed", False) if doc.exists else False

            doc_ref.set(
                {
                    "task_id": task_id,
                    "step_index": step_index,
                    "state": json.dumps(state),
                    "step_log": json.dumps(step_log),
                    "created_at": datetime.now(UTC).isoformat(),
                    "resumed": resumed,
                }
            )
            logger.info(f"Firestore checkpoint saved for task_id={task_id} step={step_index}")
            return True
        except Exception as exc:
            logger.error(f"Failed to save Firestore checkpoint: {exc}")
            return False

    def load(self, task_id: str) -> Checkpoint | None:
        if self.mode == "pg":
            try:
                # Flush first: a task resuming immediately after a save() (same
                # process, e.g. crash-recovery retry loop) must see its own write.
                CheckpointManager._batcher.flush()
                rows = pooled_pg.query(
                    "SELECT task_id, step_index, state, step_log, created_at, resumed FROM task_checkpoints WHERE task_id = %s",
                    (task_id,),
                )
                if not rows:
                    return None
                row = rows[0]
                cp = Checkpoint(
                    task_id=row[0],
                    step_index=row[1],
                    state=json.loads(row[2]),
                    created_at=str(row[4]),
                    resumed=bool(row[5]),
                    step_log=json.loads(row[3]) if row[3] else [],
                )
                pooled_pg.execute(
                    "UPDATE task_checkpoints SET resumed = TRUE WHERE task_id = %s",
                    (task_id,),
                )
                return cp
            except Exception as exc:
                logger.error(f"Failed to load Postgres checkpoint: {exc}")
                return None

        if self.mode == "sqlite":
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                try:
                    cursor.execute(
                        "SELECT task_id, step_index, state, step_log, created_at, resumed FROM checkpoints WHERE task_id = ?",
                        (task_id,),
                    )
                    row = cursor.fetchone()
                    has_log = True
                except sqlite3.OperationalError:
                    # legacy DB without step_log column
                    cursor.execute(
                        "SELECT task_id, step_index, state, created_at, resumed FROM checkpoints WHERE task_id = ?",
                        (task_id,),
                    )
                    row = cursor.fetchone()
                    has_log = False
                if not row:
                    conn.close()
                    return None

                step_log = json.loads(row[3]) if has_log and row[3] else []
                cp = Checkpoint(
                    task_id=row[0],
                    step_index=row[1],
                    state=json.loads(row[2]),
                    created_at=row[4] if has_log else row[3],
                    resumed=bool(row[5] if has_log else row[4]),
                    step_log=step_log,
                )
                cursor.execute("UPDATE checkpoints SET resumed = 1 WHERE task_id = ?", (task_id,))
                conn.commit()
                conn.close()
                return cp
            except Exception as exc:
                logger.error(f"Failed to load SQLite checkpoint: {exc}")
                return None

        if not self._db:
            return None
        try:
            doc_ref = self._db.collection(self.collection_name).document(task_id)
            doc = doc_ref.get()
            if not doc.exists:
                return None

            data = doc.to_dict()
            cp = Checkpoint(
                task_id=data["task_id"],
                step_index=data["step_index"],
                state=json.loads(data["state"]),
                created_at=data["created_at"],
                resumed=bool(data.get("resumed", False)),
                step_log=json.loads(data["step_log"]) if data.get("step_log") else [],
            )
            # Mark as resumed
            doc_ref.update({"resumed": True})
            return cp
        except Exception as exc:
            logger.error(f"Failed to load Firestore checkpoint: {exc}")
            return None

    def list_all(self) -> list[dict[str, Any]]:
        if self.mode == "pg":
            try:
                CheckpointManager._batcher.flush()
                rows = pooled_pg.query(
                    "SELECT task_id, step_index, created_at, resumed FROM task_checkpoints ORDER BY created_at DESC"
                )
                return [
                    {
                        "task_id": r[0],
                        "step_index": r[1],
                        "created_at": str(r[2]),
                        "resumed": bool(r[3]),
                    }
                    for r in rows
                ]
            except Exception as exc:
                logger.error(f"Failed to list Postgres checkpoints: {exc}")
                return []

        if self.mode == "sqlite":
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT task_id, step_index, created_at, resumed FROM checkpoints ORDER BY created_at DESC"
                )
                rows = cursor.fetchall()
                conn.close()
                return [
                    {
                        "task_id": r[0],
                        "step_index": r[1],
                        "created_at": r[2],
                        "resumed": bool(r[3]),
                    }
                    for r in rows
                ]
            except Exception as exc:
                logger.error(f"Failed to list SQLite checkpoints: {exc}")
                return []

        if not self._db:
            return []
        try:
            docs = (
                self._db.collection(self.collection_name)
                .order_by("created_at", direction=firestore.Query.DESCENDING)
                .stream()
            )
            return [
                {
                    "task_id": d.id,
                    "step_index": d.to_dict().get("step_index"),
                    "created_at": d.to_dict().get("created_at"),
                    "resumed": bool(d.to_dict().get("resumed", False)),
                }
                for d in docs
            ]
        except Exception as exc:
            logger.error(f"Failed to list Firestore checkpoints: {exc}")
            return []

    # ── Event-sourced step replay (Tree-sitter/Durable-execution enhancement) ──
    def log_step(self, task_id: str, step: dict[str, Any], step_index: int | None = None) -> bool:
        """Append one event-sourced step to the task's step_log and bump step_index.

        বাংলা মন্তব্য: প্রতিটি স্টেপের ইনপুট/আউটপুট এখানে সেভ হয়, যাতে ক্র্যাশের পর
        ঠিক যে স্টেপে আটকেছিল সেখান থেকে resume করা যায় (Zero Redundant Work)।
        """
        cp = self.load(task_id)
        state = cp.state if cp else {}
        log = list(cp.step_log) if cp else []
        idx = step_index if step_index is not None else (cp.step_index if cp else 0)
        entry = dict(step)
        entry.setdefault("index", idx)
        log.append(entry)
        return self.save(task_id, idx, state, step_log=log)

    def get_step_log(self, task_id: str) -> list[dict[str, Any]]:
        """Return the event-sourced step log for a task (empty if none)."""
        cp = self.load(task_id)
        return list(cp.step_log) if cp else []

    def replay_from(
        self, task_id: str, from_index: int
    ) -> tuple[dict[str, Any], list[dict[str, Any]]] | None:
        """Return (state, pending_steps) where pending_steps have index >= from_index.

        Caller replays only the pending steps instead of re-running the whole task.
        """
        cp = self.load(task_id)
        if cp is None:
            return None
        pending = [s for s in cp.step_log if s.get("index", 0) >= from_index]
        return cp.state, pending

    def resume_interrupted_tasks(self) -> list[str]:
        """Crash-recovery hook: task_ids with a checkpoint that were never resumed."""
        return [c["task_id"] for c in self.list_all() if not c.get("resumed")]

    def clear(self, task_id: str) -> bool:
        if self.mode == "pg":
            try:
                CheckpointManager._batcher.flush()
                pooled_pg.execute("DELETE FROM task_checkpoints WHERE task_id = %s", (task_id,))
                return True
            except Exception as exc:
                logger.error(f"Failed to clear Postgres checkpoint: {exc}")
                return False

        if self.mode == "sqlite":
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM checkpoints WHERE task_id = ?", (task_id,))
                conn.commit()
                conn.close()
                return True
            except Exception as exc:
                logger.error(f"Failed to clear SQLite checkpoint: {exc}")
                return False

        if not self._db:
            return False
        try:
            self._db.collection(self.collection_name).document(task_id).delete()
            return True
        except Exception as exc:
            logger.error(f"Failed to clear Firestore checkpoint: {exc}")
            return False
