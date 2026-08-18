"""Chaos/persistence tests for CheckpointManager step-granular replay."""

from __future__ import annotations

import os
import tempfile

from tools.checkpoint_manager import CheckpointManager


def _tmp_db() -> str:
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    return path


def test_log_step_and_replay_from():
    path = _tmp_db()
    try:
        mgr = CheckpointManager(db_path=path)
        assert mgr.save("t1", 0, {"x": 1})
        assert mgr.log_step("t1", {"action": "fetch", "out": "ok"}, step_index=1)
        assert mgr.log_step("t1", {"action": "parse", "out": "ok"}, step_index=2)
        assert mgr.log_step("t1", {"action": "write", "out": "ok"}, step_index=3)

        log = mgr.get_step_log("t1")
        assert [s["action"] for s in log] == ["fetch", "parse", "write"]

        # Resume from step 2 -> only parse + write remain pending
        result = mgr.replay_from("t1", 2)
        assert result is not None
        state, pending = result
        assert state == {"x": 1}
        assert [s["action"] for s in pending] == ["parse", "write"]
    finally:
        os.remove(path)


def test_step_log_survives_crash_new_instance():
    path = _tmp_db()
    try:
        # "Crash": first instance logs steps then is dropped
        m1 = CheckpointManager(db_path=path)
        m1.log_step("taskA", {"action": "a"}, step_index=1)
        m1.log_step("taskA", {"action": "b"}, step_index=2)
        del m1

        # New instance boots and must see the persisted step log
        m2 = CheckpointManager(db_path=path)
        log = m2.get_step_log("taskA")
        assert len(log) == 2
        assert log[1]["action"] == "b"

        # Resume from step 2 on the recovered instance
        state, pending = m2.replay_from("taskA", 2)
        assert [s["action"] for s in pending] == ["b"]
    finally:
        os.remove(path)


def test_legacy_db_without_step_log_column_still_loads():
    path = _tmp_db()
    try:
        import sqlite3

        # Create an old-style schema (no step_log column) and a row
        conn = sqlite3.connect(path)
        conn.execute(
            "CREATE TABLE checkpoints (task_id TEXT PRIMARY KEY, step_index INTEGER, state TEXT, created_at TEXT, resumed INTEGER DEFAULT 0)"
        )
        conn.execute(
            "INSERT INTO checkpoints VALUES (?,?,?,?,?)",
            ("leg", 0, '{"k": 1}', "2026-01-01T00:00:00+00:00", 0),
        )
        conn.commit()
        conn.close()

        mgr = CheckpointManager(db_path=path)
        cp = mgr.load("leg")
        assert cp is not None
        assert cp.state == {"k": 1}
        # step_log gracefully defaults to empty
        assert mgr.get_step_log("leg") == []
        # and we can still append a step (column auto-added)
        assert mgr.log_step("leg", {"action": "x"}, step_index=1)
        assert len(mgr.get_step_log("leg")) == 1
    finally:
        os.remove(path)
