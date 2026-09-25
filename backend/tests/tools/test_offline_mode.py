"""Tests for tools/offline_mode.py — Offline capability fallback."""
import pytest
from tools.offline_mode import OfflineMode


class TestOfflineMode:
    """Offline mode: detection, fallback, queue."""

    def test_init(self):
        mode = OfflineMode()
        assert mode is not None

    def test_is_offline_default_false(self):
        mode = OfflineMode()
        assert mode.is_offline() is False

    def test_set_offline(self):
        mode = OfflineMode()
        mode.set_offline(True)
        assert mode.is_offline() is True

    def test_set_online(self):
        mode = OfflineMode()
        mode.set_offline(True)
        mode.set_offline(False)
        assert mode.is_offline() is False

    def test_queue_operation(self):
        """Operations queued when offline."""
        mode = OfflineMode()
        mode.set_offline(True)
        mode.queue("test_operation", {"param": 1})
        queued = mode.get_queue()
        assert len(queued) >= 1

    def test_clear_queue(self):
        mode = OfflineMode()
        mode.set_offline(True)
        mode.queue("op1", {})
        mode.queue("op2", {})
        mode.clear_queue()
        assert len(mode.get_queue()) == 0
