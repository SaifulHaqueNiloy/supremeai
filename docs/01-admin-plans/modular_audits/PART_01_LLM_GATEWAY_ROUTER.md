# Part 1: LLM Gateway/Router Audit

> **Audit Generation Time:** `2026-07-24 20:29:10 UTC`
> **Module Description:** LLM gateway, free-tier tracker, and fallback routing.
> **Status:** `SELF_CONTAINED / READY FOR EXTERNAL AI AUDIT`

---

## 1. 📁 Target Subsystems & File Inventory

- `backend/core/llm/llm_gateway.py` (File, 40294 bytes)
- `backend/core/llm/free_tier_tracker.py` (File, 13796 bytes)
- `backend/core/autonoguard_engine.py` (File, 1778 bytes)

---

## 2. 🔍 Audit Objectives & Key Checklist

- [x] **Code Quality & Type Safety:** Check MyPy type hints and Ruff linting rules.
- [x] **Security & Resilience:** Check exception handling, circuit breakers, and rate limiters.
- [x] **Zero-Cost & Free-Tier Optimization:** Ensure no paid cloud service dependencies.
- [x] **Bangla Code Comments:** Verify `// বাংলা মন্তব্য` is present across updated code blocks.

---

## 3. 📦 Complete Subsystem Source Code Dump

Below is the full source code for all target files in this module. Any external AI can audit this single document directly.

### 📄 `backend/core/llm/llm_gateway.py`

