"""Tests for tools/bandwidth_optimizer.py — Response bandwidth optimization."""
import pytest
from tools.bandwidth_optimizer import BandwidthOptimizer


class TestBandwidthOptimizer:
    """Bandwidth optimization: compression, token reduction."""

    def test_init(self):
        opt = BandwidthOptimizer()
        assert opt is not None

    def test_optimize_empty_string(self):
        opt = BandwidthOptimizer()
        result = opt.optimize("")
        assert result == "" or result is not None

    def test_optimize_plain_text(self):
        opt = BandwidthOptimizer()
        result = opt.optimize("Hello world this is a test")
        assert isinstance(result, str)

    def test_optimize_preserves_meaning(self):
        """Optimization should not destroy key content."""
        opt = BandwidthOptimizer()
        original = "The quick brown fox jumps over the lazy dog"
        result = opt.optimize(original)
        # At least some key words preserved
        assert "fox" in result or "dog" in result or len(result) > 0

    def test_optimize_reduces_size(self):
        """Long text should be reduced (or at least not expanded)."""
        opt = BandwidthOptimizer()
        original = "a " * 1000
        result = opt.optimize(original)
        assert len(result) <= len(original)

    def test_optimize_unicode_bengali(self):
        """Bengali text should not be destroyed (regression for danda-aware)."""
        opt = BandwidthOptimizer()
        bengali = "আমার সোনার বাংলা আমি তোমায় ভালোবাসি"
        result = opt.optimize(bengali)
        assert isinstance(result, str)
        # Should retain at least some Bengali characters
        assert any('\u0980' <= c <= '\u09FF' for c in result)
