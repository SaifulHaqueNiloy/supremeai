"""
IDE Trio Pipeline
A multi-agent code generation and review pipeline consisting of:
1. GeminiWriter (Stage 1)
2. KiloReviewer (Stage 2)
3. ClineChecker (Stage 3)
"""

try:
    from .cline_checker import ClineChecker
except ImportError:
    ClineChecker = None

try:
    from .gemini_writer import GeminiWriter
except ImportError:
    GeminiWriter = None

try:
    from .kilo_reviewer import KiloReviewer, ReviewResult, ReviewSeverity
except ImportError:
    KiloReviewer = None
    ReviewResult = None
    ReviewSeverity = None

__all__ = [
    "GeminiWriter",
    "KiloReviewer",
    "ReviewResult",
    "ReviewSeverity",
    "ClineChecker",
]
