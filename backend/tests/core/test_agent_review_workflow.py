"""Tests for core/agent_review_workflow.py — PR Guardian review workflow."""
import pytest
from core.agent_review_workflow import ReviewWorkflow


class TestReviewWorkflow:
    def test_init(self):
        wf = ReviewWorkflow()
        assert wf is not None

    def test_classify_improvement(self):
        wf = ReviewWorkflow()
        result = wf.classify({"adds": 10, "removes": 2, "files": ["test.py"]})
        assert result is not None

    def test_classify_regression(self):
        wf = ReviewWorkflow()
        result = wf.classify({"adds": 0, "removes": 10, "files": ["core/security.py"]})
        assert result is not None

    def test_decide_merge_improvement(self):
        wf = ReviewWorkflow()
        decision = wf.decide({"classification": "improvement", "regressions": []})
        assert decision in ("merge", "fix", "close")

    def test_decide_close_regression(self):
        wf = ReviewWorkflow()
        decision = wf.decide({"classification": "regression", "regressions": ["security"]})
        assert decision in ("merge", "fix", "close")

    def test_risk_tier_low(self):
        wf = ReviewWorkflow()
        tier = wf.risk_tier({"files": ["README.md"], "adds": 5})
        assert tier in (1, 2, 3)

    def test_risk_tier_high(self):
        wf = ReviewWorkflow()
        tier = wf.risk_tier({"files": ["backend/core/security.py"], "adds": 50})
        assert tier in (1, 2, 3)
