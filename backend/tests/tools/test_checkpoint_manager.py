"""Tests for tools/checkpoint_manager.py — Execution checkpoint management."""
import pytest
from unittest.mock import MagicMock
from tools.checkpoint_manager import CheckpointManager


class TestCheckpointManager:
    """Checkpoint: save, load, list, delete."""

    def test_init(self):
        mgr = CheckpointManager()
        assert mgr is not None

    def test_save_checkpoint(self):
        mgr = CheckpointManager()
        result = mgr.save("task-1", {"step": 1, "data": "test"})
        assert result is not None

    def test_load_checkpoint(self):
        mgr = CheckpointManager()
        mgr.save("task-1", {"step": 1, "data": "test"})
        loaded = mgr.load("task-1")
        assert loaded is not None
        assert loaded.get("step") == 1

    def test_load_nonexistent_checkpoint(self):
        mgr = CheckpointManager()
        loaded = mgr.load("nonexistent-task")
        assert loaded is None

    def test_list_checkpoints(self):
        mgr = CheckpointManager()
        mgr.save("task-1", {"step": 1})
        mgr.save("task-2", {"step": 2})
        listing = mgr.list()
        assert isinstance(listing, (list, dict))
        assert len(listing) >= 2

    def test_delete_checkpoint(self):
        mgr = CheckpointManager()
        mgr.save("task-1", {"step": 1})
        mgr.delete("task-1")
        assert mgr.load("task-1") is None

    def test_delete_nonexistent_silent(self):
        mgr = CheckpointManager()
        # Should not raise
        mgr.delete("nonexistent")

    def test_checkpoint_overwrite(self):
        mgr = CheckpointManager()
        mgr.save("task-1", {"step": 1})
        mgr.save("task-1", {"step": 2})
        loaded = mgr.load("task-1")
        assert loaded.get("step") == 2
