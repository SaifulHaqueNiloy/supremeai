"""Regression tests for pending_tasks SQLite queue (M2.3 indexing)."""
import sqlite3
from pathlib import Path

import pytest

import models.pending_tasks as pt


@pytest.fixture
def temp_db_path(tmp_path: Path):
    """Isolate the pending_tasks DB to a temp file per test."""
    db_file = tmp_path / "pending_tasks_test.db"
    original = pt.DB_PATH
    pt.DB_PATH = db_file
    yield db_file
    pt.DB_PATH = original
    db_file.unlink(missing_ok=True)


def _index_names(db_file: Path) -> list[str]:
    conn = sqlite3.connect(db_file)
    try:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='pending_tasks'"
        ).fetchall()
        return [r[0] for r in rows]
    finally:
        conn.close()


def test_pending_tasks_indexes_created(temp_db_path: Path):
    """Queue hot-path columns (status, created_at) must be indexed."""
    # _get_conn() creates the table + indexes lazily on first access
    pt._get_conn().close()
    idx = _index_names(temp_db_path)
    assert "idx_pending_tasks_status" in idx
    assert "idx_pending_tasks_created_at" in idx


def test_pending_tasks_indexes_idempotent(temp_db_path: Path):
    """Repeated connection must not error on already-existing indexes."""
    pt._get_conn().close()
    pt._get_conn().close()  # second call — IF NOT EXISTS path
    idx = _index_names(temp_db_path)
    assert len([i for i in idx if i.startswith("idx_pending_tasks_")]) == 2


def test_pending_task_lifecycle_with_indexes(temp_db_path: Path):
    """Full create → list → update cycle still works with indexes present."""
    task = pt.create_pending_task(pt.TaskType.CODE_PUSH, {"demo": True})
    assert task.status == pt.TaskStatus.PENDING

    pending = pt.list_pending()
    assert any(t.task_id == task.task_id for t in pending)

    updated = pt.update_task_status(task.task_id, pt.TaskStatus.EXECUTED, "test_agent")
    assert updated is not None
    assert updated.status == pt.TaskStatus.EXECUTED

    # Executed tasks must no longer appear in the pending list
    remaining = pt.list_pending()
    assert all(t.task_id != task.task_id for t in remaining)
