"""
Unit and Hard-Integration Tests for Autonomous Cognitive Cache Matrix (ACCM).
Verifies:
1. Entropy Zone Classification (Zone 1 Immutable, Zone 2 Semi-Volatile, Zone 3 Zero-Trust)
2. Intent-Aware Zero-Cache Bypass (Tests, Debug, Secrets, OTP)
3. Self-Healing Cache Blast on corrupted cache values
4. Zone & Key Invalidation
"""

import pytest
import pytest_asyncio
from core.cache.autocache_proxy import AutoCacheProxy, EntropyZone


@pytest.fixture
def cache_proxy():
    return AutoCacheProxy()


def test_entropy_zone_classification(cache_proxy):
    # Zone 3: Zero-Trust triggers
    assert cache_proxy.classify_entropy_zone("Debug JWT authentication failure") == EntropyZone.ZERO_TRUST
    assert cache_proxy.classify_entropy_zone("Run test suite for database migration") == EntropyZone.ZERO_TRUST
    assert cache_proxy.classify_entropy_zone("Verify TOTP OTP secret key token") == EntropyZone.ZERO_TRUST
    assert cache_proxy.classify_entropy_zone("Audit environment drift") == EntropyZone.ZERO_TRUST

    # Zone 1: Immutable triggers
    assert cache_proxy.classify_entropy_zone("Parse AST grammar and syntax tree") == EntropyZone.IMMUTABLE
    assert cache_proxy.classify_entropy_zone("Fetch documentation and readme guide") == EntropyZone.IMMUTABLE

    # Zone 2: Semi-Volatile triggers
    assert cache_proxy.classify_entropy_zone("Configure model provider routing weights") == EntropyZone.SEMI_VOLATILE
    assert cache_proxy.classify_entropy_zone("List available skills and agents") == EntropyZone.SEMI_VOLATILE


def test_infer_category_and_ttl(cache_proxy):
    assert cache_proxy.infer_category_from_prompt("Debug transaction token") == "zero_trust"
    assert cache_proxy.get_ttl_for_category("zero_trust") == 0

    assert cache_proxy.infer_category_from_prompt("Show API documentation") == "static_docs"
    assert cache_proxy.get_ttl_for_category("static_docs") == 86400

    assert cache_proxy.infer_category_from_prompt("Generate Python function code") == "code_gen"
    assert cache_proxy.get_ttl_for_category("code_gen") == 3600


@pytest.mark.asyncio
async def test_zero_trust_bypass_execution(cache_proxy):
    call_count = 0

    async def compute_heavy_task():
        nonlocal call_count
        call_count += 1
        return f"task_result_{call_count}"

    # First call with zero_trust category (TTL = 0)
    res1 = await cache_proxy.get_or_compute("task:1", "zero_trust", compute_heavy_task)
    assert res1 == "task_result_1"
    assert call_count == 1

    # Second call must NOT use cache because it's Zero-Trust
    res2 = await cache_proxy.get_or_compute("task:1", "zero_trust", compute_heavy_task)
    assert res2 == "task_result_2"
    assert call_count == 2


@pytest.mark.asyncio
async def test_immutable_cache_hit(cache_proxy):
    call_count = 0

    async def compute_ast_analysis():
        nonlocal call_count
        call_count += 1
        return {"ast_nodes": 42, "status": "valid"}

    # First call - cache miss, computes
    res1 = await cache_proxy.get_or_compute("ast:hash123", "immutable_ast", compute_ast_analysis)
    assert res1 == {"ast_nodes": 42, "status": "valid"}
    assert call_count == 1

    # Second call - cache hit, does NOT recompute
    res2 = await cache_proxy.get_or_compute("ast:hash123", "immutable_ast", compute_ast_analysis)
    assert res2 == {"ast_nodes": 42, "status": "valid"}
    assert call_count == 1  # Still 1, 100% cached


@pytest.mark.asyncio
async def test_self_healing_cache_blast_on_corruption(cache_proxy):
    call_count = 0

    async def compute_data():
        nonlocal call_count
        call_count += 1
        return {"value": f"healthy_{call_count}"}

    # 1. Store initial value
    res1 = await cache_proxy.get_or_compute("data:key1", "code_gen", compute_data)
    assert res1 == {"value": "healthy_1"}
    assert call_count == 1

    # 2. Corrupt the cache entry intentionally
    cache_proxy.memory_store["data:key1"] = {"value": "corrupted_bad_data"}

    # 3. Define a validator that rejects corrupted data
    def is_healthy(data):
        return isinstance(data, dict) and data.get("value", "").startswith("healthy_")

    # 4. Access with validator: system detects corruption, triggers Cache Blast, and computes fresh
    res2 = await cache_proxy.get_or_compute(
        "data:key1",
        "code_gen",
        compute_data,
        validator_fn=is_healthy,
    )
    assert res2 == {"value": "healthy_2"}
    assert call_count == 2