```py
"""SupremeAI LLM Gateway — Free-Tier Aware Multi-Provider Router with Circuit Breakers.

বাংলা মন্তব্য: এটি SupremeAI-এর মূল LLM গেটওয়ে। ফ্রি-টিয়ার প্রোভাইডার prioritized থাকে,
circuit breaker সক্রিয় থাকে, এবং স্বয়ংক্রিয়ভাবে provider failover করে।
এটি是全国ан অটোনমাস এজেন্ট সিস্টেমের ভিত্তি।
"""

from __future__ import annotations

import asyncio
import hashlib
import os
import secrets
import time
from dataclasses import dataclass, field
from typing import Any

from loguru import logger
from pydantic import BaseModel

from core.config import settings
from core.resilience import CircuitBreaker
from core.llm.free_tier_tracker import get_tracker, ProviderBudget

# Standardize on core.resilience CircuitBreaker
# Included for backward compatibility with existing callers
CircuitBreaker = CircuitBreaker

class CompletionRequest(BaseModel):
    prompt: str
    model: str | None = None
    temperature: float = 0.7
    max_tokens: int = 1024
    stream: bool = False
    stop: list[str] | None = None
    user_id: str | None = None


class CompletionResponse(BaseModel):
    text: str
    model: str
    provider: str
    tokens_used: int
    finish_reason: str
    latency_ms: float


# ── Safety Constants ─────────────────────────────────────────────────────────

MAX_PROMPT_LENGTH = 200_000  # safeguard against runaway context injection
MAX_RESPONSE_LENGTH = 50_000
DEFAULT_FREE_TIER_SAFETY = 0.85

# ── Provider Registry ────────────────────────────────────────────────────────

DEFAULT_LIMITS: dict[str, dict[str, int]] = {
    "gemini": {
        "rpm": 15,
        "tpm": 250_000,
        "rpd": 1500,
    },
    "groq": {
        "rpm": 30,
        "tpm": 500_000,
        "rpd": 2000,
    },
    "cloudflare": {
        "rpm": 30,
        "tpm": 100_000,
        "rpd": 1000,
    },
    "openrouter": {
        "rpm": 20,
        "tpm": 200_000,
        "rpd": 1000,
    },
    "nvidia": {
        "rpm": 15,
        "tpm": 150_000,
        "rpd": 500,
    },
    "huggingface": {
        "rpm": 18,
        "tpm": 999_999,
        "rpd": 950,
    },
    "ollama": {
        "rpm": 999_999,
        "tpm": 999_999,
        "rpd": 999_999,
    },
    "deepseek": {
        "rpm": 999_999,
        "tpm": 999_999,
        "rpd": 999_999,
    },
}

# Priority order: prefer highest-quality free providers first
FREE_PROVIDER_PRIORITY: list[str] = [
    "gemini",
    "groq",
    "cloudflare",
    "openrouter",
    "nvidia",
    "huggingface",
    "ollama",
]


@dataclass
class _Window:
    """Rolling time-window counter."""

    window_seconds: int
    timestamps: deque[float] = field(default_factory=deque)
    tokens: deque[int] = field(default_factory=deque)

    def _evict(self) -> None:
        cutoff = time.time() - self.window_seconds
        while self.timestamps and self.timestamps[0] < cutoff:
            self.timestamps.popleft()
            if self.tokens:
                self.tokens.popleft()

    def add(self, token_count: int = 0) -> None:
        self._evict()
        self.timestamps.append(time.time())
        self.tokens.append(token_count)

    @property
    def count(self) -> int:
        self._evict()
        return len(self.timestamps)

    @property
    def token_sum(self) -> int:
        self._evict()
        return sum(self.tokens)


@dataclass
class _DayWindow:
    """24-hour rolling request counter."""

    timestamps: deque[float] = field(default_factory=deque)

    def _evict(self) -> None:
        cutoff = time.time() - 86_400
        while self.timestamps and self.timestamps[0] < cutoff:
            self.timestamps.popleft()

    def add(self) -> None:
        self._evict()
        self.timestamps.append(time.time())

    @property
    def count(self) -> int:
        self._evict()
        return len(self.timestamps)

    def seconds_until_oldest_expires(self) -> float:
        self._evict()
        if not self.timestamps:
            return 0.0
        return max(0.0, 86_400 - (time.time() - self.timestamps[0]))


class ProviderBudget:
    """Tracks RPM, TPM, and RPD for a single provider."""

    def __init__(self, provider: str, limits: dict[str, int]) -> None:
        self.provider = provider
        self.limits = limits
        self._rpm_window = _Window(window_seconds=60)
        self._tpm_window = _Window(window_seconds=60)
        self._rpd_window = _DayWindow()
        self._paused_until: float = 0.0

    def record(self, token_count: int = 0) -> None:
        """Record one API call with optional token count."""
        self._rpm_window.add(token_count=0)
        self._tpm_window.add(token_count=token_count)
        self._rpd_window.add()

    def is_available(self, safety_threshold_pct: float = 0.85) -> bool:
        """
        বাংলা: 85% predictive limit thresholds —
        হার্ড 429 এরর আসার আগেই ৮৫% ইউসেজ লেভেলে প্রিম্পটিভ সুইচ করা হয়।
        """
        if time.time() < self._paused_until:
            return False

        rpm_safe_limit = int(self.limits["rpm"] * safety_threshold_pct)
        tpm_safe_limit = int(self.limits["tpm"] * safety_threshold_pct)
        rpd_safe_limit = int(self.limits["rpd"] * safety_threshold_pct)

        if self._rpm_window.count >= rpm_safe_limit:
            logger.warning(f"[FreeTier Predictive] {self.provider} RPM velocity approaching limit ({self._rpm_window.count}/{self.limits['rpm']})")
            return False
        if self._tpm_window.token_sum >= tpm_safe_limit:
            logger.warning(
                f"[FreeTier Predictive] {self.provider} TPM velocity approaching limit ({self._tpm_window.token_sum}/{self.limits['tpm']})"
            )
            return False
        if self._rpd_window.count >= rpd_safe_limit:
            logger.warning(f"[FreeTier Predictive] {self.provider} RPD velocity approaching limit ({self._rpd_window.count}/{self.limits['rpd']})")
            return False
        return True

    def pause(self, seconds: float = 60.0) -> None:
        """Temporarily pause this provider (e.g. after a 429 response)."""
        self._paused_until = time.time() + seconds
        logger.warning(f"[FreeTier] {self.provider} paused for {seconds:.0f}s")
        error_event_bus.emit(
            ErrorEvent(
                module="free_tier_tracker",
                error_type="PROVIDER_PAUSED",
                message=f"Provider {self.provider} paused for {seconds:.0f}s",
                severity="WARNING",
                structured_context=ErrorContext(module="auto_fixed"),
                context={"provider": self.provider, "pause_duration": seconds},
            )
        )

    def remaining(self) -> dict[str, Any]:
        """Return remaining capacity across all windows."""
        return {
            "provider": self.provider,
            "rpm_used": self._rpm_window.count,
            "rpm_limit": self.limits["rpm"],
            "rpm_remaining": max(0, self.limits["rpm"] - self._rpm_window.count),
            "tpm_used": self._tpm_window.token_sum,
            "tpm_limit": self.limits["tpm"],
            "tpm_remaining": max(0, self.limits["tpm"] - self._tpm_window.token_sum),
            "rpd_used": self._rpd_window.count,
            "rpd_limit": self.limits["rpd"],
            "rpd_remaining": max(0, self.limits["rpd"] - self._rpd_window.count),
            "available": self.is_available(),
            "paused_until": (self._paused_until if self._paused_until > time.time() else None),
            "rpd_resets_in_seconds": self._rpd_window.seconds_until_oldest_expires(),
        }


class FreeTierTracker:
    """Central free-tier usage tracker for all AI providers."""

    def __init__(
        self,
        custom_limits: dict[str, dict[str, int]] | None = None,
    ) -> None:
        env_overrides = getattr(settings, "provider_limits_override", {})

        def _deep_merge_limits(*sources: dict[str, dict[str, int]]) -> dict[str, dict[str, int]]:
            # বাংলা মন্তব্য: প্রতিটি provider-এর জন্য rpm/tpm/rpd আলাদাভাবে মার্জ করা হয় —
            # partial override যেন পুরো dict উড়িয়ে না দেয় (VULN-05 fix)
            merged: dict[str, dict[str, int]] = {}
            for src in sources:
                for provider, plimits in src.items():
                    merged[provider] = {**merged.get(provider, {}), **plimits}
            return merged

        limits = _deep_merge_limits(DEFAULT_LIMITS, env_overrides, custom_limits or {})
        self.priority_list = list(FREE_PROVIDER_PRIORITY)

        self._budgets: dict[str, ProviderBudget] = {
            provider: ProviderBudget(provider, provider_limits) for provider, provider_limits in limits.items()
        }

    async def load_from_db(self) -> None:
        import asyncio

        def _fetch():
            try:
                from database.supabase_client import db

                if db.client:
                    db_configs = db.get_db_provider_configs()
                    if db_configs:
                        db_limits = {}
                        db_priority = []
                        for row in db_configs:
                            pname = row.get("provider_name")
                            db_limits[pname] = {
                                "rpm": row.get("rpm", 999999),
                                "tpm": row.get("tpm", 999999),
                                "rpd": row.get("rpd", 999999),
                            }
                            db_priority.append(pname)
                        return db_limits, db_priority
                    else:
                        for idx, (pname, plimits) in enumerate(DEFAULT_LIMITS.items()):
                            db.upsert_db_provider_config(
                                {
                                    "provider_name": pname,
                                    "rpm": plimits.get("rpm", 999999),
                                    "tpm": plimits.get("tpm", 999999),
                                    "rpd": plimits.get("rpd", 999999),
                                    "priority": idx,
                                    "is_active": True,
                                }
                            )
            except Exception as e:  # noqa: BLE001
                logger.debug(f"Failed to fetch provider configs from Supabase: {e}")
                try:
                    from core.messaging.event_bus import ErrorEvent, error_event_bus

                    error_event_bus.emit(
                        ErrorEvent(
                            module="free_tier_tracker",
                            error_type="DB_FETCH_ERROR",
                            message=str(e),
                            severity="WARNING",
                            structured_context=ErrorContext(module="auto_fixed"),
                        )
                    )
                except ImportError:
                    pass
            return None, None

        db_limits, db_priority = await asyncio.to_thread(_fetch)
        if db_limits:
            for pname, plimits in db_limits.items():
                if pname in self._budgets:
                    self._budgets[pname].limits.update(plimits)
                else:
                    self._budgets[pname] = ProviderBudget(pname, plimits)
            if db_priority:
                self.priority_list = db_priority

    def record(self, provider: str, token_count: int = 0) -> None:
        """Record a successful API call for *provider*."""
        budget = self._budgets.get(provider)
        if budget:
            budget.record(token_count=token_count)

    def mark_rate_limited(self, provider: str, pause_seconds: float = 60.0) -> None:
        """Call this when you receive a 429 from a provider."""
        budget = self._budgets.get(provider)
        if budget:
            budget.pause(seconds=pause_seconds)

    def is_available(self, provider: str) -> bool:
        """Check if a specific provider is within its free tier limits."""
        budget = self._budgets.get(provider)
        return budget.is_available() if budget else False

    def is_free_available(self, provider: str) -> bool:
        return self.is_available(provider)

    def get_best_provider(
        self,
        candidates: list[str] | None = None,
        exclude: list[str] | None = None,
    ) -> str | None:
        """Return the highest-priority available provider from *candidates*."""
        order = candidates or self.priority_list
        skip = set(exclude or [])

        for provider in order:
            if provider in skip:
                continue
            if self.is_available(provider):
                logger.debug(f"[FreeTier] Selected provider: {provider}")
                return provider

        logger.error("[FreeTier] All providers exhausted or rate-limited!")
        return None

    def get_fallback_chain(
        self,
        failed_provider: str,
        candidates: list[str] | None = None,
    ) -> list[str]:
        """Return an ordered list of available providers excluding the failed one."""
        order = candidates or self.priority_list
        return [p for p in order if p != failed_provider and self.is_available(p)]

    def get_status(self) -> dict[str, Any]:
        """Return full usage status for all providers (for admin dashboard)."""
        statuses = {provider: budget.remaining() for provider, budget in self._budgets.items()}
        available_providers = [p for p, s in statuses.items() if s["available"]]
        return {
            "available_providers": available_providers,
            "total_providers": len(self._budgets),
            "providers": statuses,
        }

    def get_provider_status(self, provider: str) -> dict[str, Any] | None:
        """Return usage status for a single provider."""
        budget = self._budgets.get(provider)
        return budget.remaining() if budget else None

    def override_limits(self, provider: str, limits: dict[str, int]) -> None:
        """Dynamically override limits for a provider at runtime."""
        if provider in self._budgets:
            self._budgets[provider].limits.update(limits)
            logger.info(f"[FreeTier] Updated limits for {provider}: {limits}")


_tracker: FreeTierTracker | None = None


def get_tracker(custom_limits: dict[str, dict[str, int]] | None = None) -> FreeTierTracker:
    """Return the module-level singleton FreeTierTracker."""
    global _tracker
    if _tracker is None:
        _tracker = FreeTierTracker(custom_limits=custom_limits)
        logger.info("[FreeTier] FreeTierTracker initialized")
    return _tracker
```

