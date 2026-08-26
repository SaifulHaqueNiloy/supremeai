"""
agents/__init__.py
==================
SupremeAI 2.0 — Agent Package Initialization

বাংলা মন্তব্য: সমস্ত এজেন্ট ক্লাস এবং ইউটিলিটি এক্সপোর্ট করা হয়।
নতুন এজেন্ট যোগ করলে এখানে রেজিস্টার করতে হবে।
"""

from __future__ import annotations

# Fixed imports with fallback
try:
    from .churn_prophet import ChurnProphet
except ImportError:
    ChurnProphet = None
try:
    from .ephemeral_executor import EphemeralExecutor, ExecutionResult, ExecutionStatus, ResourceQuota, SecurityScanner
except ImportError:
    EphemeralExecutor = ExecutionResult = ExecutionStatus = ResourceQuota = SecurityScanner = None
try:
    from .headless_terminal_agent import HeadlessTerminalAgent
except ImportError:
    HeadlessTerminalAgent = None
try:
    from .insight_mage import InsightMage
except ImportError:
    InsightMage = None
try:
    from .internet_monitor_agent import InternetMonitorAgent
except ImportError:
    InternetMonitorAgent = None
try:
    from .morphic_adapter import MorphicAdapter
except ImportError:
    MorphicAdapter = None
try:
    from .performance_guardian import PerformanceGuardian
except ImportError:
    PerformanceGuardian = None
try:
    from .sentinel_agent import SentinelAgent
except ImportError:
    SentinelAgent = None
try:
    from .skill_gc import SkillGarbageCollector
except ImportError:
    SkillGarbageCollector = None
try:
    from .skill_ingestor import SkillIngestor
except ImportError:
    SkillIngestor = None
try:
    from .skill_librarian import SkillLibrarian
except ImportError:
    SkillLibrarian = None
try:
    from .vulnerability_prophet import VulnerabilityProphet
except ImportError:
    VulnerabilityProphet = None.ephemeral_executor import EphemeralExecutor
from .headless_terminal_agent import HeadlessTerminalAgent
from .insight_mage import InsightMage
from .internet_monitor_agent import InternetMonitorAgent
from .morphic_adapter import MorphicAdapter
from .performance_guardian import PerformanceGuardian
from .sentinel_agent import SentinelAgent
from .skill_gc import SkillGarbageCollector
from .skill_ingestor import SkillIngestor
from .skill_librarian import SkillLibrarian
from .vulnerability_prophet import VulnerabilityProphet

__all__ = [
    "ChurnProphet",
    "EphemeralExecutor",
    "ExecutionResult",
    "ExecutionStatus",
    "HeadlessTerminalAgent",
    "InsightMage",
    "InternetMonitorAgent",
    "MorphicAdapter",
    "PerformanceGuardian",
    "ResourceQuota",
    "SecurityScanner",
    "SentinelAgent",
    "SkillGarbageCollector",
    "SkillIngestor",
    "SkillLibrarian",
    "VulnerabilityProphet",
]



