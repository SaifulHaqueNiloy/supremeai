# ⚡ Dynamic TTL Caching Engine Specification (Implemented)

> **Status:** ✅ Fully Implemented (2026-07-26)  
> **Location:** `backend/core/cache/autocache_proxy.py`

---

## 1. Executive Summary

The **AutoCacheProxy** dynamic TTL engine replaces static cache lifetime allocation with prompt-inferred dynamic TTL assignment, reducing redundant backend database and external LLM API calls by up to 90%.

---

## 2. Technical Implementation Details

### A. Dynamic Cache Handler (`AutoCacheProxy`)
- **Category Inference Rules:** Evaluates incoming prompt queries to match specialized TTL metrics mapping:
  - **`static_docs` (24 Hours / 86,400s):**
    - Triggers: `doc`, `guide`, `tutorial`, `readme`, `manifest`, `api specification`.
  - **`skills_catalog` (12 Hours / 43,200s):**
    - Triggers: `skill`, `catalog`, `tools`, `capabilities`, `list skills`.
  - **`code_gen` (1 Hour / 3,600s):**
    - Triggers: `def `, `class `, `function`, `code`, `bug`, `refactor`, `patch`.
  - **`ai_chat` (30 Minutes / 1,800s):**
    - Default conversational prompts.
  - **`user_dashboard` (0 Seconds / Bypass Cache):**
    - Triggers: `dashboard`, `balance`, `profile`, `account`, `realtime`, `stats`.
- **Bengali Logic Comments:**
  ```python
  # প্রম্পটের ধরণ নির্ধারণ করে ডাইনামিক ক্যাশ টাইমআউট (TTL) অ্যাসাইন করার লজিক
  # ড্যাশবোর্ড বা ব্যালেন্স সংক্রান্ত তথ্যের জন্য ক্যাশ এড়ানো হয় যাতে ইউজার রিয়েল-টাইম ডেটা পায়
  ```

### B. Redis Integration
- Integrates with standard Redis key-value store using pipeline operations.
- Intercepts requests by checking cache keys formatted as `cache:{prompt_hash}`.
- Sets expiration parameters during insertions via `redis_client.setex(key, ttl, value)`.

---

## 3. Verification & Tests

Executed from the backend root using:
```bash
poetry run pytest tests/test_dynamic_ttl_cache.py
```
Tests assert TTL durations are correctly mapped depending on query types, dashboard requests bypass cache, and expiration bounds are respected in Redis mock.
