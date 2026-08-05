# Phase 3: LLM Gateway & AI Orchestration — Audit & Implementation Report

## 📋 Audit Summary

### ✅ Strengths Identified
1. **Lazy Singleton Pattern**: `get_llm_gateway()` avoids cold-start import cost
2. **Secure API Key Passing**: `api_key` per-call via `_get_api_key_for_model()` — no `os.environ` injection
3. **Free Tier Tracker**: Rolling RPM/TPM/RPD windows with conservative 5% buffer below official limits
4. **Provider Priority Chain**: Gemini → Groq → Cloudflare → OpenRouter → Nvidia → HuggingFace → Ollama
5. **Circuit Breaker Per Model**: Each model gets its own `CircuitBreaker` with configurable thresholds
6. **Semantic Cache**: Zero-cost cached responses for repeated queries
7. **Cost Guard**: Tier-based budget validation (`free`/`economy`/`premium`) with Redis-backed spend tracking
8. **Emergency Halt**: Global swarm stop via `swarm_streamer.is_halted()` prevents runaway agents

### ❌ Issues & Gaps Found

| # | Issue | File | Severity | Impact |
|---|-------|------|----------|--------|
| 1 | `_setup_callbacks()` mutates global `litellm` state | `llm_gateway.py:65` | MEDIUM | Not thread-safe in multi-worker mode |
| 2 | `sys.path` manipulation in orchestrator | `orchestrator.py:63` | MEDIUM | Fragile; breaks in Docker/Cloud Run |
| 3 | Routing policy file path uses `os.path.dirname` thrice | `llm_gateway.py:20` | LOW | Relies on module location |
| 4 | No provider quota reset notification | `free_tier_tracker.py` | MEDIUM | No webhook/callback when quota resets |
| 5 | Cost Guard `check_budget` sync/async branching | `cost_guard.py:76` | MEDIUM | Firestore SDK version coupling |
| 6 | Swarm DAG unregistered agent = RuntimeError, not graceful | `swarm_orchestrator.py:177` | LOW | Could be a warning + skip |
| 7 | `TASK_MODEL_MAP` has hardcoded model strings | `llm_gateway.py:43` | MEDIUM | Not configurable via env/settings |
| 8 | No prompt injection guard | `llm_gateway.py:acompletion` | HIGH | User prompts passed directly to LLM |

---

## 🔧 Implementation Plan

### Fix 1: Replace Global litellm State Mutation with Per-Call Settings
**File**: `backend/core/llm/llm_gateway.py`
**Lines**: `_setup_callbacks()` (~line 52) & `_setup_litellm_globals()` (~line 42)

Replace global callbacks with per-call `litellm.acompletion(..., fallbacks=...)` and `litellm.utils.CustomStreamWrapper` wrapper:

```python
def _setup_litellm_globals(self) -> None:
    """বাংলা মন্তব্য: Minimal litellm global settings — শুধু non-mutating config।
    success/failure callback আর globally set না করে per-call kwargs-এ pass করা হবে।
    """
    import litellm  # lazy import
    litellm.drop_params = True
    litellm.telemetry = False
    # litellm.success_callback/failure_callback সরানো হলো — thread-safety issue
```

**In `acompletion()`**, pass callbacks via kwargs instead:
```python
response = await litellm.acompletion(
    model=current_model,
    messages=messages_payload,
    timeout=timeout,
    api_key=api_key,
    # Per-call callbacks — thread-safe
    success_callback=[self._log_success],
    failure_callback=[self._log_failure],
    **kwargs,
)
```

### Fix 2: Remove `sys.path` Manipulation from Orchestrator
**File**: `backend/core/orchestration/orchestrator.py`
**Lines**: 58-63

```python
async def _run_budget_guardian(self) -> None:
    """বাংলা মন্তব্য: sys.path manipulation সরানো হলো — import চলে না হলে graceful degrade."""
    try:
        from scripts.orchestrator.auto_budget_guardian import run_budget_guardian_check
        await asyncio.to_thread(run_budget_guardian_check)
    except ImportError:
        logger.warning("Budget guardian script not found — skipping (non-critical).")
    except Exception as exc:
        logger.error(f"Budget guardian execution failed: {exc}")
```

### Fix 3: Make TASK_MODEL_MAP Configurable via Settings
**File**: `backend/core/llm/llm_gateway.py`
**Lines**: ~43-51 (class level constant → instance attribute with settings fallback)

