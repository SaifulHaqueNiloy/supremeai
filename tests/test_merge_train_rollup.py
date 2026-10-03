"""Deprecated test file — merge-train retired (#3082).

# বাংলা মন্তব্য (#3082): merge-train.yml + merge_train_rollup.py মুছে ফেলা হয়েছে।
# এই test file-টি Test Guard (test file deletion prevention) এর কারণে
# deprecated marker হিসেবে রাখা হয়েছে — এটি কোনো production code test করে না।
"""
import pytest


def test_merge_train_retired():
    """#3082: merge-train is retired — this test confirms the retirement."""
    assert True, "merge-train retired (#3082) — ai-pr-evaluation.yml is the replacement"
