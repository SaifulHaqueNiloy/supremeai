"""
Tests for M3.2: E2E Integration & Synthetic Benchmark Scenarios
===============================================================
বাংলা: M3.2 এর অধীনে সোয়ার্ম পাইপলাইন, কস্ট গার্ড এক্সিড ব্রিচ সিমুলেশন
এবং JIT OTP ভ্যালিডেশন ফ্লো-এর পূর্ণাঙ্গ ইউনিট ও ইন্টিগ্রেশন টেস্ট স্যুট।
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from workers.synthetic_load_benchmark import (
    CostGuardBreachScenario,
    JitOtpValidationScenario,
    MockAgentNode,
    MockRedisManager,
    ScenarioMetrics,
    SwarmBenchmarkScenario,
    SyntheticBenchmarkSuiteRunner,
)


class TestSwarmBenchmarkScenario:
    """Tests for Scenario 1: Demo Agent Swarm & Concurrency Stress."""

    @pytest.mark.asyncio
    async def test_mock_agent_node_success(self):
        node = MockAgentNode(role="Architect", latency_range=(0.001, 0.002), failure_rate=0.0)
        res = await node.execute({"task_id": "task_1"})
        assert res["status"] == "completed"
        assert res["agent"] == "Architect"
        assert "task_1" in res["result"]

    @pytest.mark.asyncio
    async def test_mock_agent_node_injected_failure(self):
        node = MockAgentNode(role="QA", latency_range=(0.001, 0.002), failure_rate=1.0)
        with pytest.raises(RuntimeError, match="transient processing failure"):
            await node.execute({"task_id": "task_fail"})

    @pytest.mark.asyncio
    async def test_single_swarm_pipeline_execution(self):
        swarm = SwarmBenchmarkScenario(failure_threshold=5, recovery_timeout=1.0)
        res = await swarm.run_single_swarm_pipeline(task_id="test_dag_1", inject_failure=False)
        assert res["status"] == "success"
        assert res["task_id"] == "test_dag_1"
        assert res["agents_executed"] == 5
        assert res["elapsed_ms"] > 0

    @pytest.mark.asyncio
    async def test_circuit_breaker_trips_under_failures(self):
        swarm = SwarmBenchmarkScenario(failure_threshold=3, recovery_timeout=60.0)
        
        # Trigger 3 failures
        for i in range(3):
            res = await swarm.run_single_swarm_pipeline(task_id=f"fail_{i}", inject_failure=True)
            assert res["status"] == "failed"

        # 4th request must be blocked by circuit breaker
        with pytest.raises(RuntimeError, match="CIRCUIT_BREAKER_OPEN"):
            await swarm.run_single_swarm_pipeline(task_id="blocked_task", inject_failure=False)

    @pytest.mark.asyncio
    async def test_swarm_benchmark_load_runner(self):
        swarm = SwarmBenchmarkScenario(failure_threshold=20, recovery_timeout=0.1)
        metrics: ScenarioMetrics = await swarm.run_benchmark(num_requests=15, concurrency=5, failure_spike_pct=0.0)
        
        assert metrics.total_requests == 15
        assert metrics.successful_requests == 15
        assert metrics.failed_requests == 0
        assert metrics.success_rate == 100.0
        assert metrics.rps > 0
        assert metrics.min_latency > 0
        assert metrics.p95_latency >= metrics.min_latency


class TestCostGuardBreachScenario:
    """Tests for Scenario 2: Cost Guard Budget Breach & Quota Limits."""

    @pytest.mark.asyncio
    async def test_mock_redis_spend_accumulation(self):
        redis = MockRedisManager(is_alive=True)
        val = await redis.incrbyfloat("key1", 0.05)
        assert val == 0.05
        val2 = await redis.incrbyfloat("key1", 0.05)
        assert val2 == 0.10
        cached = await redis.get_cache("key1")
        assert float(cached) == 0.10

    @pytest.mark.asyncio
    async def test_spend_exhaustion_detection(self):
        scenario = CostGuardBreachScenario()
        # Economy tier: per task = 0.02, daily cap = 0.20
        # 15 requests * 0.02 = 0.30 -> should approve 10 and reject 5
        res = await scenario.simulate_spend_exhaustion(
            tenant_id="tenant_breach_test",
            tier="economy",
            num_bursts=15
        )
        assert res["breached"] is True
        assert res["approvals"] == 10
        assert res["rejections"] == 5
        assert res["final_spent"] == 0.20
        assert len(res["history"]) == 15
        assert res["history"][10]["status"] == "rejected"

    @pytest.mark.asyncio
    async def test_redis_outage_failsafe_allows_free_blocks_paid(self):
        scenario = CostGuardBreachScenario()
        results = await scenario.test_failsafe_redis_outage(tenant_id="tenant_offline")
        
        # Free tier is safe ($0 cost)
        assert results["free"]["allowed"] is True
        assert results["free"]["status"] == "dispatched"

        # Paid tiers are rejected to prevent unbilled cost drift
        assert results["economy"]["allowed"] is False
        assert results["economy"]["status"] == "rejected_safely"
        assert results["premium"]["allowed"] is False
        assert results["premium"]["status"] == "rejected_safely"

    @pytest.mark.asyncio
    async def test_cost_guard_benchmark_runner(self):
        scenario = CostGuardBreachScenario()
        metrics = await scenario.run_benchmark(num_tenants=4, tasks_per_tenant=15)
        
        assert metrics.total_requests == 60
        assert metrics.custom_metrics["tenants_tested"] == 4
        assert metrics.custom_metrics["tenants_breached"] > 0
        assert metrics.failed_requests > 0  # breached tasks are rejected
        assert metrics.successful_requests > 0


class TestJitOtpValidationScenario:
    """Tests for Scenario 3: JIT OTP Lifecycle & Escalation."""

    def test_otp_generation_and_entropy(self):
        scenario = JitOtpValidationScenario(otp_ttl_seconds=300)
        code1 = scenario.generate_otp("admin_1", active_channel="discord")
        code2 = scenario.generate_otp("admin_2", active_channel="email")

        assert len(code1) == 6
        assert code1.isdigit()
        assert len(code2) == 6
        assert code2.isdigit()
        assert code1 != code2  # Highly improbable to collide

    @pytest.mark.asyncio
    async def test_otp_dispatch_and_email_fallback(self):
        scenario = JitOtpValidationScenario()
        code = scenario.generate_otp("admin_dispatch", active_channel="discord")

        # 1. Normal Discord delivery
        res_discord = await scenario.dispatch_otp("admin_dispatch", code, simulate_discord_failure=False)
        assert res_discord["status"] == "delivered"
        assert res_discord["effective_channel"] == "discord"

        # 2. Discord failure triggers automated email fallback
        res_email = await scenario.dispatch_otp("admin_dispatch", code, simulate_discord_failure=True)
        assert res_email["status"] == "delivered"
        assert res_email["effective_channel"] == "email"

    @pytest.mark.asyncio
    async def test_otp_verification_and_escalation_token(self):
        scenario = JitOtpValidationScenario()
        code = scenario.generate_otp("admin_verify")

        # Correct code -> escalation granted
        res = await scenario.verify_otp("admin_verify", code)
        assert res["status"] == "authorized"
        assert "escalation_token" in res
        assert len(res["escalation_token"]) > 20
        assert res["expires_in_seconds"] == 900

    @pytest.mark.asyncio
    async def test_otp_replay_attack_prevention(self):
        scenario = JitOtpValidationScenario()
        code = scenario.generate_otp("admin_replay")

        # 1st verification -> authorized
        res1 = await scenario.verify_otp("admin_replay", code)
        assert res1["status"] == "authorized"

        # 2nd verification with same code -> rejected as replay attack
        res2 = await scenario.verify_otp("admin_replay", code)
        assert res2["status"] == "rejected"
        assert "replay_attack_detected" in res2["reason"]

    @pytest.mark.asyncio
    async def test_otp_brute_force_lockout(self):
        scenario = JitOtpValidationScenario(max_attempts=5)
        scenario.generate_otp("admin_bruteforce")

        # Submit 4 wrong codes
        for attempt in range(4):
            res = await scenario.verify_otp("admin_bruteforce", "000000")
            assert res["status"] == "rejected"
            assert res["reason"] == "invalid_code"
            assert res["remaining_attempts"] == (4 - attempt)

        # 5th wrong code -> triggers account lockout
        res_5 = await scenario.verify_otp("admin_bruteforce", "000000")
        assert res_5["status"] == "rejected"
        assert "account_locked" in res_5["reason"]

        # Subsequent attempts are blocked immediately due to lock
        res_subsequent = await scenario.verify_otp("admin_bruteforce", "123456")
        assert res_subsequent["status"] == "rejected"
        assert res_subsequent["reason"] == "account_locked_brute_force"

    @pytest.mark.asyncio
    async def test_otp_expired_rejection(self):
        scenario = JitOtpValidationScenario(otp_ttl_seconds=-1)  # already expired
        code = scenario.generate_otp("admin_expired")

        res = await scenario.verify_otp("admin_expired", code)
        assert res["status"] == "rejected"
        assert res["reason"] == "otp_expired"

    @pytest.mark.asyncio
    async def test_jit_otp_benchmark_runner(self):
        scenario = JitOtpValidationScenario()
        metrics = await scenario.run_benchmark(num_verifications=25)
        
        assert metrics.total_requests == 25
        assert metrics.successful_requests == 25
        assert metrics.failed_requests == 0
        assert metrics.rps > 0


class TestMasterSyntheticSuiteRunner:
    """Tests for full master benchmark suite runner."""

    @pytest.mark.asyncio
    async def test_master_suite_runner(self):
        runner = SyntheticBenchmarkSuiteRunner()
        report = await runner.run_all(swarm_requests=10, cost_guard_tenants=3, jit_otp_verifications=15)

        assert report["summary"]["all_scenarios_passed"] is True
        assert "demo_agent_swarm" in report["scenarios"]
        assert "cost_guard_breach" in report["scenarios"]
        assert "jit_otp_validation" in report["scenarios"]
        assert report["summary"]["total_operations"] > 0