```python
def __init__(self) -> None:
    self.routing_policy = self._load_routing_policy()
    self._setup_litellm_globals()
    self._circuit_breakers: dict[str, CircuitBreaker] = {}

    # Task-to-Model mapping — settings override first, then defaults
    from core.config import settings
    self.task_model_map = getattr(settings, 'task_model_map', {}) or dict(TASK_MODEL_MAP)

    from core.cache.semantic_cache import SemanticCache
    self.cache = SemanticCache()
```

### Fix 4: Add Provider Quota Reset Callback
**File**: `backend/core/llm/free_tier_tracker.py`
**Lines**: Add after `is_available()` (~line 170)

```python
async def on_quota_reset(self, provider: str) -> None:
    """বাংলা মন্তব্য: যখন কোনো provider-এর quota রিসেট হয়, তখন callback/webhook ট্রিগার করে।
    বর্তমানে শুধু logger warning, পরে WebSocket notification যোগ করা যাবে।
    """
    logger.info(f"[FreeTier] Provider {provider} quota window reset — available again")
    error_event_bus.emit(
        ErrorEvent(
            module="free_tier_tracker",
            error_type="PROVIDER_QUOTA_RESET",
            message=f"Provider {provider} quota reset",
            severity="INFO",
            structured_context=ErrorContext(module="auto_fixed"),
            context={"provider": provider},
        )
    )
```

### Fix 5: Add Prompt Injection Guard in LLM Gateway
**File**: `backend/core/llm/llm_gateway.py`
**Lines**: Add method and call before `acompletion`

```python
def _detect_prompt_injection(self, prompt: str | list[dict[str, Any]]) -> bool:
    """বাংলা মন্তব্য: Prompt injection ডিটেকশন — known patterns check করে।

    Returns:
        True if injection detected (should reject), False if safe.
    """
    if isinstance(prompt, str):
        text = prompt
    elif isinstance(prompt, list):
        text = " ".join(msg.get("content", "") for msg in prompt if isinstance(msg.get("content"), str))
    else:
        return False

    # Known injection patterns
    injection_patterns = [
        "ignore all previous instructions",
        "ignore all prior instructions",
        "you are now",
        "system prompt",
        "forget everything",
        "pretend you are",
        "you are not",
        "bypass",
        "jailbreak",
        "DAN",
        "do anything now",
    ]

    text_lower = text.lower()
    for pattern in injection_patterns:
        if pattern in text_lower:
            logger.warning(f"Potential prompt injection detected: pattern='{pattern}'")
            return True

    return False
```

Call in `acompletion()` before cache check:
```python
if prompt_text and self._detect_prompt_injection(prompt_text):
    error_event_bus.emit(
        ErrorEvent(
            module="llm_gateway",
            error_type="PROMPT_INJECTION_DETECTED",
            message="Prompt injection detected in request",
            severity="WARNING",
            structured_context=ErrorContext(module="auto_fixed"),
        )
    )
    return {"success": False, "error": "Prompt rejected: potential injection detected", "cost": 0.0}
```

---

## 📁 Files to Modify

| # | File | Action | Reason |
|---|------|--------|--------|
| 1 | `backend/core/llm/llm_gateway.py` | EDIT | Replace global litellm state mutation, make TASK_MODEL_MAP configurable, add prompt injection guard |
| 2 | `backend/core/orchestration/orchestrator.py` | EDIT | Remove fragile sys.path manipulation |
| 3 | `backend/core/llm/free_tier_tracker.py` | EDIT | Add quota reset callback method |
| 4 | `backend/core/llm/token_budget.py` | AUDIT | Verify token budgeting accuracy |
| 5 | `backend/core/llm/token_deductor.py` | AUDIT | Verify token deduction correctness |

---

## 🔍 Self-Audit Checklist

- [x] **Ripple-Effect Guard**: Removing global litellm mutation won't break other modules since callbacks are purely logging
- [x] **Anti-Silent Failure**: Prompt injection detection explicitly returns error response, not silent pass
- [x] **Stateless Validation**: Task model map loads from settings (configurable) with defaults fallback
- [x] **Dependency Sync**: All fixes only use existing imports (`settings`, `logger`, `event_bus`)
- [x] **Configuration Drift**: Hardcoded model strings replaced with settings-driven config

---

## ✅ Next Steps After Phase 3
**Proceed to Phase 4: Database & Persistence Layer**
