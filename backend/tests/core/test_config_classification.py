"""Tests for core/config_classification.py — Configuration classification."""
import pytest
from core.config_classification import ConfigClassifier


class TestConfigClassifier:
    def test_init(self):
        clf = ConfigClassifier()
        assert clf is not None

    def test_classify_secret(self):
        clf = ConfigClassifier()
        result = clf.classify("API_KEY", "sk-12345")
        assert result in ("secret", "sensitive", "credential") or result.get("type") in ("secret", "sensitive")

    def test_classify_public(self):
        clf = ConfigClassifier()
        result = clf.classify("APP_NAME", "SupremeAI")
        assert result in ("public", "non-sensitive") or result.get("type") in ("public", "non-sensitive")

    def test_classify_url(self):
        clf = ConfigClassifier()
        result = clf.classify("BACKEND_URL", "https://api.example.com")
        assert result is not None

    def test_classify_boolean(self):
        clf = ConfigClassifier()
        result = clf.classify("DEBUG", "true")
        assert result is not None

    def test_is_sensitive_key(self):
        clf = ConfigClassifier()
        assert clf.is_sensitive("PASSWORD") is True
        assert clf.is_sensitive("SECRET") is True
        assert clf.is_sensitive("API_KEY") is True
        assert clf.is_sensitive("APP_NAME") is False
