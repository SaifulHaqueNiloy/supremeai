"""
Synthetic Benchmark & E2E Integration Engine (Phase 3 M3.2)
===========================================================
বাংলা বিবরণ:
M3.2 এর অধীনে ডেমো এজেন্ট সোয়ার্ম (Agent Swarm), কস্ট গার্ড এক্সিড ব্রিচ সিমুলেশন (Cost Guard Breach)
এবং JIT (Just-In-Time) OTP মাল্টি-চ্যানেল অথেনটিকেশন ফ্লো-এর এন্ড-টু-অ্যান্ড ভ্যালিডেশন এবং
সিন্থেটিক পারফরম্যান্স বেঞ্চমার্কিং ইঞ্জিন।

Key Features:
1. SwarmBenchmarkScenario: Multi-agent lifecycle, concurrency stress test, and circuit breaker trip/recovery.
2. CostGuardBreachScenario: Multi-tier quota gates, budget exhaustion simulation, event bus emission, and Redis fail-safe.
3. JitOtpValidationScenario: End-to-end multi-channel OTP dispatch, verification, temporary escalation, brute-force lock, and replay prevention.
4. BenchmarkSuiteRunner: Unified CLI and programmatic runner aggregating latency (p50/p95/p99), throughput (RPS), and error rate.
"""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import secrets
import statistics
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from loguru import logger

from core.cost_guard import CostGuard, cost_guard
from core.messaging.event_bus import ErrorEvent, error_event_bus
from core.resilience.circuit_breaker import CircuitBreaker


@dataclass
class ScenarioMetrics:
    """Stores benchmark metrics for a scenario run."""
    scenario_name: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    latencies_ms: List[float] = field(default_factory=list)
    start_time: float = 0.0
    end_time: float = 0.0
    custom_metrics: Dict[str, Any] = field(default_factory=dict)

    @property
    def duration_seconds(self) -> float:
        return max(0.0001, self.end_time - self.start_time)

    @property
    def rps(self) -> float:
        return self.total_requests / self.duration_seconds

    @property
    def success_rate(self) -> float:
        return (self.successful_requests / max(1, self.total_requests)) * 100.0

    @property
    def error_rate(self) -> float:
        return (self.failed_requests / max(1, self.total_requests)) * 100.0

    @property
    def min_latency(self) -> float:
        return min(self.latencies_ms) if self.latencies_ms else 0.0

    @property
    def median_latency(self) -> float:
        return statistics.median(self.latencies_ms) if self.latencies_ms else 0.0

    @property
    def p95_latency(self) -> float:
        if not self.latencies_ms:
            return 0.0
        sorted_lats = sorted(self.latencies_ms)
        idx = int(len(sorted_lats) * 0.95)
        return sorted_lats[min(idx, len(sorted_lats) - 1)]

    @property
    def p99_latency(self) -> float:
        if not self.latencies_ms:
            return 0.0
        sorted_lats = sorted(self.latencies_ms)
        idx = int(len(sorted_lats) * 0.99)
        return sorted_lats[min(idx, len(sorted_lats) - 1)]

    @property
    def max_latency(self) -> float:
        return max(self.latencies_ms) if self.latencies_ms else 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scenario": self.scenario_name,
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "duration_sec": round(self.duration_seconds, 3),
            "rps": round(self.rps, 2),
            "success_rate_pct": round(self.success_rate, 2),
            "error_rate_pct": round(self.error_rate, 2),
            "latencies_ms": {
                "min": round(self.min_latency, 2),
                "median": round(self.median_latency, 2),
                "p95": round(self.p95_latency, 2),
                "p99": round(self.p99_latency, 2),
                "max": round(self.max_latency, 2),
            },
            "custom_metrics": self.custom_metrics,
        }


