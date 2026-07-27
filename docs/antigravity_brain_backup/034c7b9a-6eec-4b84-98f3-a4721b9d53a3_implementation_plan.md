# Cloud-Native Security Audit Implementation Plan

নিরাপত্তা অডিট রিপোর্টে চিহ্নিত সমস্যাগুলোর প্রেক্ষিতে আমাদের কোডবেস বিশ্লেষণ করে নিম্নলিখিত সংশোধনীগুলো প্রস্তাব করা হচ্ছে:

## Proposed Changes

### AST Security & Sandbox
#### [MODIFY] [immune_system.py](file:///c:/Users/n/supremeai/supremeai_2.0/backend/core/immune_system.py)
- `ASTSecurityScanner` ক্লাসে `visit_Name` মেথড যোগ করা হবে যাতে নিষিদ্ধ ফাংশনের (যেমন `getattr`, `eval` ইত্যাদি) রেফারেন্স সংরক্ষণ বা অন্য ভ্যারিয়েবলে অ্যাসাইন করাও ব্লক করা যায়।

#### [MODIFY] [docker_sandbox.py](file:///c:/Users/n/supremeai/supremeai_2.0/backend/sandbox/docker_sandbox.py)
- `test_payload` সরাসরি পাইথন কমান্ড স্ট্রিং-এ কনক্যাটেনেট না করে কন্টেইনারে Environment Variable (`SANDBOX_PAYLOAD`) হিসেবে পাস করা হবে এবং কন্টেইনারের ভেতর `ast.literal_eval` দিয়ে নিরাপদে পার্স করা হবে।

### Network & Observability
#### [MODIFY] [sentinel_agent.py](file:///c:/Users/n/supremeai/supremeai_2.0/backend/core/sentinel_agent.py)
- `_validate_endpoint_url` মেথডে `production`/`staging`-এ শুধুমাত্র পোর্ট `8080` (লোকাল ব্যাকএন্ড) ব্যতীত অন্য সমস্ত লুপব্যাক/লোকালহোস্ট রিকোয়েস্ট ব্লক করার লজিক যোগ করা হবে।

### Distributed Caching & Locks
#### [MODIFY] [redis_manager.py](file:///c:/Users/n/supremeai/supremeai_2.0/backend/core/cache/redis_manager.py)
- Idempotency Lock ডিলিট করার সময় lock hijacking এড়াতে `contextvars` দিয়ে প্রতিটি রিকোয়েস্টের ইউনিক লক টোকেন ট্র্যাকিং নিশ্চিত করা হবে, যা Lua স্ক্রিপ্টের মাধ্যমে কেবল ওনারশিপ ম্যাচ করলেই লক রিলিজ করবে।

#### [MODIFY] [rate_limiter.py](file:///c:/Users/n/supremeai/supremeai_2.0/backend/core/rate_limiter.py)
- `InMemoryFallbackLimiter._cleanup` মেথডে কোনো কী-এর ভ্যালু খালি (empty list) হয়ে গেলে মেমোরি লিক এড়াতে ডিকশনারি থেকে কী-টি ডিলিট (`del`) করে দেওয়া হবে।

### Secrets & Configuration Drift
#### [MODIFY] [config.py](file:///c:/Users/n/supremeai/supremeai_2.0/backend/core/config.py)
- `_get_cached_secret` মেথডে ইনফিনিট ইন-মেমোরি ক্যাশিং পরিহার করে সরাসরি `secret_vault.fetch_secret(key)` কল করা হবে, যা ইতিমধ্যে TTL ক্যাশিং মেনে চলে। এতে সিক্রেট রোটেশন কাজ করবে।

### Precision & Information Disclosure
#### [MODIFY] [token_deductor.py](file:///c:/Users/n/supremeai/supremeai_2.0/backend/core/llm/token_deductor.py)
- `deduct_byoc_deployment`-এ floating-point precision loss এড়াতে Decimal conversion ব্যবহার করা হবে।

#### [MODIFY] [payments.py](file:///c:/Users/n/supremeai/supremeai_2.0/backend/api/routes/payments.py)
- Deprecated পেমেন্ট রাউটের এক্সেপশন মেসেজে `detail=str(e)` পরিহার করে জেনেরিক মেসেজ দিয়ে ইনফরমেশন লিকেজ বন্ধ করা হবে।

## Verification Plan

### Automated Tests
- `pytest backend/tests/core/test_cache_optimization.py` রান করে ইন্টিগ্রিটি ও লকিং মেকানিজম পরীক্ষা করা হবে।
- প্রজেক্টের কোর টেস্ট স্যুট রান করা হবে: `poetry run pytest`
