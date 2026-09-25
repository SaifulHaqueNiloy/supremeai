"""Tests for tools/preference_memory.py — User preference storage."""
import pytest
from tools.preference_memory import PreferenceMemory


class TestPreferenceMemory:
    """Preference memory: set, get, delete, list."""

    def test_init(self):
        mem = PreferenceMemory()
        assert mem is not None

    def test_set_preference(self):
        mem = PreferenceMemory()
        mem.set("user-1", "theme", "dark")
        assert mem.get("user-1", "theme") == "dark"

    def test_get_nonexistent_preference(self):
        mem = PreferenceMemory()
        result = mem.get("user-1", "nonexistent")
        assert result is None

    def test_delete_preference(self):
        mem = PreferenceMemory()
        mem.set("user-1", "theme", "dark")
        mem.delete("user-1", "theme")
        assert mem.get("user-1", "theme") is None

    def test_list_user_preferences(self):
        mem = PreferenceMemory()
        mem.set("user-1", "theme", "dark")
        mem.set("user-1", "language", "bn")
        prefs = mem.list("user-1")
        assert isinstance(prefs, (dict, list))
        assert len(prefs) >= 2

    def test_preferences_isolated_per_user(self):
        mem = PreferenceMemory()
        mem.set("user-1", "theme", "dark")
        mem.set("user-2", "theme", "light")
        assert mem.get("user-1", "theme") == "dark"
        assert mem.get("user-2", "theme") == "light"

    def test_overwrite_preference(self):
        mem = PreferenceMemory()
        mem.set("user-1", "theme", "dark")
        mem.set("user-1", "theme", "light")
        assert mem.get("user-1", "theme") == "light"
