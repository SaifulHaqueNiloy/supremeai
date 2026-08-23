"""
IDE Trio Pipeline
A multi-agent code generation and review pipeline consisting of:
1. GeminiWriter (Stage 1)
2. KiloReviewer (Stage 2)
3. ClineChecker (Stage 3)
"""

from .cline_checker import ClineChecker
from .gemini_writer import GeminiWriter
from .kilo_reviewer import KiloReviewer, ReviewResult, ReviewSeverity

__all__ = [
    "GeminiWriter",
    "KiloReviewer",
    "ReviewResult",
    "ReviewSeverity",
    "ClineChecker",
]
