# মেমোরি ব্যবহার কমানোর জন্য সমাধান (Zero Maintenance Cost রেখে)

## ১. ক্যাশে অপটিমাইজেশন

### সমস্যা

- মেমোরি ব্যবহার ৯০% এর উপরে
- রেন্ডার ফ্রি টিয়ারে ৫১২ এমবি র‍্যাম শুধুমাত্র

### সমাধান

1. **লাইটওয়েট ক্যাশে ব্যবহার করুন**:
   - `cachetools` এর [LRUCache](file://f:\supremeai\backend\core\optimization\performance_optimizer.py#L65-L122) ব্যবহার করুন মেমোরি নির্দিষ্ট সীমায় রাখতে
   - ক্যাশে এন্ট্রির TTL (Time-To-Live) সেট করুন যাতে পুরানো ডেটা অটো মুছে যায়

2. **ক্যাশে সাইজ সীমিত করুন**:
   - [LLM_CACHE_MAX_SIZE](file://f:\supremeai\backend\core\config.py#L104-L104) কমান (বর্তমানে ৫০০ হতে পারে)
   - কনফিগে `LLM_CACHE_MAX_SIZE: int = Field(default=100)` সেট করুন

## ২. ডেটাবেস কানেকশন অপটিমাইজেশন

### সমস্যা

- অপ্রয়োজনীয় ডেটাবেস কানেকশন মেমোরি খাচ্ছে

### সমাধান

1. **কানেকশন পুল সাইজ কমান**:
   - `pgbouncer_pool.py` এ কানেকশন পুলের সাইজ কমান
   - বর্তমানে এটি `min_size=3, max_size=12` আছে - এটি `min_size=1, max_size=5` করুন

## ৩. ব্যাকগ্রাউন্ড প্রসেস নিষ্ক্রিয় করুন

### সমস্যা

- অপ্রয়োজনীয় ব্যাকগ্রাউন্ড প্রসেস মেমোরি ব্যবহার করছে

### সমাধান

1. **অপ্রয়োজনীয় এজেন্ট বন্ধ করুন**:
   - [SelfEvolutionAgent](file://f:\supremeai\backend\core\evolution\self_evolution_agent.py#L38-L322), [DailyLearner](file://f:\supremeai\backend\core\evolution\daily_learner.py#L402-L569), [AutoScalingAgent](file://f:\supremeai\backend\agents\infrastructure\auto_scaling_agent.py#L48-L532) ইত্যাদি ডিফল্টভাবে বন্ধ রাখুন
   - [.env](file://f:\supremeai\backend\alembic\env.py#L0-L0) ফাইলে `ENABLE_SELF_EVOLUTION_AGENT=false` ইত্যাদি সেট করুন

## ৪. রিডিস ক্যাশে অপটিমাইজেশন

### সমস্যা

- রিডিস ক্যাশে এন্ট্রি সঠিকভাবে TTL সেট না করা

### সমাধান

1. **ক্যাশে এন্ট্রিতে TTL সেট করুন**:
   - রিডিসে প্রতিটি ক্যাশে এন্ট্রির জন্য ৩০-৬০ মিনিট TTL সেট করুন
   - কোডে `redis.set(key, value, ex=1800)` ব্যবহার করুন

## ৫. লগিং অপটিমাইজেশন

### সমস্যা

- অতিরিক্ত লগিং মেমোরি খাচ্ছে

### সমাধান

1. **লগ লেভেল কমান**:
   - প্রোডাকশনে [INFO](file://f:\supremeai\backend\core\auto_healer.py#L44-L44) এর পরিবর্তে [WARNING](file://f:\supremeai\scripts\devops\config\models.py#L7-L7) বা [ERROR](file://f:\supremeai\scripts\devops\config\models.py#L8-L8) লগ করুন
   - `LOG_LEVEL=WARNING` সেট করুন

## ৬. অপ্রয়োজনীয় ডিপেন্ডেন্সি রিমুভ

### সমস্যা

- অপ্রয়োজনীয় লাইব্রেরি মেমোরি খাচ্ছে

### সমাধান

1. **প্রয়োজনের বাইরে ডিপেন্ডেন্সি রিমুভ করুন**
2. **টুল লোডিং অপটিমাইজ করুন** - শুধুমাত্র প্রয়োজনীয় টুল লোড করুন

## ৭. মেমোরি প্রোফাইলিং টুল ব্যবহার

### সমাধান

1. `tracemalloc` বা `memory_profiler` ব্যবহার করে কোন ফাংশন কত মেমোরি খাচ্ছে তা চেক করুন
2. মেমোরি লিক ডিটেক্ট করুন এবং ঠিক করুন

## সারমর্ম

রেন্ডার ফ্রি টিয়ারে রান করতে গেলে মেমোরি অপটিমাইজেশন অত্যন্ত গুরুত্বপূর্ণ। ক্যাশে সাইজ, ডেটাবেস কানেকশন, ব্যাকগ্রাউন্ড প্রসেস এবং লগিং সবগুলো অপটিমাইজ করতে হবে।

হ্যাঁ—আমি আপনার **বর্তমান live Render service-এর metrics + error/warning logs** দেখে বলছি। আমার verdict হলো:

> **এই optimization plan-এর মূল direction সঠিক, কিন্তু 그대로 apply করা উচিত নয়।**
> বিশেষ করে `LLM_CACHE_MAX_SIZE=100` বা সব agent বন্ধ করার আগে root cause ঠিক করতে হবে।

আপনার বর্তমান Render service `supremeai-backend-v2` Free plan-এ চলছে এবং memory limit **536,870,900 bytes ≈ 512 MiB**। Live metrics-এ memory প্রায় **435–450 MB** পর্যন্ত ছিল, অর্থাৎ roughly **81–84% of container limit**। আর application নিজে ~**90.4–90.6%** warning দিচ্ছে।

## 🔴 সবচেয়ে গুরুত্বপূর্ণ সমস্যা: Cache নয়, DB/asyncpg architecture

Live log-এ বারবার এই error আসছে:

`DuplicatePreparedStatementError`

এবং Render log নিজেই কারণ হিসেবে দেখাচ্ছে:

> PgBouncer transaction/statement mode + asyncpg prepared statements conflict.

এটি `SentinelAgent`, `ConfigCache`, `maintenance_pipeline`—একাধিক জায়গায় হচ্ছে।

অর্থাৎ বর্তমানে আপনার architecture এমন কিছু করছে:

**SQLAlchemy → asyncpg → PgBouncer → PostgreSQL**

কিন্তু asyncpg prepared statement cache এবং PgBouncer-এর mode একে অপরের সাথে conflict করছে।

### এর impact

এটা শুধু একটি harmless warning নয়।

এর ফলে:

- DB health check fail হচ্ছে
- Sentinel বারবার DB operation করতে গিয়ে error পাচ্ছে
- ConfigCache DB load fail করছে
- maintenance cleanup fail করছে
- Sentinel heartbeat হারাচ্ছে
- Supervisor বারবার dead/unhealthy agent monitor করছে
- একই error বারবার log হচ্ছে

সুতরাং **এটিই Phase 1-এর #1 priority।**

---

# আপনার proposed 7টি solution-এর verdict

| Proposed change                | আমার verdict                          |      Priority |
| ------------------------------ | ------------------------------------- | ------------: |
| LRU cache + TTL                | ✅ করব                                 |          High |
| `LLM_CACHE_MAX_SIZE 500 → 100` | ⚠️ benchmark করে                      |        Medium |
| DB pool `3/12 → 1/5`           | ⚠️ হ্যাঁ, কিন্তু আগে architecture fix |          High |
| Background agents disable      | ✅ selectiveভাবে                       | **Very High** |
| Redis TTL                      | ✅ করব                                 |        Medium |
| `LOG_LEVEL=WARNING`            | ⚠️ পুরো system-এ নয়                   |           Low |
| Dependency removal             | ✅ audit করব                           |        Medium |
| tracemalloc profiling          | ✅ অবশ্যই                              |          High |

---

# 1. Cache optimization — ✅ YES

এটা আপনার plan-এর ভালো অংশ।

`cachetools.LRUCache` ব্যবহার করা reasonable, কারণ in-process cache-এর upper bound থাকবে।

আমি শুধু:

```text
LLM_CACHE_MAX_SIZE = 100
```

blindly সেট করব না।

কারণ cache entry-এর size সমান নয়।

উদাহরণ:

```text
100 small objects ≠ 100 large LLM responses
```

### Better approach

Environment-driven:

```text
LLM_CACHE_MAX_SIZE=100
LLM_CACHE_TTL_SECONDS=1800
```

এবং cache অবশ্যই:

- bounded
- TTL-based
- LRU
- serialization-efficient

হতে হবে।

### Target

প্রথমে:

```text
100 entries
30 min TTL
```

তারপর Render memory observe করা।

---

# 2. DB pool — ⚠️ YES, but not the first fix

আপনার proposed:

```text
min_size=3
max_size=12
```

থেকে:

```text
min_size=1
max_size=5
```

করাটা 512 MB environment-এর জন্য reasonable।

কিন্তু এখানে একটা গুরুত্বপূর্ণ বিষয়:

**pool size কমালেই `DuplicatePreparedStatementError` ঠিক হবে না।**

কারণ log-এর root cause prepared statement handling।

### আগে ঠিক করতে হবে

যদি PgBouncer ব্যবহার করেন, asyncpg connection configuration-এ:

```text
statement_cache_size=0
```

ব্যবহার করার প্রয়োজন হতে পারে।

অথবা architecture অনুযায়ী:

**PgBouncer বাদ দিয়ে SQLAlchemy/asyncpg-এর own pooling** ব্যবহার করা যেতে পারে।

কোনটা আপনার current infrastructure-এর জন্য correct সেটা codebase দেখে নির্ধারণ করা উচিত।

### তাই priority

```text
Prepared statement compatibility
        ↓
DB pool tuning
        ↓
Observe memory
```

---

# 3. Background agents — 🔴 এখানে আপনার plan সবচেয়ে বেশি সঠিক

Live log-এ খুব গুরুত্বপূর্ণ evidence আছে।

বারবার:

```text
Agent 'sentinel' has no heartbeat for 90s
Agent 'swarm-cache' has no heartbeat for 90s
Agent 'task-queue-worker' has no heartbeat for 90s
Agent 'system-telemetry' has no heartbeat for 90s
```

তারপর:

```text
120s
150s
180s
...
630s
```

পর্যন্ত যাচ্ছে।

এটা normal নয়।

বিশেষ করে আপনার memory pressure-এর মধ্যে এতগুলো continuously running autonomous/background subsystem রাখার প্রয়োজন আছে কিনা সেটা review করা উচিত।

### কিন্তু আমি "সব বন্ধ" বলব না।

বরং 3-tier architecture করব:

### Tier A — Always ON

শুধু production core:

```text
API
Auth
DB
LLM routing
essential request processing
health endpoints
```

### Tier B — On-demand

```text
SelfEvolutionAgent
AutoSkillCreator
AutoScalingAgent
advanced autonomous operations
```

User/admin action বা explicit feature request হলে চালু হবে।

### Tier C — Scheduled/offline

```text
DailyLearner
deep optimization
model analysis
cleanup
long-running evolution
```

এগুলো request-serving process-এর সাথে সবসময় চালানো উচিত নয়।

---

# 4. Redis TTL — ✅ YES, but understand one thing

আপনার:

```python
redis.set(key, value, ex=1800)
```

approach ভালো।

কিন্তু Redis cache-এর memory এবং Render web service-এর Python process memory **এক জিনিস নয়**।

Redis যদি external Render Key Value/Redis instance হয়, তার memory আপনার Python process-এর 512 MB-এর অংশ নয়।

তাই Redis optimization করবেন:

- Redis memory control করার জন্য
- stale data কমানোর জন্য
- cost/performance-এর জন্য

কিন্তু **512 MB web service memory problem-এর primary fix হিসেবে Redis TTL-কে ধরবেন না।**

---

# 5. Logging — ⚠️ আপনার plan এখানে একটু ভুল direction-এ

আপনি বলেছেন:

```text
INFO → WARNING
```

আমি production-এ পুরো application-এর জন্য এটা করব না।

কারণ debugging-এর জন্য INFO অনেক গুরুত্বপূর্ণ।

বরং:

### Keep

```text
ERROR
WARNING
```

### selectively keep

```text
INFO
```

### Remove/reduce

- repeated heartbeat warnings
- same memory warning every 30 sec
- duplicate DB exception stack traces
- noisy polling logs

আপনার বর্তমান log-এ যেমন:

```text
STILL WARNING (90.43%)
STILL WARNING (90.45%)
STILL WARNING (90.61%)
```

বারবার আসছে।

এগুলো memory খুব বেশি খাচ্ছে—এমন প্রমাণ নেই।

বরং **log noise** তৈরি করছে।

একটা state-change based logger ভালো:

```text
90% crossed → WARNING
still 90% → no log
below 85% → recovery log
```

---

# 6. Dependencies — ✅ অবশ্যই audit করুন

এটা আমি strongly recommend করছি।

বিশেষ করে আপনি আগে `sentence_transformers` dependency পেয়েছিলেন—এই ধরনের ML dependency Python process startup memory অনেক বাড়াতে পারে।

512 MB environment-এ আমাদের philosophy হওয়া উচিত:

> **Don't load an ML framework just because one feature might use it.**

Instead:

```text
Core API
   ↓
lightweight dependencies
   ↓
optional/heavy feature
   ↓
lazy import
```

উদাহরণ:

```python
if feature_enabled:
    from sentence_transformers import ...
```

rather than module import at startup।

---

# 7. tracemalloc — ✅ অবশ্যই

এটা খুব গুরুত্বপূর্ণ।

কারণ এখন আমরা জানি:

```text
Render memory ≈ 435–450 MB
```

কিন্তু জানি না:

```text
Python objects = ?
SQLAlchemy = ?
cache = ?
ML libraries = ?
agent state = ?
imported modules = ?
```

এই breakdown দরকার।

তবে production-এ `memory_profiler` permanentভাবে চালানো উচিত নয়।

Better:

```text
tracemalloc
    ↓
diagnostic mode
    ↓
identify allocation
    ↓
fix
    ↓
disable detailed profiling
```

---

# 🚨 আরও একটি গুরুত্বপূর্ণ finding

আপনার memory pressure-এর সাথে এই error pattern-টা correlated:

```text
DB prepared statement error
        ↓
Sentinel DB operation fails
        ↓
heartbeat disappears
        ↓
Supervisor keeps monitoring
        ↓
repeated errors/warnings
```

এটা আমার কাছে **architecture malfunction**-এর signal।

আরেকটি error:

```text
Failed to sync model registries from DB:
cannot import name 'sync_from_db'
from services.smart_model_router
```

এটাও live production error।

অর্থাৎ শুধু memory optimization করলে আপনার backend healthy হয়ে যাবে না।

---

# আমি হলে implementation order এভাবে করতাম

## 🔴 Phase 0 — আগে correctness

### 1. Fix duplicate prepared statements

সবচেয়ে আগে।

```text
asyncpg + PgBouncer compatibility
```

### 2. Fix

```text
sync_from_db import error
```

### 3. Fix Sentinel heartbeat architecture

DB failure হলে agent যেন permanently zombie state-এ না যায়।

---

# 🟠 Phase 1 — Memory reduction

তারপর:

```text
LLM cache
    ↓
LRU + TTL
    ↓
100 initial max
```

তারপর:

```text
DB pool
3/12
 ↓
1/5
```

তারপর:

```text
disable unnecessary always-on agents
```

---

# 🟡 Phase 2 — Dependency optimization

Audit করুন:

```text
sentence-transformers
torch
transformers
numpy
scipy
pandas
opencv
browser automation
ML/embedding libraries
```

যেগুলো startup-এ প্রয়োজন নেই:

**lazy load / optional dependency / remove**

---

# 🟢 Phase 3 — Memory validation

প্রতিটি deploy-এর পরে:

```text
Startup memory
↓
Idle memory
↓
10 requests
↓
50 requests
↓
100 requests
↓
LLM request
↓
DB-heavy request
↓
memory after GC
```

আমাদের target হওয়া উচিত:

### Current

```text
~435–450 MB
```

### First target

```text
<400 MB
```

### Good target

```text
350–380 MB
```

### Excellent for 512 MB

```text
<350 MB
```

কারণ 512 MB-এর একেবারে কাছাকাছি থাকলে সামান্য traffic spike-এ OOM হতে পারে।

---

# ⚠️ একটা জিনিস আমি এখনই করতাম না

আমি **শুধু memory কমানোর জন্য**:

```text
ENABLE_SELF_EVOLUTION_AGENT=false
ENABLE_DAILY_LEARNER=false
ENABLE_AUTO_SCALING_AGENT=false
```

সবগুলো একসাথে blindly disable করতাম না।

কারণ আপনার SupremeAI-এর autonomous architecture-এর অংশ এগুলো।

বরং configuration-এ:

```text
CORE
OPTIONAL
SCHEDULED
```

এই তিন category তৈরি করতাম।

এতে feature হারাবেন না, কিন্তু 512 MB instance-এ সবসময় সবকিছু loaded/running থাকবে না।

---

# আমার final recommendation

আপনার দেওয়া plan-কে আমি **প্রায় 70% approve** করব, কিন্তু execution order পরিবর্তন করব।

```text
CURRENT
────────────────────────
~435–450 MB memory
~512 MB limit
90%+ internal warning
DB prepared statement errors
multiple zombie agents
repeated warnings
missing model-router import
────────────────────────

             ↓

PHASE 1
DB/PgBouncer/asyncpg FIX
             ↓
PHASE 2
Disable unnecessary always-on agents
             ↓
PHASE 3
LRU + TTL + bounded cache
             ↓
PHASE 4
DB pool 1–5
             ↓
PHASE 5
Heavy dependency audit/lazy loading
             ↓
PHASE 6
Logging noise reduction
             ↓
PHASE 7
tracemalloc validation
             ↓

TARGET
~350–380 MB idle/normal
<80% memory under normal load
no repeated DB prepared-statement errors
no zombie heartbeat warnings
```

### সবচেয়ে গুরুত্বপূর্ণ কথা

**আপনার বর্তমান Render log দেখে আমার মনে হচ্ছে memory problem-এর একটা অংশ symptom, আর DB/agent architecture problem একটা root-cause multiplier।**

তাই শুধু:

> `LLM_CACHE_MAX_SIZE 500 → 100`

করলে আমি সন্তুষ্ট হব না।

**প্রথমে `DuplicatePreparedStatementError` + unnecessary always-on agents ঠিক করা উচিত।** এরপর cache/pool/dependency optimization করলে 512 MB Free instance-এ থাকার সম্ভাবনা অনেক বেশি হবে। Live Render monitoring-এর জন্য এই metrics/log workflow-ই উপযুক্ত।

**আমার recommendation: এই plan follow করুন, কিন্তু revised order-এ—এবং সরাসরি production-এ সব change একসাথে নয়।**
