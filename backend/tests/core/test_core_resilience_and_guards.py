import asyncio
import enum
from datetime import UTC, datetime, timedelta
import pytest
from core.retry_budget import RetryBudget
from core.enum_guard import EnumGuard, EnumGuardError
from core.failure_fingerprint import make_fingerprint, _normalize_message
from core.permission_cache import PermissionCache, PermissionResult

class SampleStatus(enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    FAILED = "failed"

@pytest.mark.asyncio
async def test_retry_budget_consume_and_refill():
    budget = RetryBudget(max_tokens=2, refill_rate_per_sec=10.0)
    assert await budget.consume() is True
    assert await budget.consume() is True
    assert await budget.consume() is False

    await asyncio.sleep(0.15)
    assert await budget.consume() is True

def test_enum_guard_validation():
    val = EnumGuard.validate_and_parse(SampleStatus, "active")
    assert val == SampleStatus.ACTIVE

    val_upper = EnumGuard.validate_and_parse(SampleStatus, "PENDING")
    assert val_upper == SampleStatus.PENDING

    val_exact = EnumGuard.validate_and_parse(SampleStatus, SampleStatus.FAILED)
    assert val_exact == SampleStatus.FAILED

    with pytest.raises(EnumGuardError):
        EnumGuard.validate_and_parse(SampleStatus, "invalid_status")

    fallback_val = EnumGuard.safe_fallback(SampleStatus, "non_existent", SampleStatus.PENDING)
    assert fallback_val == SampleStatus.PENDING

def test_failure_fingerprint():
    msg = "Error connecting to 192.168.1.1:8080 with id 12345678-1234-1234-1234-123456789abc and ptr 0xdeadbeef"
    norm = _normalize_message(msg)
    assert "<IP>" in norm
    assert "<UUID>" in norm
    assert "<HEX>" in norm

    try:
        raise ValueError("Invalid user input detected")
    except ValueError as e:
        fp1 = make_fingerprint(e)
        fp2 = make_fingerprint(e)
        assert fp1 == fp2
        assert len(fp1) == 64

def test_permission_cache():
    cache = PermissionCache(l1_ttl=10, l2_ttl=60)
    
    # 1. never_allowed
    res_never = PermissionResult(action_name="delete_db", state="never_allowed")
    assert bool(res_never) is False

    # 2. always_allowed
    res_always = PermissionResult(action_name="read_docs", state="always_allowed")
    assert bool(res_always) is True

    # 3. allowed_for_now active vs expired
    future_time = datetime.now(UTC) + timedelta(minutes=5)
    res_temp_active = PermissionResult(action_name="temp_edit", state="allowed_for_now", expires_at=future_time)
    assert bool(res_temp_active) is True

    past_time = datetime.now(UTC) - timedelta(minutes=5)
    res_temp_expired = PermissionResult(action_name="temp_edit", state="allowed_for_now", expires_at=past_time)
    assert bool(res_temp_expired) is False

    # Cache store & retrieval
    cache._set_l1(res_always)
    assert cache.check("read_docs") == "always_allowed"
    assert cache.check("unknown_action") == "not_allowed"

    # Health check
    health = cache.health_check()
    assert health["l1_cache_size"] == 1
    assert "read_docs" in health["l1_keys"]

    # Invalidate
    cache.invalidate("read_docs")
    assert cache.check("read_docs") == "not_allowed"
