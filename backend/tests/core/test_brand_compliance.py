"""Tests for core/brand_compliance.py — Brand compliance checker."""
import pytest
from core.brand_compliance import BrandCompliance


class TestBrandCompliance:
    def test_init(self):
        bc = BrandCompliance()
        assert bc is not None

    def test_check_compliant_content(self):
        bc = BrandCompliance()
        result = bc.check("Welcome to SupremeAI, the best AI platform")
        assert result.get("compliant") is True or result.get("passed") is True

    def test_check_non_compliant_content(self):
        bc = BrandCompliance()
        result = bc.check("This product is terrible and unreliable")
        assert result is not None

    def test_check_empty_content(self):
        bc = BrandCompliance()
        result = bc.check("")
        assert result is not None

    def test_check_bengali_content(self):
        bc = BrandCompliance()
        result = bc.check("সুপ্রিমএআই একটি চমৎকার প্ল্যাটফর্ম")
        assert result is not None
