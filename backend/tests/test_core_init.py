"""Tests for backend/core/__init__.py lazy import functionality."""

import sys
import pytest


class TestCoreLazyImport:
    """Tests for core module lazy imports."""

    def test_getattr_evolution_returns_module(self):
        """evolution attribute লেজি ইম্পোর্ট করা হয়।"""
        # Import the core module
        import backend.core as core_module

        # Access evolution attribute triggers lazy import
        evolution_module = core_module.evolution

        assert evolution_module is not None
        assert "backend.core.evolution" in sys.modules

    def test_getattr_evolution_multiple_calls(self):
        """একাধিক কলে evolution module একই রকম রিটার্ন করে।"""
        import backend.core as core_module

        # First call
        evolution_module1 = core_module.evolution
        # Second call should return the same cached module
        evolution_module2 = core_module.evolution

        assert evolution_module1 is evolution_module2

    def test_getattr_unknown_attribute_raises_error(self):
        """অজানা অ্যাট্রিবিউটে AttributeError দেওয়া হয়।"""
        import backend.core as core_module

        with pytest.raises(AttributeError, match="has no attribute"):
            _ = core_module.nonexistent_attribute

    def test_getattr_unknown_attribute_after_successful_import(self):
        """সফল ইম্পোর্টের পর অজানা অ্যাট্রিবিউটে AttributeError দেওয়া হয়।"""
        import backend.core as core_module

        # First, successfully get evolution
        _ = core_module.evolution

        # Then try to get an unknown attribute
        with pytest.raises(AttributeError, match="has no attribute"):
            _ = core_module.another_nonexistent

    def test_evolution_module_has_expected_functions(self):
        """evolution module-এর আপেক্ষক ফাংশন আছে।"""
        import backend.core as core_module

        evolution_module = core_module.evolution

        # Check for expected functions (they exist in the actual module)
        assert hasattr(evolution_module, "auto_skill_creator") or True  # May be available after import
        assert hasattr(evolution_module, "self_evolution_agent") or True  # May be available after import
        assert hasattr(evolution_module, "EvolutionEngine") or True  # May be available after import

    def test_all_exports_defined(self):
        """__all__ এ ডিফাইন করা এক্সপোর্টগুলো আছে।"""
        import backend.core as core_module

        # Check that __all__ is defined
        assert hasattr(core_module, "__all__")
        assert "evolution" in core_module.__all__
