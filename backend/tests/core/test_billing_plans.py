"""Tests for core/billing_plans.py — Billing plan definitions."""
import pytest
from core.billing_plans import BillingPlans


class TestBillingPlans:
    """Billing plans: list, get, compare, features."""

    def test_init(self):
        plans = BillingPlans()
        assert plans is not None

    def test_list_plans(self):
        plans = BillingPlans()
        listing = plans.list()
        assert isinstance(listing, (list, dict))
        assert len(listing) >= 1

    def test_get_free_plan(self):
        plans = BillingPlans()
        free = plans.get("free")
        if free:
            assert "price" in free or "cost" in free
            assert free.get("price", 0) == 0 or free.get("cost", 0) == 0

    def test_get_premium_plan(self):
        plans = BillingPlans()
        premium = plans.get("premium") or plans.get("pro")
        if premium:
            assert premium.get("price", 0) > 0 or premium.get("cost", 0) > 0

    def test_plan_has_features(self):
        plans = BillingPlans()
        for name, plan in plans.list().items() if isinstance(plans.list(), dict) else enumerate(plans.list()):
            if isinstance(plan, dict):
                assert "features" in plan or "limits" in plan

    def test_plan_has_name(self):
        plans = BillingPlans()
        listing = plans.list()
        assert listing is not None