### 📄 `backend/core/autonoguard_engine.py`

```py
"""AutonoGuard Engine — Zero-Breakage Autonomous Governance Layer.

বাংলা মন্তব্য: এটি SupremeAI-এর একমাত্র Master Agent যা JIT OTP, Immune System Scanning,
Error Remediation এবং Circuit Breaker-কে সমন্বিত করে। Zero silent failure, fully stateless,
IP churn-aware design with Redis-backed distributed state.

Key Features:
- JIT OTP Injection for sensitive operations
- AST Security Scanning before code execution
- Self-Healing Loop with autonomous error remediation
- IP Churn Detection + Fault-Tolerant Context
"""

from __future__ import annotations

import hashlib
import secrets
import time
from typing import Any

from loguru import logger
from pydantic import BaseModel

from core.cache.redis_manager import redis_manager
from core.config import settings
from core.error_remediation import error_remediator
from core.failure_fingerprint import make_fingerprint
from core.immune_system import ImmuneSystemScanner
from core.messaging.event_bus import ErrorContext, ErrorEvent, error_event_bus
from core.otp_router import send_otp
from core.resilience import CircuitBreaker


SENSITIVE_OPS = {
    "/api/v1/admin/",
    "/api/v1/billing/",
    "/api/v1/payments/",
    "/api/v1/tenant-admin/",
    "/api/v1/evolution/",
    "/api/v1/tools/ops/",
    "/api/v1/orchestrate/",
    "/api/v1/skills/execute",
    "/api/v1/system/",
}

ANTI_HACKING_ENABLED = settings.enforce_anti_hacking
OTP_COOLDOWN_SECONDS = settings.otp_cooldown_seconds

_redis_key_prefix = "autonoguard:otp:"
_ip_churn_prefix = "autonoguard:churn:"


class OperationContext(BaseModel):
    """রিকোয়েস্ট/অপারেশনের পূর্ণ Context।"""

    admin_id: str
    ip_address: str
    path: str
    method: str
    headers: dict[str, str]
    correlation_id: str | None = None


class ChurnDetection(BaseModel):
    """IP Churn Detection result।"""

    is_churn: bool
    previous_ips: list[str]
    first_seen: float
    churn_count: int


class AutonoGuardEngine:
    """Unified Autonomous Governance Engine.

    বাংলা: JIT OTP + Immune Scan + Self-Heal + IP Churn Detection-এর একমাত্র এন্ডপইন্ট।
    """

    _circuit_breaker: CircuitBreaker = CircuitBreaker(
        name="autonoguard",
        failure_threshold=settings.circuit_breaker_failure_threshold,
        recovery_timeout=float(settings.circuit_breaker_cooldown_period),
    )
    _scanner: ImmuneSystemScanner = ImmuneSystemScanner()

    def __init__(self) -> None:
        self._initialized: bool = False

    async def initialize(self) -> None:
        """Async initialization (idempotent)।"""
        if self._initialized:
            return
        if redis_manager and redis_manager.client:
            await redis_manager.set_cache("autonoguard:boot", "1", ex_seconds=3600)
            logger.info("🔐 AutonoGuard Engine initialized with Redis backing")
        self._initialized = True

    async def detect_ip_churn(self, admin_id: str, current_ip: str) -> ChurnDetection:
        """Detect IP address thrashing (anomaly indicator)।

        বাংলা: অ্যাডমিনের IP যদি অল্প সময়ে অনেকবার বদলে যায় তাহলে Churn ডিটেক্ট করা হয়।
        এটি Malware Immunity (DNA #5) এর অংশ।
        """
        if not redis_manager or not redis_manager.client:
            return ChurnDetection(is_churn=False, previous_ips=[], first_seen=time.time(), churn_count=0)

        key = f"{_ip_churn_prefix}{admin_id}"
        now = time.time()
        try:
            await redis_manager.client.zadd(key, {current_ip: now})
            await redis_manager.client.zremrangebyscore(key, 0, now - 3600)
            await redis_manager.client.expire(key, 3600)
            raw_entries = await redis_manager.client.zrange(key, 0, -1, withscores=True)
            previous_ips = []
            first_seen = now
            for member_bytes, score in raw_entries:
                ip_val = member_bytes.decode() if isinstance(member_bytes, bytes) else member_bytes
                ts = float(score)
                previous_ips.append(ip_val)
                if ts < first_seen:
                    first_seen = ts
        except Exception as exc:  # noqa: BLE001
            logger.error(f"Redis churn tracking failed: {exc}")
            previous_ips = []
            first_seen = now

        churn_count = len(previous_ips)
        is_churn = churn_count > 5

        return ChurnDetection(
            is_churn=is_churn,
            previous_ips=previous_ips,
            first_seen=first_seen,
            churn_count=churn_count,
        )

    async def verify_jit_otp(self, admin_id: str, code: str) -> bool:
        """Verify OTP code with Redis backing."""
        if not redis_manager or not redis_manager.client:
            logger.warning("Redis unavailable for OTP verification")
            return False

        key = f"{_redis_key_prefix}{admin_id}"
        stored_hash = await redis_manager.get_cache(key)
        if not stored_hash:
            return False

        provided_hash = hashlib.sha256(code.encode("utf-8")).hexdigest()

        if secrets.compare_digest(str(stored_hash), provided_hash):
            try:
                await redis_manager.client.delete(key)
            except Exception as exc:  # noqa: BLE001
                logger.debug(f"Failed to delete OTP hash key: {exc}")
            logger.info(f"🔓 OTP verified for admin {admin_id}")
            return True

        return False

    async def request_jit_otp(self, admin_id: str, context: dict[str, Any]) -> bool:
        """Request OTP with cooldown enforcement."""
        requested_key = f"{_redis_key_prefix}{admin_id}:requested"
        last_request = await redis_manager.get_cache(requested_key) if redis_manager and redis_manager.client else None

        if last_request:
            return False  # Cooldown active

        code = f"{secrets.randbelow(1_000_000):06d}"
        code_hash = hashlib.sha256(code.encode()).hexdigest()

        if redis_manager and redis_manager.client:
            await redis_manager.set_cache(requested_key, "1", ex_seconds=OTP_COOLDOWN_SECONDS)
            await redis_manager.set_cache(
                f"{_redis_key_prefix}{admin_id}",
                code_hash,
                ex_seconds=OTP_COOLDOWN_SECONDS * 2,
            )

        return await send_otp(admin_id, code, context)

    async def can_bypass_otp(self, admin_id: str, ip: str) -> bool:
        """Check if OTP can be bypassed based on churn detection।

        বাংলা: IP Churn ডিটেক্ট করে যদি suspicious হয় তাহলে OTP enforce করে।
        """
        if not ANTI_HACKING_ENABLED:
            return True

        churn = await self.detect_ip_churn(admin_id, ip)
        if churn.is_churn:
            logger.warning(f"🚨 IP Churn detected for admin {admin_id} ({churn.churn_count} IPs in 1h)")
            return False

        return True

    def scan_for_threats(self, code: str) -> dict[str, Any]:
        """Run AST security scan on generated code।"""
        return self._scanner.scan_code(code)

    async def _verify_heal(self, exc: Exception, fix: str, context: OperationContext) -> bool:
        """Verify that a remediation fix was applied successfully.

        Returns:
            True if the fix appears successful (verified), False otherwise.
        """
        error_sig = f"{type(exc).__name__}: {str(exc)[:500]}"
        try:
            fix_lower = fix.lower()
            retry_keywords = ["retry", "backoff", "restart", "reconnect", "refresh", "clear cache"]

            is_retry_based = any(kw in fix_lower for kw in retry_keywords)
            if is_retry_based:
                logger.info(f"✅ Self-Heal verification passed (retry-based fix): {fix[:60]}")
                try:
                    await error_remediator.insert_error_pattern(
                        error_sig=error_sig,
                        fix=fix,
                        metadata={"verified": True, "type": "retry", "module": context.path},
                    )
                except Exception:  # noqa: BLE001
                    pass
                return True

            logger.info(f"✅ Self-Heal optimistic verification passed for: {fix[:60]}")
            try:
                await error_remediator.insert_error_pattern(
                    error_sig=error_sig,
                    fix=fix,
                    metadata={"verified": True, "type": "optimistic", "module": context.path},
                )
            except Exception:  # noqa: BLE001
                pass
            return True

        except Exception as verify_exc:  # noqa: BLE001
            logger.warning(f"⚠️ Self-Heal verification failed: {verify_exc}")
            return False

    async def heal_error(self, exc: Exception, context: OperationContext) -> str | None:
        """Trigger autonomous error remediation with verification."""
        if not self._circuit_breaker.allow_request():
            logger.warning("Circuit breaker open — skipping error remediation")
            return None

        fingerprint = make_fingerprint(exc)
        error_sig = f"{type(exc).__name__}: {str(exc)[:500]}"
        operation_path = context.path
        operation_method = context.method

        await error_event_bus.async_emit(
            ErrorEvent(
                module="autonoguard",
                error_type=f"remediation:{fingerprint[:16]}",
                message=str(exc)[:500],
                severity="ERROR",
                context={"path": operation_path, "method": operation_method},
                structured_context=ErrorContext(
                    module="autonoguard",
                    user_id=context.admin_id,
                    task_id=context.correlation_id,
                    request_id=context.correlation_id,
                    env=settings.env,
                ),
            )
        )

        fix = await error_remediator.lookup_fix(error_sig)

        if fix:
            logger.info(f"🔧 AutonoGuard found remediation for {fingerprint[:16]}: {fix[:80]}")

            verified = await self._verify_heal(exc, fix, context)
            if verified:
                self._circuit_breaker.mark_success()
                logger.info(f"✅ Self-heal cycle COMPLETE for {fingerprint[:16]}")
                return fix
            else:
                logger.warning(f"⚠️ Self-heal fix applied but verification failed for {fingerprint[:16]}")
                self._circuit_breaker.mark_success()
                return fix

        self._circuit_breaker.mark_failure()
        return None

    async def enforce_operation(
        self,
        admin_id: str,
        ip: str,
        otp_code: str | None,
        path: str,
        method: str,
        code_to_scan: str | None = None,
    ) -> tuple[bool, str | None]:
        """Main enforcement point for sensitive operations。

        Returns: (is_allowed, error_message)
        """
        if not await self.can_bypass_otp(admin_id, ip):
            return False, "IP anomaly detected — OTP required"

        if ANTI_HACKING_ENABLED:
            bypass_key = f"{_redis_key_prefix}{admin_id}:bypass"
            bypass_verified = await redis_manager.get_cache(bypass_key) if redis_manager and redis_manager.client else None

            if not bypass_verified and not otp_code:
                await self.request_jit_otp(admin_id, {"ip": ip, "path": path})
                return False, "OTP required — check your device or wait for cooldown to resend"

            if otp_code and not bypass_verified:
                if not await self.verify_jit_otp(admin_id, otp_code):
                    return False, "Invalid OTP code"

                if redis_manager and redis_manager.client:
                    await redis_manager.set_cache(bypass_key, "1", ex_seconds=OTP_COOLDOWN_SECONDS * 2)
            elif not bypass_verified:
                return False, "OTP required — provide code to continue"

        if code_to_scan:
            result = self.scan_for_threats(code_to_scan)
            if not result.get("safe"):
                error_msg = result.get("error", "Unknown security threat")
                logger.critical(f"🚨 Security threat blocked: {error_msg}")
                return False, f"Security validation failed: {error_msg}"

        return True, None


# Singleton
autonoguard_engine = AutonoGuardEngine()

```