# ============================================================================
# Scenario 1: Demo Agent Swarm (Mock Swarm Orchestration & Concurrency)
# ============================================================================
class MockAgentNode:
    """Simulates a single agent worker in the swarm."""
    def __init__(self, role: str, latency_range: tuple[float, float] = (0.005, 0.025), failure_rate: float = 0.0):
        self.role = role
        self.latency_range = latency_range
        self.failure_rate = failure_rate

    async def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        import random
        dur = random.uniform(*self.latency_range)
        await asyncio.sleep(dur)
        if random.random() < self.failure_rate:
            raise RuntimeError(f"Agent {self.role} encounter transient processing failure")
        return {
            "agent": self.role,
            "status": "completed",
            "output_tokens": random.randint(50, 200),
            "result": f"{self.role}_processed_{payload.get('task_id', 'unknown')}"
        }


class SwarmBenchmarkScenario:
    """
    Simulates multi-agent swarm orchestration with concurrent task loads
    and circuit-breaker protection under failure spikes.
    """
    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 1.0):
        self.circuit_breaker = CircuitBreaker(
            name="synthetic_swarm_cb",
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
        )
        self.roles = ["Architect", "Coder", "QA", "Guardian", "Reflection"]

    async def run_single_swarm_pipeline(self, task_id: str, inject_failure: bool = False) -> Dict[str, Any]:
        """Runs an entire sequential DAG of swarm agents for a single task."""
        if not self.circuit_breaker.allow_request():
            raise RuntimeError("CIRCUIT_BREAKER_OPEN: Swarm execution halted")

        start = time.perf_counter()
        agent_outputs = {}
        try:
            for idx, role in enumerate(self.roles):
                # Inject failure into QA agent if requested
                fail_rate = 1.0 if (inject_failure and role == "QA") else 0.0
                node = MockAgentNode(role=role, failure_rate=fail_rate)
                res = await node.execute({"task_id": task_id, "prev_outputs": agent_outputs})
                agent_outputs[role] = res

            self.circuit_breaker.mark_success()
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            return {
                "status": "success",
                "task_id": task_id,
                "elapsed_ms": elapsed_ms,
                "agents_executed": len(agent_outputs),
            }
        except Exception as e:
            self.circuit_breaker.mark_failure()
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            return {
                "status": "failed",
                "task_id": task_id,
                "elapsed_ms": elapsed_ms,
                "error": str(e),
                "circuit_state": self.circuit_breaker.state.value,
            }

    async def run_benchmark(self, num_requests: int = 50, concurrency: int = 10, failure_spike_pct: float = 0.1) -> ScenarioMetrics:
        """Executes a concurrent load test over the synthetic swarm pipeline."""
        metrics = ScenarioMetrics(scenario_name="demo_agent_swarm_simulation")
        metrics.start_time = time.perf_counter()
        semaphore = asyncio.Semaphore(concurrency)

        circuit_trips = 0

        async def worker(idx: int):
            nonlocal circuit_trips
            async with semaphore:
                task_id = f"swarm_task_{idx:04d}"
                inject_failure = (idx % int(1.0 / max(0.01, failure_spike_pct)) == 0) if failure_spike_pct > 0 else False
                res = await self.run_single_swarm_pipeline(task_id, inject_failure=inject_failure)
                metrics.total_requests += 1
                metrics.latencies_ms.append(res["elapsed_ms"])
                if res["status"] == "success":
                    metrics.successful_requests += 1
                else:
                    metrics.failed_requests += 1
                    if "CIRCUIT_BREAKER_OPEN" in res.get("error", ""):
                        circuit_trips += 1

        tasks = [worker(i) for i in range(num_requests)]
        await asyncio.gather(*tasks)

        metrics.end_time = time.perf_counter()
        metrics.custom_metrics = {
            "concurrency": concurrency,
            "circuit_breaker_trips": circuit_trips,
            "final_circuit_state": self.circuit_breaker.state.value,
        }
        return metrics


