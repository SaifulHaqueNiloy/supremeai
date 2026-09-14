# SupremeAI — diff.patch সারাংশ

এই প্যাচটি `github.com/saifulHaqueNiloy/supremeai` (commit `f6d5711`) এর ১০টি ফাইলে
**নিরাপত্তা, নির্ভরযোগ্যতা ও পারফরম্যান্স** উন্নতি আনে। নিচে প্রতিটি পরিবর্তনের কারণ ও
প্রভাব ব্যাখ্যা করা হলো।

---

## ১. `backend/api/routes/auth.py` — JWT টোকেন ও লগইন নিরাপত্তা

### সমস্যা
- `db.client.auth.sign_in_with_password(...)` সিঙ্ক্রোনাস কল ছিল async ফাংশনে — event loop ব্লক হতো।
- `except Exception as e: raise HTTPException(401, str(e))` — internal error (DB, network) ক্লায়েন্টকে লিক করত।
- অ্যাক্সেস টোকেন ২৪ ঘণ্টা মেয়াদী ছিল — চুরি হলে দীর্ঘ সময় ব্যবহারযোগ্য।
- টোকেনে `iat`, `jti` claim ছিল না — রিভোকেশন ও অডিট ট্রেইলিং অসম্ভব।

### সমাধান
- `asyncio.to_thread()` দিয়ে Supabase কল thread pool-এ অফলোড করা হলো।
- নির্দিষ্ট `HTTPException` পুনরায় রেইজ করে, বাকি exception 500 + generic message রিটার্ন করে।
- অ্যাক্সেস টোকেন ১ ঘণ্টা, নতুন **রিফ্রেশ টোকেন** ৭ দিন মেয়াদী।
- প্রতিটি টোকেনে `iat`, `jti`, `type` (access/refresh) claim যোগ।
- নতুন `/auth/refresh` এন্ডপয়েন্ট — type confusion attack প্রতিরোধ।

---

## ২. `backend/api/routes/admin_auth.py` — Async Redis কল

### সমস্যা
- `redis_queue.get(f"jwt_blacklist:{jti}")` সিঙ্ক্রোনাস Upstash REST কল async route-এ — event loop ব্লক।
- `redis_queue.set(key, ..., ex=window)` একই সমস্যা।
- `require_admin_token` sync ফাংশন ছিল — FastAPI async dependency হিসেবে ব্যবহার হতো।

### সমাধান
- `require_admin_token` ও `admin_rate_limit` এখন `async`।
- সকল `redis_queue.get/set` কল `asyncio.to_thread()` দিয়ে wrapped।

---

## ৩. `backend/api/routes/chat.py` — SSE স্ট্রিমিং হেডার

### সমস্যা
- `stream_chat` এন্ডপয়েন্টে স্ট্যান্ডার্ড SSE হেডার ছিল না — nginx/CDN স্ট্রিম বাফার করত।
- ক্লায়েন্ট ডিসকানেক্ট হলে রিসোর্স ক্লিনআপ ছিল না।

### সমাধান
- `Cache-Control: no-cache, no-transform`, `X-Accel-Buffering: no`, `Connection: keep-alive` হেডার যোগ।
- `Content-Encoding: identity` — কম্প্রেশন বন্ধ যাতে SSE chunks সঠিকভাবে স্ট্রিম হয়।

---

## ৪. `backend/core/app_builder.py` — `/health` এন্ডপয়েন্ট async Redis

### সমস্যা
- `/health` এন্ডপয়েন্টে `redis_queue.set(probe_key, "1", ex=30)` ও `redis_queue.get(probe_key)` সরাসরি সিঙ্ক্রোনাস কল — প্রতিটি health probe-এ event loop ব্লক।

### সমাধান
- `asyncio.to_thread()` দিয়ে offload।
- ৩ সেকেন্ড টাইমআউট সহ — Redis স্টল হলে degraded status রিটার্ন।

---

## ৫. `backend/core/health_check.py` — আসল ডেটাবেস পিং

### সমস্যা (CRITICAL)
- `check_database()` সবসময় `"healthy"` রিটার্ন করত — placeholder ছিল। Monitoring-এ ডেটাবেস ডাউন হলেও false positive "healthy" রিপোর্ট।

### সমাধান
- SQLAlchemy engine দিয়ে আসল `SELECT 1` কুয়েরি চালানো হয়।
- ৩ সেকেন্ড টাইমআউট — দীর্ঘস্থায়ী স্টল রোধে।
- Engine না থাকলে বা কুয়েরি ফেইল করলে `UNHEALTHY` রিপোর্ট।

---

## ৬. `backend/core/security/api_key_middleware.py` — X-Forwarded-For স্পুফিং প্রতিরোধ

