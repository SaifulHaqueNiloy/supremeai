"""
adaptive_engine/__init__.py
===========================
SupremeAI 2.0 — Adaptive Engine Package Initialization

বাংলা মন্তব্য: অ্যাডাপ্টিভ ইঞ্জিন প্যাকেজ — স্বয়ংক্রিয় শেখা, প্ল্যাটফর্ম
অ্যাডাপ্টেশন, এবং অভিজ্ঞতা ভিত্তিক উন্নয়ন মডিউল।
"""

from __future__ import annotations

from typing import Any

from adaptive_engine.experience_db import Experience, ExperienceDatabase
from adaptive_engine.intent_parser import IntentParser
from adaptive_engine.learning_loop import LearningLoop
from adaptive_engine.platform_learner import PlatformLearner, PlatformProfile
from adaptive_engine.registry import PlatformRegistry

# VERIFY FIX: removed broken imports of LearningCycleResult, LearningInsight,
# create_learning_loop — these were defined in the OLD learning_loop.py before
# Phase 2 Learning Consolidation refactored it to delegate to core.unified_learning.
# Keeping them in __all__ would cause ImportError at package import time, which
# blocks ExperienceDatabase and all auto-learning from working.
# Callers needing these should import from core.unified_learning directly.

__all__ = [
    "Experience",
    "ExperienceDatabase",
    "IntentParser",
    "LearningLoop",
    "PlatformLearner",
    "PlatformProfile",
    "PlatformRegistry",
]

# Version tracking for adaptive engine components
__version__ = "2.0.0"
__engine_build__ = "2026.07.20"


def get_engine_info() -> dict[str, Any]:
    """Return adaptive engine metadata."""
    return {
        "version": __version__,
        "build": __engine_build__,
        "components": sorted(__all__),
    }
