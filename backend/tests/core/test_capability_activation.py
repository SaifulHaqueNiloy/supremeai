"""Tests for core/capability_activation.py — Capability activation flow."""
import pytest
from core.capability_activation import CapabilityActivator


class TestCapabilityActivator:
    """Capability activator: activate, deactivate, status."""

    def test_init(self):
        act = CapabilityActivator()
        assert act is not None

    def test_activate_capability(self):
        act = CapabilityActivator()
        result = act.activate("browser_automation")
        assert result is not None
        assert isinstance(result, (bool, dict))

    def test_deactivate_capability(self):
        act = CapabilityActivator()
        act.activate("browser_automation")
        result = act.deactivate("browser_automation")
        assert result is not None

    def test_is_active(self):
        act = CapabilityActivator()
        act.activate("browser_automation")
        assert act.is_active("browser_automation") is True

    def test_is_active_nonexistent(self):
        act = CapabilityActivator()
        assert act.is_active("nonexistent") is False

    def test_list_active(self):
        act = CapabilityActivator()
        act.activate("cap-1")
        act.activate("cap-2")
        active = act.list_active()
        assert isinstance(active, list)
        assert len(active) >= 2