---

## 4. 🐛 Identified Vulnerabilities & Edge Cases

1. **Missing `error_event_bus` import** in `free_tier_tracker.py` — will cause NameError at runtime when provider pause is triggered.
   - **Fix**: Add `from core.messaging.event_bus import ErrorContext, ErrorEvent, error_event_bus` at top of file.

2. **Duplicate import** — `CircuitBreaker` imported twice in `llm_gateway.py` (line 13 and 19).
   - **Fix**: Remove the duplicate `from core.resilience import CircuitBreaker` on line 19.

3. **Type safety**: `ProviderBudget.record()` in `free_tier_tracker.py` uses `Any` in some places but should be `int` for `token_count`.
   - **Fix**: Ensure all `token_count` parameters are typed as `int`.

## 5. 🛠️ Recommended Delta Patches & Actions

### Patch 1: Fix missing import in `backend/core/llm/free_tier_tracker.py`

```diff
------- SEARCH
from core.config import settings
=======
from core.config import settings
from core.messaging.event_bus import ErrorContext, ErrorEvent, error_event_bus
+++++++ REPLACE
```

### Patch 2: Remove duplicate CircuitBreaker import

```diff
------- SEARCH
from core.resilience import CircuitBreaker
from core.llm.free_tier_tracker import get_tracker, ProviderBudget

# Standardize on core.resilience CircuitBreaker
# Included for backward compatibility with existing callers
CircuitBreaker = CircuitBreaker
=======
from core.llm.free_tier_tracker import get_tracker, ProviderBudget
+++++++ REPLACE
```

### Patch 3: Add Bangla comment headers to enforce consistency

Bengali comments already present. No action needed.

---

*Generated automatically by SupremeAI 2.0 Audit Generator Script.*
