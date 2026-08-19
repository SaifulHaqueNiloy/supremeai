"""
SupremeAI — 10k User Zero-Cost Defense Layer Test Suite
======================================================
Validates Tier 0 cache hits, multi-provider load balancing, and 429 auto-failover.
"""

import asyncio
import pytest
import time
from core.llm.distilled_cache_resolver import DistilledCacheResolver
from core.llm.free_tier_quota_balancer import FreeTierQuotaBalancer
from core.llm.zero_cost_gateway import ZeroCostGateway


@pytest.mark.asyncio
async def test_tier0_instant_cache_hit():
    gateway = ZeroCostGateway()
    # Query known built-in precomputed patch
    res = await gateway.generate_response("How do I setup FastAPI CORS middleware?")
    
    assert res["cache_hit"] is True
    assert res["tier"] == "Tier_0_Distilled_Cache"
    assert res["tokens_consumed"] == 0
    assert "CORSMiddleware" in res["text"]
    assert res["latency_ms"] < 50.0  # Fast sub-50ms resolution


@pytest.mark.asyncio
async def test_tier1_multi_provider_load_balancing():
    balancer = FreeTierQuotaBalancer()
    
    # Simulate heavy traffic to groq
    for _ in range(35):
        balancer.record_usage("groq/llama-3.3-70b-versatile", tokens=200)
    
    # Should automatically divert traffic to another provider (e.g. cloudflare, cerebras or gemini)
    optimal = balancer.select_optimal_free_provider(estimated_tokens=500)
    assert "groq" not in optimal  # Diverted away from throttled groq


@pytest.mark.asyncio
async def test_429_failover_resilience():
    gateway = ZeroCostGateway()
    
    fail_count = 0
    async def mock_failing_provider(model: str, prompt: str):
        nonlocal fail_count
        if "gemini" in model or "groq" in model:
            fail_count += 1
            raise Exception("429 Too Many Requests: Rate Limit Exceeded")
        return f"Success via {model}"

    # Query novel prompt not in cache
    res = await gateway.generate_response(
        prompt="Synthesize unique async reactor pattern xyz123",
        mock_provider_call=mock_failing_provider
    )

    # Should have recovered and succeeded on an alternate provider (e.g. cloudflare or cerebras)
    assert fail_count >= 1
    assert res["cache_hit"] is False
    assert "Success via" in res["text"]
    assert res["tier"] == "Tier_1_Free_Quota_Balancer"
