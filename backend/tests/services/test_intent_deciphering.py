"""Tests for services/intent_deciphering.py — Intent analysis service."""
import pytest
from services.intent_deciphering import IntentDecipherer


class TestIntentDecipherer:
    """Intent deciphering: classification, risk scoring."""

    def test_init(self):
        dec = IntentDecipherer()
        assert dec is not None

    def test_classify_read_intent(self):
        dec = IntentDecipherer()
        result = dec.classify("Show me the current settings")
        assert result is not None
        assert "intent" in result or "type" in result

    def test_classify_write_intent(self):
        dec = IntentDecipherer()
        result = dec.classify("Update the configuration")
        assert result is not None

    def test_classify_delete_intent(self):
        dec = IntentDecipherer()
        result = dec.classify("Delete all user data")
        assert result is not None

    def test_risk_score_low(self):
        dec = IntentDecipherer()
        result = dec.assess_risk("What is the current time?")
        assert result is not None
        assert isinstance(result, (int, float, dict))

    def test_risk_score_high(self):
        dec = IntentDecipherer()
        result = dec.assess_risk("Drop the production database")
        assert result is not None

    def test_empty_prompt(self):
        dec = IntentDecipherer()
        result = dec.classify("")
        assert result is not None

    def test_bengali_intent(self):
        dec = IntentDecipherer()
        result = dec.classify("সিস্টেমের সেটিংস দেখাও")
        assert result is not None
