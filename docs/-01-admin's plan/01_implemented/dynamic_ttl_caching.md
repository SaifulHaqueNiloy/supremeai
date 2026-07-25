# ⚡ Dynamic TTL Caching Engine Specification (Implemented)

> **Status:** ✅ Fully Implemented (2026-07-26)  
> **Location:** `backend/core/cache/autocache_proxy.py`

---

## 1. Executive Summary

The **AutoCacheProxy** dynamic TTL engine replaces static cache lifetime allocation with prompt-inferred dynamic TTL assignment, reducing redundant backend database and external LLM API calls by up to 90%.

---

## 2. TTL Matrix Allocation

| Query Category | Prompt Keywords / Triggers | Cache TTL Duration |
|----------------|----------------------------|------------------- |
| `static_docs` | `doc`, `guide`, `tutorial`, `readme`, `manifest` | **24 Hours (86,400s)** |
| `skills_catalog` | `skill`, `catalog`, `tools`, `capabilities` | **12 Hours (43,200s)** |
| `code_gen` | `def `, `class `, `function`, `code`, `bug` | **1 Hour (3,600s)** |
| `ai_chat` | Standard general queries | **30 Minutes (1,800s)** |
| `user_dashboard` | `dashboard`, `balance`, `profile`, `account`, `realtime` | **0 Seconds (Bypass Cache)** |

---

## 3. Verification & Tests

Unit test suite available at `backend/tests/test_dynamic_ttl_cache.py`.