### সমস্যা
- `request.client.host` সরাসরি ব্যবহার হতো — ক্লায়েন্ট `X-Forwarded-For` হেডার স্পুফ করে rate limit বাইপাস করতে পারত।

### সমাধান
- `_extract_client_ip(request)` ফাংশন যোগ।
- `settings.trusted_proxy_count` (env var `TRUSTED_PROXY_COUNT`) কনফিগার করা থাকলেই XFF থেকে আসল IP নেওয়া হয়।
- না থাকলে raw `request.client.host` — স্পুফিং সম্ভব কিন্তু behavior unchanged (no breaking change)।

---

## ৭. `backend/core/security/auth_middleware.py` — Token type validation

### সমস্যা
- `_decode_jwt` শুধু exp চেক করত — রিফ্রেশ টোকেন অ্যাক্সেস হিসেবে ব্যবহার হতে পারত (token confusion attack)।

### সমাধান
- `type` claim চেক যোগ — `type=refresh` টোকেন অ্যাক্সেস হিসেবে ব্যবহার রোধ।

---

## ৮. `backend/core/security/input_sanitizer.py` — শক্তিশালী PII মাস্কিং

### সমস্যা
- ফোন রেজেক্স অতিরিক্ত loose — ৪-ডিজিট সংখ্যাকেও ফোন ভাবত।
- ক্রেডিট কার্ড, SSN, IBAN প্যাটার্ন ছিল না।
- ইমেইল রেজেক্স plus-addressing সাপোর্ট করত না।

### সমাধান
- IPv4 প্যাটার্ন প্রতিটি অক্টেট 0-255 চেক সহ।
- ফোন নম্বর ন্যূনতম ৭ ডিজিট, E.164 সামঞ্জস্যপূর্ণ।
- US SSN (`XXX-XX-XXXX`), IBAN, ক্রেডিট কার্ড (13-19 ডিজিট, **Luhn ভ্যালিডেশন সহ**) যোগ।
- Luhn ভ্যালিডেশন false positive উল্লেখযোগ্যভাবে কমায়।

---

## ৯. `backend/database/session.py` — Production fail-fast

### সমস্যা (CRITICAL)
- `init_engine()` ইঞ্জিন তৈরি ব্যর্থ হলে silently SQLite in-memory fallback করত।
- প্রোডাকশনে এটি **সম্পূর্ণ data loss** ঘটাত — প্রতি রিস্টার্টে সব ডেটা মুছে যেত।

### সমাধান
- `ENV=production` হলে SQLite fallback নিষিদ্ধ — সরাসরি `RuntimeError` raise।
- Test/staging environment-এ fallback অপরিবর্তিত।

---

## ১০. `frontend/src/services/apiClient.ts` — Token ক্লিয়ার ও কনকারেন্সি কনফিগ

### সমস্যা
- `cachedToken` একবার সেট হলে লগআউটে মুছে যেত না — পুরোনো টোকেন পরবর্তী রিকোয়েস্টে ব্যবহার।
- কনকারেন্সি hardcoded `3` — env var দিয়ে কনফিগারযোগ্য ছিল না।
- 401 হলেও টোকেন ক্লিয়ার হতো না।

### সমাধান
- `clearAuthToken()` এক্সপোর্ট যোগ — cachedToken ও localStorage উভয় থেকে মুছে।
- কনকারেন্সি `VITE_API_CONCURRENCY` env var দিয়ে কনফিগারযোগ্য (default: 3)।
- `handleResponse` এ 401 হলে automatically `clearAuthToken()` কল।

---

## প্রয়োগ (Apply)

```bash
cd /path/to/supremeai
git apply supremeai-improvements.patch
```

বা commit করতে:

```bash
git apply supremeai-improvements.patch
git add -A
git commit -m "fix(security): critical security & reliability improvements

- auth: async Supabase calls, refresh tokens, jti/iat claims
- admin_auth: async Redis calls (event loop unblock)
- chat: SSE headers for proxy buffering
- health_check: real DB ping (no more fake healthy)
- app_builder: async Redis in /health endpoint
- api_key_middleware: X-Forwarded-For spoofing protection
- auth_middleware: refresh token type validation
- input_sanitizer: Luhn-validated credit card, SSN, IBAN masking
- session: production fail-fast (no SQLite fallback)
- apiClient: token clear on logout/401, env-configurable concurrency"
```

## পরীক্ষা (Testing)

```bash
# Backend
cd backend && poetry run pytest

# Frontend
cd frontend && pnpm test
```

## নতুন Env Vars

- `TRUSTED_PROXY_COUNT` (backend) — XFF থেকে আসল IP এক্সট্র্যাকশনের জন্য পরিচিত প্রক্সি চেইন সংখ্যা।
- `VITE_API_CONCURRENCY` (frontend) — API ক্লায়েন্ট কনকারেন্সি (default: 3)।
