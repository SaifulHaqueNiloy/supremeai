# Backend Test Failures — Implementation Plan

CI রানে **304টি টেস্ট ফেইল** হয়েছে। লগ বিশ্লেষণ করে দেখা গেছে মূলত **৩টি ভিন্ন ধরনের রুট কারণ** আছে যেগুলো থেকে সব ব্যর্থতা উৎপন্ন হয়েছে।

---

## 🔍 রুট কারণ বিশ্লেষণ

### কারণ ১: `AuthMiddleware` টেস্টে Auth Bypass করছে না (সবচেয়ে বড় সমস্যা — ~৮০% failure)

**সমস্যা:**
`auth_middleware.py:139`-এ:
```python
if _is_public_path(path) or (is_test_environment() and getattr(settings, "allow_test_auth_bypass", False)):
```

এখানে `is_test_environment()` সত্য হলেও `allow_test_auth_bypass` **`False`** ডিফল্ট মান রাখা হয়েছিল নিরাপত্তার জন্য। কিন্তু CI workflow-এ এই env var সেট করা নেই।

ফলে `"Bearer test-token"` দিয়ে পাঠানো সব রিকোয়েস্ট JWT ভেরিফাই করতে গিয়ে fail করছে এবং `401 Unauthorized` রিটার্ন করছে।

**প্রভাবিত টেস্ট:** `TestAdminRoutes`, `test_api_new_endpoints`, `test_api_keys`, `test_health_returns_ok`, `test_task_execute_*` সহ ৫০+ ক্লাস।

**ফিক্স:** CI workflow-এ `ALLOW_TEST_AUTH_BYPASS=true` env var যোগ করতে হবে।

---

### কারণ ২: `api.routes.api_keys` ফাংশন সিগনেচার মিসমাচ (টেস্ট বনাম রিয়েল API)

**সমস্যা:**
Test files (`test_api_keys_coverage.py`) পুরনো API সিগনেচার ধরে কল করছে:
```python
# Test বলছে:
result = create_api_key(payload, mock_request)
# কিন্তু বাস্তব function:
create_api_key(payload, request, key_hash, key_masked, key_prefix)  # ৩টি extra arg দরকার

# Test বলছে:
list_api_keys(...)
# কিন্তু import-ই হচ্ছে না:
ImportError: cannot import name 'list_api_keys' from 'api.routes.api_keys'

# Test বলছে:
revoke_api_key("key-1", mock_request)  # ২ arg
# কিন্তু বাস্তব function ১ arg নেয়

# Test বলছে:
rotate_api_key("key-1", mock_request)
# কিন্তু বাস্তব function: rotate_api_key(key_id, new_key_masked, new_key_prefix) নেয়
```

**ফিক্স:** `tests/test_api_keys_coverage.py`-এ টেস্টগুলো রিয়েল API সিগনেচারের সাথে সামঞ্জস্যপূর্ণ করতে হবে।

---

### কারণ ৩: `jwt_secret` property production-mode চেক টেস্টে ভুলভাবে trigger হচ্ছে

**সমস্যা:**
`config.py:467`-এ:
```python
raise ValueError("🚨 CRITICAL: SUPREMEAI_JWT_SECRET must be explicitly set in production...")
```
কিছু টেস্টে `env="test"` থাকলেও `settings.env` পড়তে গিয়ে অন্য কনফিগ থেকে "production" আসছে অথবা `_get_cached_secret("SUPREMEAI_JWT_SECRET")` ক্যাশ থেকে empty রিটার্ন করছে।

**ফিক্স:** CI workflow-এ `SUPREMEAI_JWT_SECRET` ইতিমধ্যে set করা আছে। `TestSettingsValidators.test_get_cached_secret_caches_value` টেস্টের ভেতরে mock context ঠিকমতো প্যাচ করতে হবে।

---

## User Review Required

> [!IMPORTANT]
> **কারণ ১ (AuthMiddleware Bypass)** ফিক্স করার দুটো পথ আছে। আপনাকে সিদ্ধান্ত নিতে হবে:
> - **Option A (Recommended):** CI workflow-এ `ALLOW_TEST_AUTH_BYPASS=true` যোগ করা — production কোডে কোনো পরিবর্তন নেই, শুধু CI config পরিবর্তন।
> - **Option B:** প্রতিটি টেস্ট ফাইলে `settings.allow_test_auth_bypass = True` mock করা — বেশি কাজ কিন্তু workflow-নির্ভর না।

> [!WARNING]
> `test_api_keys_coverage.py` টেস্টগুলো রিয়েল `api/routes/api_keys.py`-র বর্তমান সিগনেচারের সাথে সম্পূর্ণ মিল নেই। `api_keys.py`-এর বর্তমান সিগনেচার রিভিউ করা দরকার নিশ্চিত করতে যে টেস্টগুলো update করা উচিত, নাকি production API সিগনেচার।

---

## Proposed Changes

### Component 1 — CI Workflow Fix (ROOT CAUSE #1)

#### [MODIFY] [supreme-core-ci.yml](file:///c:/Users/n/supremeai/supremeai_2.0/.github/workflows/supreme-core-ci.yml)

Backend test job-এর `env` ব্লকে যোগ করতে হবে:
```yaml
ALLOW_TEST_AUTH_BYPASS: "true"
```

---

### Component 2 — Test File Fix (ROOT CAUSE #2)

#### [MODIFY] [test_api_keys_coverage.py](file:///c:/Users/n/supremeai/supremeai_2.0/backend/tests/test_api_keys_coverage.py)

বাস্তব `api/routes/api_keys.py`-এর ফাংশন সিগনেচার দেখে টেস্টগুলো আপডেট করতে হবে:
- `create_api_key()` call সঠিক করা
- `list_api_keys` import সঠিক করা (function নাম ভেরিফাই করা)
- `revoke_api_key()` এবং `rotate_api_key()` call সঠিক করা

---

### Component 3 — Config Test Fix (ROOT CAUSE #3)

#### [MODIFY] [test_settings_validators.py বা সংশ্লিষ্ট টেস্ট ফাইল](file:///c:/Users/n/supremeai/supremeai_2.0/backend/tests/)

`TestSettingsValidators.test_get_cached_secret_caches_value` টেস্টে `env` এবং jwt_secret mock ঠিকমতো set করতে হবে।

---

## Verification Plan

### Automated Tests
```bash
# ফিক্সের পর লোকালি রান করা
poetry run pytest tests/test_api.py tests/test_admin_routes.py tests/test_api_keys_coverage.py tests/test_api_new_endpoints.py -v --tb=short
```

### Manual Verification
- CI পুশ করার পর GitHub Actions-এ `🐍 Backend (Test)` job সবুজ হয়েছে কিনা চেক করা।

---

## Priority Order

| Priority | কাজ | প্রভাব |
|----------|-----|--------|
| 🔴 P1 | `ALLOW_TEST_AUTH_BYPASS=true` CI-তে যোগ | ~৮০% failure দূর হবে |
| 🟡 P2 | `test_api_keys_coverage.py` সিগনেচার ফিক্স | ~১৫% failure দূর হবে |
| 🟢 P3 | Config/Settings test mock ফিক্স | বাকি failure দূর হবে |