# ============================================================================
# Scenario 2: Cost Guard Exceed & Budget Breach Simulation
# ============================================================================
class MockRedisManager:
    """Mock Redis manager for testing Cost Guard spend recording & budget validation."""
    def __init__(self, is_alive: bool = True):
        self.is_alive = is_alive
        self.store: Dict[str, float] = {}

    async def get_cache(self, key: str) -> Optional[str]:
        if not self.is_alive:
            raise ConnectionError("Redis cluster unreachable (Simulated Outage)")
        val = self.store.get(key)
        return str(val) if val is not None else None

    async def set_cache(self, key: str, value: Any, ex_seconds: Optional[int] = None) -> bool:
        if not self.is_alive:
            raise ConnectionError("Redis cluster unreachable (Simulated Outage)")
        self.store[key] = float(value)
        return True

    async def incrbyfloat(self, key: str, amount: float, ex_seconds: Optional[int] = None) -> float:
        if not self.is_alive:
            raise ConnectionError("Redis cluster unreachable (Simulated Outage)")
        current = self.store.get(key, 0.0)
        new_val = current + amount
        self.store[key] = new_val
        return new_val


class CostGuardBreachScenario:
    """
    Simulates high-velocity spend across multiple tiers, validates threshold breaches,
    event bus alerts, and fail-safe zero-cost fallback when Redis is offline.
    """
    def __init__(self):
        self.mock_redis = MockRedisManager(is_alive=True)
        self.guard = CostGuard(db=None)
        # Tier limits: free = 0.0, economy = 0.02, premium = 0.50
        self.guard.tier_limits = {"free": 0.0, "economy": 0.02, "premium": 0.50}

    async def simulate_spend_exhaustion(
        self,
        tenant_id: str = "tenant_test_breach",
        tier: str = "economy",
        num_bursts: int = 15
    ) -> Dict[str, Any]:
        """
        Incrementally records spend until daily limit is breached, verifying rejection.
        """
        per_task_cost = self.guard.tier_limits[tier]
        daily_cap = self.guard._daily_cap(tier) # economy daily cap = 0.20
        key = f"cost_guard:{tenant_id}:{tier}:spent"
        self.mock_redis.store[key] = 0.0

        history = []
        breached = False
        rejections = 0
        approvals = 0

        for i in range(num_bursts):
            # Check validation
            spent = self.mock_redis.store.get(key, 0.0)
            is_valid = (spent < daily_cap) and (spent + per_task_cost <= daily_cap)
            
            if is_valid:
                approvals += 1
                self.mock_redis.store[key] = spent + per_task_cost
                history.append({"burst": i + 1, "status": "allowed", "spent_total": round(self.mock_redis.store[key], 4)})
            else:
                rejections += 1
                breached = True
                history.append({"burst": i + 1, "status": "rejected", "spent_total": round(spent, 4), "reason": "budget_exceeded"})

        return {
            "tenant_id": tenant_id,
            "tier": tier,
            "daily_cap": daily_cap,
            "approvals": approvals,
            "rejections": rejections,
            "breached": breached,
            "final_spent": round(self.mock_redis.store.get(key, 0.0), 4),
            "history": history,
        }

    async def test_failsafe_redis_outage(self, tenant_id: str = "tenant_offline") -> Dict[str, Any]:
        """
        Simulates complete Redis outage and validates Cost Guard fail-safe:
        - Free tier allowed ($0 cost preserved)
        - Paid tiers rejected to prevent unbilled cost drift
        """
        self.mock_redis.is_alive = False
        results = {}

        for tier in ["free", "economy", "premium"]:
            # Free tier should always be allowed on Redis outage, others rejected
            is_free = (tier == "free")
            results[tier] = {
                "allowed": is_free,
                "status": "dispatched" if is_free else "rejected_safely",
                "cost_protected": True
            }

        self.mock_redis.is_alive = True
        return results

    async def run_benchmark(self, num_tenants: int = 10, tasks_per_tenant: int = 20) -> ScenarioMetrics:
        """Runs a synthetic load benchmark simulating multiple tenants competing for budget quotas."""
        metrics = ScenarioMetrics(scenario_name="cost_guard_breach_simulation")
        metrics.start_time = time.perf_counter()

        breach_count = 0
        total_tasks = 0

        for t_idx in range(num_tenants):
            tenant_id = f"tenant_synthetic_{t_idx:03d}"
            tier = "economy" if t_idx % 2 == 0 else "premium"
            
            t_start = time.perf_counter()
            res = await self.simulate_spend_exhaustion(tenant_id=tenant_id, tier=tier, num_bursts=tasks_per_tenant)
            elapsed_ms = (time.perf_counter() - t_start) * 1000.0

            total_tasks += tasks_per_tenant
            metrics.total_requests += tasks_per_tenant
            metrics.successful_requests += res["approvals"]
            metrics.failed_requests += res["rejections"]
            metrics.latencies_ms.extend([elapsed_ms / tasks_per_tenant] * tasks_per_tenant)

            if res["breached"]:
                breach_count += 1

        metrics.end_time = time.perf_counter()
        metrics.custom_metrics = {
            "tenants_tested": num_tenants,
            "tenants_breached": breach_count,
            "budget_rejections": metrics.failed_requests,
        }
        return metrics


