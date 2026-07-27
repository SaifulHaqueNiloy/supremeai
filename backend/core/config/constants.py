"""
Constants Module for SupremeAI 2.0
==================================
Centralized constants eliminating all magic numbers across the codebase.

বাংলা: সব ম্যাজিক নম্বর নির্মূল করার জন্য কেন্দ্রীভূত কনস্ট্যান্টস মডিউল।
Timeout, Rate Limit, Cache TTL, Database, Security — সব কনফিগারেশন এখানে।
"""

from typing import Final


class TimeoutConfig:
    """Timeout-related configuration constants."""
    REDIS_TIMEOUT: Final[int] = 5
    DB_QUERY_TIMEOUT: Final[int] = 30
    LLM_RESPONSE_TIMEOUT: Final[int] = 120
    HTTP_REQUEST_TIMEOUT: Final[int] = 60
    WEBSOCKET_TIMEOUT: Final[int] = 300


class RateLimitConfig:
    """Rate limiting configuration constants."""
    FREE_TIER_RPM: Final[int] = 60
    PRO_TIER_RPM: Final[int] = 600
    ENTERPRISE_TIER_RPM: Final[int] = 6000
    BURST_MULTIPLIER: Final[int] = 3
    RATE_LIMIT_WINDOW: Final[int] = 60


class CacheConfig:
    """Cache-related configuration constants."""
    REDIS_CACHE_TTL: Final[int] = 300       # 5 minutes
    LOCAL_CACHE_TTL: Final[int] = 30        # 30 seconds
    SESSION_CACHE_TTL: Final[int] = 3600    # 1 hour
    CONFIG_CACHE_TTL: Final[int] = 60       # 1 minute
    L1_CACHE_MAX_SIZE: Final[int] = 1000
    L2_CACHE_MAX_SIZE: Final[int] = 10000


class DatabaseConstants:
    """Database configuration constants."""
    ADMIN_POOL_SIZE: Final[int] = 1
    ADMIN_POOL_OVERFLOW: Final[int] = 2
    USER_POOL_SIZE: Final[int] = 2
    USER_POOL_OVERFLOW: Final[int] = 13
    POOL_TIMEOUT: Final[int] = 30
    POOL_RECYCLE: Final[int] = 1800          # 30 minutes


class SecurityConstants:
    """Security-related configuration constants."""
    JWT_EXPIRE_MINUTES: Final[int] = 10080   # 7 days
    OTP_LENGTH: Final[int] = 10
    OTP_EXPIRATION: Final[int] = 300         # 5 minutes
    PASSWORD_MIN_LENGTH: Final[int] = 12
    MAX_LOGIN_ATTEMPTS: Final[int] = 5
    ACCOUNT_LOCKOUT_DURATION: Final[int] = 900  # 15 minutes


class MemoryConstants:
    """Memory management configuration constants."""
    LRU_CACHE_MAX_SIZE: Final[int] = 1000
    LFU_CACHE_MAX_SIZE: Final[int] = 1000
    WEAK_CACHE_TTL: Final[int] = 300         # 5 minutes
    OBJECT_POOL_DEFAULT_SIZE: Final[int] = 10
    MEMORY_PROFILING_INTERVAL: Final[int] = 30


class AgentConstants:
    """Agent-related configuration constants."""
    AGENT_SESSION_TIMEOUT: Final[int] = 3600       # 1 hour
    AGENT_EXECUTION_TIMEOUT: Final[int] = 1800     # 30 minutes
    AGENT_HEARTBEAT_INTERVAL: Final[int] = 30      # 30 seconds
    AGENT_SELF_HEALING_RETRIES: Final[int] = 5
    CIRCUIT_BREAKER_FAILURE_THRESHOLD: Final[int] = 5
    CIRCUIT_BREAKER_COOLDOWN: Final[int] = 300     # 5 minutes


# Pagination defaults
DEFAULT_PAGE_SIZE: Final[int] = 20
MAX_PAGE_SIZE: Final[int] = 100

# Performance thresholds
SLOW_QUERY_THRESHOLD_MS: Final[float] = 1000.0    # 1 second
HIGH_MEMORY_USAGE_THRESHOLD: Final[float] = 80.0  # 80%
HIGH_CPU_USAGE_THRESHOLD: Final[float] = 80.0     # 80%

# Batch processing
BATCH_SIZE_DEFAULT: Final[int] = 100
BATCH_SIZE_LARGE: Final[int] = 1000


__all__ = [
    "TimeoutConfig",
    "RateLimitConfig",
    "CacheConfig",
    "DatabaseConstants",
    "SecurityConstants",
    "MemoryConstants",
    "AgentConstants",
    "DEFAULT_PAGE_SIZE",
    "MAX_PAGE_SIZE",
    "SLOW_QUERY_THRESHOLD_MS",
    "HIGH_MEMORY_USAGE_THRESHOLD",
    "HIGH_CPU_USAGE_THRESHOLD",
    "BATCH_SIZE_DEFAULT",
    "BATCH_SIZE_LARGE",
]