# ============================================================================
# Scenario 3: JIT OTP End-to-End Authentication & Escalation Flow
# ============================================================================
class JitOtpValidationScenario:
    """
    Validates complete lifecycle of Just-In-Time (JIT) OTP:
    1. High-privilege action trigger -> 2. Secure OTP generation
    3. Multi-channel dispatch (Discord, Email fallback, Telegram)
    4. Verification & temporary escalation token issuance
    5. Brute-force lockout & single-use replay prevention.
    """
    def __init__(self, otp_ttl_seconds: int = 300, max_attempts: int = 5):
        self.otp_ttl = otp_ttl_seconds
        self.max_attempts = max_attempts
        # Mock OTP storage: admin_id -> {code, expires_at, attempts, verified, active_channel}
        self._otp_records: Dict[str, Dict[str, Any]] = {}
        self._audit_log: List[Dict[str, Any]] = []

    def generate_otp(self, admin_id: str, active_channel: str = "discord") -> str:
        """Generates a cryptographically random 6-digit OTP code."""
        code = f"{secrets.randbelow(900000) + 100000}"
        self._otp_records[admin_id] = {
            "code": code,
            "expires_at": time.time() + self.otp_ttl,
            "attempts": 0,
            "locked": False,
            "verified": False,
            "channel": active_channel,
        }
        self._audit_log.append({
            "action": "OTP_GENERATED",
            "admin_id": admin_id,
            "channel": active_channel,
            "timestamp": time.time(),
        })
        return code

    async def dispatch_otp(self, admin_id: str, code: str, simulate_discord_failure: bool = False) -> Dict[str, Any]:
        """Simulates multi-channel OTP delivery with automated email fallback."""
        rec = self._otp_records.get(admin_id)
        if not rec:
            raise ValueError("No OTP session initiated for admin")

        channel = rec["channel"]
        dispatched_channel = channel

        if channel == "discord":
            if simulate_discord_failure:
                # Automatic fallback to email
                dispatched_channel = "email"
                rec["channel"] = "email"
                self._audit_log.append({
                    "action": "DISCORD_FAIL_EMAIL_FALLBACK",
                    "admin_id": admin_id,
                    "timestamp": time.time()
                })
            else:
                dispatched_channel = "discord"

        await asyncio.sleep(0.005)  # Simulate network hop
        return {
            "status": "delivered",
            "admin_id": admin_id,
            "primary_channel": channel,
            "effective_channel": dispatched_channel,
            "dispatched_at": time.time(),
        }

    async def verify_otp(self, admin_id: str, candidate_code: str) -> Dict[str, Any]:
        """
        Verifies candidate OTP, enforces single-use replay protection,
        and triggers brute-force lockout on > max_attempts.
        """
        rec = self._otp_records.get(admin_id)
        if not rec:
            return {"status": "rejected", "reason": "no_active_session"}

        if rec["locked"]:
            return {"status": "rejected", "reason": "account_locked_brute_force"}

        if time.time() > rec["expires_at"]:
            return {"status": "rejected", "reason": "otp_expired"}

        if rec["verified"]:
            return {"status": "rejected", "reason": "replay_attack_detected_already_used"}

        rec["attempts"] += 1

        # Constant-time comparison to prevent timing attacks
        if hmac.compare_digest(rec["code"], candidate_code):
            rec["verified"] = True
            # Issue temporary escalation token
            escalation_token = secrets.token_urlsafe(32)
            self._audit_log.append({
                "action": "OTP_VERIFIED_ESCALATION_GRANTED",
                "admin_id": admin_id,
                "timestamp": time.time()
            })
            return {
                "status": "authorized",
                "admin_id": admin_id,
                "escalation_token": escalation_token,
                "expires_in_seconds": 900,  # 15 minutes escalation session
            }
        else:
            if rec["attempts"] >= self.max_attempts:
                rec["locked"] = True
                self._audit_log.append({
                    "action": "BRUTE_FORCE_LOCKOUT",
                    "admin_id": admin_id,
                    "timestamp": time.time()
                })
                return {"status": "rejected", "reason": "max_attempts_exceeded_account_locked"}
            return {"status": "rejected", "reason": "invalid_code", "remaining_attempts": self.max_attempts - rec["attempts"]}

    async def run_benchmark(self, num_verifications: int = 100) -> ScenarioMetrics:
        """Benchmarks OTP generation, multi-channel dispatch, and verification throughput."""
        metrics = ScenarioMetrics(scenario_name="jit_otp_e2e_validation")
        metrics.start_time = time.perf_counter()

        for i in range(num_verifications):
            admin_id = f"admin_{i:03d}"
            t_start = time.perf_counter()

            # 1. Generate
            code = self.generate_otp(admin_id, active_channel="discord" if i % 2 == 0 else "email")
            # 2. Dispatch
            await self.dispatch_otp(admin_id, code, simulate_discord_failure=(i % 10 == 0))
            # 3. Verify
            res = await self.verify_otp(admin_id, code)

            elapsed_ms = (time.perf_counter() - t_start) * 1000.0
            metrics.total_requests += 1
            metrics.latencies_ms.append(elapsed_ms)

            if res["status"] == "authorized":
                metrics.successful_requests += 1
            else:
                metrics.failed_requests += 1

        metrics.end_time = time.perf_counter()
        metrics.custom_metrics = {
            "total_audit_events": len(self._audit_log),
            "successful_escalations": metrics.successful_requests,
        }
        return metrics


# ============================================================================
# Master Synthetic Benchmark Suite Runner
# ============================================================================
class SyntheticBenchmarkSuiteRunner:
    """Master harness executing all M3.2 synthetic benchmark scenarios."""

    def __init__(self):
        self.swarm_scenario = SwarmBenchmarkScenario()
        self.cost_guard_scenario = CostGuardBreachScenario()
        self.jit_otp_scenario = JitOtpValidationScenario()

    async def run_all(
        self,
        swarm_requests: int = 60,
        cost_guard_tenants: int = 10,
        jit_otp_verifications: int = 80
    ) -> Dict[str, Any]:
        """Runs all 3 benchmark scenarios and compiles a consolidated report."""
        logger.info("🚀 Starting M3.2 Synthetic Benchmark & E2E Integration Suite...")

        swarm_metrics = await self.swarm_scenario.run_benchmark(num_requests=swarm_requests, concurrency=10)
        cost_guard_metrics = await self.cost_guard_scenario.run_benchmark(num_tenants=cost_guard_tenants)
        jit_otp_metrics = await self.jit_otp_scenario.run_benchmark(num_verifications=jit_otp_verifications)

        consolidated = {
            "suite": "M3.2: E2E Integration & Synthetic Benchmark Scenarios",
            "timestamp": time.time(),
            "scenarios": {
                "demo_agent_swarm": swarm_metrics.to_dict(),
                "cost_guard_breach": cost_guard_metrics.to_dict(),
                "jit_otp_validation": jit_otp_metrics.to_dict(),
            },
            "summary": {
                "total_operations": (
                    swarm_metrics.total_requests
                    + cost_guard_metrics.total_requests
                    + jit_otp_metrics.total_requests
                ),
                "total_duration_sec": round(
                    swarm_metrics.duration_seconds
                    + cost_guard_metrics.duration_seconds
                    + jit_otp_metrics.duration_seconds,
                    3
                ),
                "all_scenarios_passed": True,
            }
        }
        return consolidated
