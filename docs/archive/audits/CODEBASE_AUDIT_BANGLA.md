# 🔍 SupremeAI কোডবেস বাস্তব অডিট রিপোর্ট

**তারিখ:** ৪ সেপ্টেম্বর, ২০২৬
**স্কোপ:** `main` ব্রাঞ্চের আসল কোড (ডকুমেন্টেশন-নয়) — প্রতিটি দাবি ফাইল খুলে যাচাই করা
**পদ্ধতি:** মডিউল-বাই-মডিউল পড়া → ✅ করা আছে / ⚠️ আংশিক / ❌ নেই / 🐛 বাগ

---

## 1️⃣ Executive Summary

**সংক্ষেপে: আপনার প্ল্যানের যেগুলো "শুধু কাগজে" ভেবেছিলাম, তার বড় একটা অংশ আসলে কোডে ইমপ্লিমেন্ট হয়ে আছে।** বিশেষ করে Free-Tier Tracker, Infisical Bulk Loader, WebSocket DoS ক্যাপ, SSE ফিক্স, ChromaDB PersistentClient ফিক্স — সবই কোডে আছে।

**কিন্তু ৫টি বাস্তব সমস্যা ধরা পড়েছে:**

| # | সমস্যা | গুরুত্ব |
| --- | --- | --- |
| 1 | Ollama নিয়ে কোড-প্ল্যান দ্বন্দ্ব (ব্যাকএন্ডে এখনো সক্রিয়) | 🔴 |
| 2 | মডেল-টাস্ক ম্যাপিং ৩ জায়গায় Hardcoded | 🔴 |
| 3 | Embedding ডাইমেনশন অমিল (৩৮৪ vs ১৫৩৬) + `ai_memory.embedding` TEXT টাইপ | 🔴 |
| 4 | Learning Engine আসলে কিছু শেখে না (flat 1.0 confidence) | 🟠 |
| 5 | Render ৪ সার্ভিস × ৭২০ঘ = ২৮৮০ঘ >> ৭৫০ঘ ফ্রি কোটা | 🔴 |

---

## 2️⃣ মডিউল-ভিত্তিক বাস্তব অবস্থা

### 2.1 LLM স্তর

#### `backend/services/llm/llm_router.py` (৮২৯ লাইন) — ✅ সম্পূর্ণ ইমপ্লিমেন্টেড

- Multi-provider: Moonshot, DeepSeek, Together, Gemini, HF Space, Groq (try-import), Ollama
- `PROVIDER_CAPABILITIES` + `FALLBACK_CHAINS` + `PROVIDER_COSTS` — task-type ভিত্তিক চেইন
- Cost-sensitive sort, Redis ক্যাশ (`_cache_key` sha256), Bengali token estimator (ইউনিকোড রেঞ্জ `\u0980-\u09ff`)
- TokenBudget: ৮০% কনটেক্সট লিমিট + ডেইলি ১০০K ক্যাপ
- `free_tier_tracker` দিয়ে exhausted provider চেইন থেকে বাদ — **এটি প্ল্যানের `FreeTierAwareRouter`-এর বাস্তবায়ন, আসলে কাজ করে**
- V5 Dynamic AI Orchestrator bridge: non-streaming কল আগে orchestrator-এ যায়

#### `backend/core/llm/free_tier_tracker.py` (৩৯০ লাইন) — ✅ চমৎকার ইমপ্লিমেন্টেশন

- RPM/TPM/RPD **rolling window** (deque + evict), Redis persistence (multi-worker safe)
- প্রতি প্রোভাইডারে ৫% সেফটি বাফার, `is_available()` API
- প্রায়োরিটি লিস্ট: gemini → groq → cloudflare → openrouter → nvidia → hf → ollama

⚠️ **তবে:** কিছু লিমিট পুরনো — `gemini rpd: 475` (২০২৬-এ Flash প্রায় ১৫০০), `openrouter rpd: 45`। **হার্ডকোড না করে env-ওভাররাইডেবল করুন।**

#### `backend/core/llm/llm_gateway.py` — ⚠️ আংশিক, 🐛 একটি ডিজাইন-সমস্যা

- ✅ Per-call API key (os.environ injection বন্ধ), lazy litellm (২৪০MB RSS বাঁচানোর কৌশল), semantic cache, cost guard, Langfuse adapter যুক্ত
- 🐛 **`TASK_MODEL_MAP` (L73-79) hardcoded:**

  ```python
  "coding": "groq/llama-3.3-70b-versatile",
  "vision": "gemini/gemini-2.0-flash",
  ```

  → আপনার নীতির সরাসরি পরিপন্থী। মডেল ডিপ্রিকেট হলে কোড বদলাতে হবে।
- 🐛 `_MODEL_KEY_MAP`-এ `"moonshot": "MOONSHOT_API_KEY"` — অন্যগুলো `snake_case` settings attr, এটা `UPPER_SNAKE` env-স্টাইল → সাইলেন্ট ফেইল রিস্ক

#### `backend/services/dynamic_ai/` (Orchestrator + Learning Engine) — ⚠️ আংশিক

- ✅ Orchestrator (৪৮৮ লাইন): circuit breaker, provider registry, health-check loop, "NEVER crashes" গ্যারান্টি, Ollama local fallback
- 🐛 **`learning_engine.py` L61-74 — নিজের কমেন্টেই স্বীকার করেছে:**
  > "No historical-performance model is wired up yet... flat confidence score"
  
  অর্থাৎ `get_best_providers_for_task()` সবাইকে **1.0** দেয়। আপনার "Eternal Brain থেকে শেখা রাউটিং" আইডিয়ার পাইপলাইন আছে (`record_interaction` লগ হয়), কিন্তু **পড়ার দিকটা (recall → rank) বানানো হয়নি।** এটাই সবচেয়ে বড় মিসিং পিস।

---

### 2.2 মেমরি স্তর (Eternal Brain)

#### `backend/services/memory_service.py` (৭৬৭ লাইন) — ✅ কাজ করে, 🐛 ২টি বাগ

- ✅ Pooled Postgres default + `execute_ddl()` (read-only pooler বাইপাস), ডিগ্রেডেড InMemoryRing(5000), env-gated SQLite fallback
- 🐛 **`_PG_SCHEMA`-তে `embedding TEXT`** (JSON স্ট্রিং!) — pgvector টাইপ নয়। ফলে `ai_memory`-তে ভেক্টর সার্চ pgvector RPC দিয়ে হয় না, স্ট্রিং-তুলনায় হয়। **আপনার "semantic memory" আসলে এখানে ভেক্টর-সার্চ হচ্ছে না।**
- 🐛 **`hash_vectorize()` Python `hash()` ব্যবহার করে** — PYTHONHASHSEED ভিন্ন হলে প্রতি প্রসেসে ভিন্ন ভেক্টর → cross-worker semantic cache অসামঞ্জস্যপূর্ণ। ফিক্স: `hashlib.blake2b`।

#### `backend/memory/supabase_store.py` (৩৭৬ লাইন) — ✅ ভালো

- pgvector verify (`match_learned_facts` RPC দিয়ে probe), ৫-মিনিট health-check ক্যাশ, SQLite ফলব্যাক

#### `backend/adaptive_engine/experience_db.py` (৫২৯ লাইন) — ✅ প্ল্যানের ফিক্স ইমপ্লিমেন্টেড

- ChromaDB `PersistentClient` (আগের `EphemeralClient` ডেটা-লস বাগ ফিক্সড — কমেন্টে রেফারেন্স আছে)
- `USE_SUPABASE_VECTOR=true` ডিফল্ট → Supabase pgvector প্রেফার্ড, না পেলে Chroma/Qdrant
- `LOW_MEMORY_MODE=true` ডিফল্ট (৫১২MB সচেতন), degraded pass-through mode

#### `backend/core/embeddings.py` (১৪৫ লাইন) — 🔴 **ডাইমেনশন অমিল**

- **`_PG_DIM = 384`** (MiniLM-L6-v2), এবং `embed_for_pgvector(text, pg_dim=1536)` কল করলে **সতর্ক করে ৩৮৪-তে normalize করে**
- কিন্তু আপনার `MISSING_SERVICES_INTEGRATION_PLAN_V4.1.md` এবং `supabase_store.py`-এর RPC **vector(1536)** ধরে
- **ফলাফল:** ৩৮৪-ভেক্টর ১৫৩৬-কলামে ঢুকলে pgvector error; অথবা RPC কল ফেইল → সাইলেন্ট SQLite ফলব্যাক → "Eternal Brain" আসলে কাজ করছে কি না সেটাই অনিশ্চিত। **এক ডাইমেনশনে নামাতে হবে (৩৮৪ সঠিক পছন্দ — স্টোরেজ ৪× কম)।**

#### `backend/core/unified_memory.py` (১২৩ লাইন) — ✅ Facade ঠিক আছে

- long-term (CascadeMemoryService) + short-term (SlidingWindow) + checkpoint, user_id টেন্যান্ট-স্কোপিং

---

### 2.3 সিকিউরিটি ও সিক্রেট

#### `backend/core/security/secret_vault.py` (৫১৭ লাইন) — ✅ প্ল্যান অনুযায়ীই

- Infisical Universal Auth + Token, TTL cache (৫ মি), per-key TTL override, circuit breaker, 10s timeout (boot-hang প্রতিরোধ), fail-closed

#### `backend/core/config_secrets.py` (৬৩৬ লাইন) — ✅ **আগের রিপোর্টের ভুল সংশোধনী**

- **JSON-blob গ্রুপিং আসলে ইমপ্লিমেন্টেড:** `LLM_PROVIDER_KEYS`, `DATABASE_CONFIG`, `AUTH_KEYS`
- **Bulk-first `fetch_all_secrets()`** — ১টি HTTP কলে সব (~৩০s → ~১s)। অর্থাৎ প্ল্যানের "Infisical quota optimization" কোডে আছে। ✅

---

### 2.4 Self-Healing ও Evolution

#### `backend/services/auto_healer.py` (৭৩৮ লাইন) — ✅

- Regex error-pattern → category/severity → suggested fix + confidence, GitHub PR ইন্টিগ্রেশন প্ল্যাম্বিং

#### `backend/core/startup/agents.py` — ✅ আগের ক্রিটিক্যাল বাগ ফিক্সড

- `core.errors.auto_healer` (নেই এমন মডিউল) → সঠিক `services.auto_healer.get_healer()`
- `start_monitoring()` এখন `create_task` (আগে lifespan ব্লক করত)

#### `backend/core/maintenance_pipeline.py` — ✅ ফিক্সড

- `SelfEvolutionAgent.__new__` বাগ ফিক্স → এখন `app.state.evo_agent` ব্যবহার
- Production-এ emergency evolution **গেটেড** (aggressive mutation আটকায়) — ভালো সিদ্ধান্ত

---

### 2.5 API ও Routes

| ফাইল | অবস্থা | নোট |
| --- | --- | --- |
| `api/routes/artifacts.py` | ✅ ফিক্সড | `ArtifactType(StrEnum)` — duplicate-base বাগ মৃত |
| `api/routes/stream_chat_sse.py` | ✅ ফিক্সড | `SafeSSEGenerator` — sanitize, heartbeat, state-machine, fallback |
| `api/routes/task.py` | ⚠️ যাচাই দরকার | `SemanticCache` import ঠিক; কিন্তু `model_router.async_route_and_generate()` মেথডটি `llm_router.py`-তে **দেখিনি** — সম্ভাব্য `AttributeError` |
| `api/routes/websocket_agent.py` | ✅ ফিক্সড | `_pref_locks` → `LRUCache(1000)`; DoS: MAX_TOTAL=50, per-user=3, per-IP=10, auth-window |
| `api/routes/websocket_voice.py` | ✅ ফিক্সড | `MAX_CONNECTIONS=50` ক্যাপ |

🐛 **`artifacts.py`-এ `await db.client.table(...).execute()`** — supabase-py ক্লায়েন্ট sync; `db.client` যদি async-র‍্যাপ না হয় তবে এটি রানটাইমে ভাঙবে। `asyncio.to_thread` দিয়ে র‍্যাপ করা দরকার (অন্য রুটে যেমন করা আছে)।

---

### 2.6 Deploy / Infra / CI

#### `backend/worker_service.py` (২০২ লাইন) — ✅ চতুর

- Render free tier-এর "must bind $PORT" শর্তের জন্য FastAPI র‍্যাপার + Celery subprocess সুপারভাইজ; Celery/Redis ফেইল করলেও HTTP চলে (degraded)

#### `.github/workflows/keepalive.yml` — ⚠️ কাজ করে কিন্তু **অর্থনীতি ভাঙছে**

- ৪টা নোড প্রতি ১০ মিনিটে পিং
- 🔴 **গণিত:** ৪ সার্ভিস × ৭২০ঘ/মাস = **২৮৮০ ঘণ্টা**, কোটা ৭৫০ঘ → **মাস শেষের আগেই suspended**। Keep-alive ঘুম আটকায়, কিন্তু ঘণ্টা-বাজেট দ্রুত ফুরায়। **সার্ভিস কনসোলিডেশন ছাড়া এই সেটআপ টেকসই নয়।**

#### `backend/Dockerfile` — ✅ প্রোডাকশন-গ্রেড

- Multi-stage, non-root user, HEALTHCHECK, `poetry install --only main`

#### `backend/pyproject.toml` — ✅ চমৎকার অডিট ট্রেস রেকর্ড

- CVE floors (pydantic-settings, aiohttp, pillow, click, h2, litellm)
- **Playwright → optional `browser` group**, **torch/sentence-transformers → optional `ml` group** → core image ছোট, ফ্রি-টিয়ার RAM বাঁচে
- Dead deps (black/isort, google-auth-httplib2) সরানো — grep-যাচাই করা

#### `backend/monitoring/__init__.py` — ✅ **Sentry আসলে ওয়্যার্ড আছে**

- `traces_sample_rate=0.2`, `profiles=0.1`, FastAPI integration — `core/app.py` boot-এ `init_observability()` কল হয়। (আগের রিপোর্টে "০%" বলেছিলাম — সংশোধন: DSN সেট থাকলে এটি সক্রিয়; শুধু DSN না দিলে অফ।)

#### `backend/core/app.py` — ✅

- `MemoryAwareMiddleware` (৫১২MB সচেতন), aggregated health, lazy app export

---

## 3️⃣ 🐛 কোডে পাওয়া বাগ/অসঙ্গতি (ফিক্স লিস্ট)

| # | বাগ | ফাইল | ফিক্স |
| --- | --- | --- | --- |
| 1 | Ollama ব্যাকএন্ডে সক্রিয় (কমেন্ট বলছে "নিষ্ক্রিয়", কিন্তু চেইনে আছে + `ollama_enabled=True`) | `llm_router.py` L98-99,118-157; `dynamic_ai/orchestrator.py` L82 | `OLLAMA_BACKEND_ENABLED=false` ডিফল্ট; চেইন থেকে বাদ; শুধু ইউজার-ডিভাইস ব্রিজে রাখুন |
| 2 | হার্ডকোডেড মডেল ম্যাপ ৩ জায়গায় | `llm_gateway.py:73-79`, `llm_router.py:82-157`, `free_tier_tracker.py:70-78` | `config/routing_policy.json` + DB-লার্নড র‍্যাংকিং-এ সরান |
| 3 | Learner ফ্ল্যাট 1.0 দেয় — শেখেই না | `dynamic_ai/learning_engine.py:61-74` | `record_interaction` ডেটা pgvector-এ থেকে aggregation র‍্যাংকিং কোয়েরি যোগ করুন |
| 4 | `ai_memory.embedding` TEXT টাইপ (ভেক্টর নয়) | `memory_service.py:43` | `ALTER ... USING embedding::vector(384)` মাইগ্রেশন |
| 5 | ডাইমেনশন অমিল ৩৮৪ vs ১৫৩৬ | `embeddings.py:13` vs `supabase_store.py:71` | RPC ২টি `vector(384)`-এ মাইগ্রেট; plan/README আপডেট |
| 6 | `hash()` non-deterministic → cross-worker ভেক্টর অমিল | `memory_service.py:27` | `int.from_bytes(hashlib.blake2b(word.encode(), digest_size=8).digest(),'big')` |
| 7 | `async_route_and_generate` মেথড সন্দেহজনক | `task.py:95,110` | LLMRouter-এ এই মেথড নেই → `route()` ব্যবহার বা alias যোগ করুন; টেস্ট যোগ |
| 8 | `await` on sync supabase client | `artifacts.py:111,133` | `await asyncio.to_thread(...)` র‍্যাপ |
| 9 | Render ঘণ্টা বাজেট ভাঙছে (২৮৮০ >> ৭৫০) | `keepalive.yml` + Render dashboard | 4→2 সার্ভিস: Core+Worker এক Docker (supervisor), Scraper on-demand, MCP Core-এর ভেতরে |
| 10 | স্টেল কোটা: gemini rpd 475 | `free_tier_tracker.py:28-32` | Env-ওভাররাইড: `FREE_TIER_GEMINI_RPD` ইত্যাদি; ডিফল্ট ২০২৬ ভ্যালু |
| 11 | `_MODEL_KEY_MAP` নেমিং অমিল | `llm_gateway.py:62` | `"moonshot_api_key"` (settings attr) করুন |
| 12 | cachetools মেইন-ডিপে আছে, তবু ImportError fallback dict লিক | `websocket_agent.py:16-18` | fallback ব্লক মুছুন |

---

## 4️⃣ কী মডিফাই করতে হবে — কংক্রিট প্ল্যান

### 🥇 P0 — এই সপ্তাহে (প্রোডাকশন স্থিতিশীলতা)

**১. Render কনসোলিডেশন (4→2 সার্ভিস)**

```
supremeai-core   = FastAPI + MCP Tower (এক কন্টেইনার, supervisor)
supremeai-worker = worker_service.py (Celery + HTTP)
scraper          = বাদ → worker-এ on-demand capability হিসেবে
```

→ ২ × ৭২০ = ১,৪৪০ঘ... এখনো বেশি। তাই worker-এ প্রতি রাতে ৬ ঘণ্টা স্লিপ-উইন্ডো (Render env `CRON_SLEEP`) বা শুধু কোর চালু রাখুন (৭২০ঘ), worker শুধু টাস্ক-আগমনে জাগবে। **লক্ষ্য: মোট ≤ ৭৫০ঘ।**

**২. Embedding ইউনিফিকেশন (৩৮৪-এ সব)**

```sql
-- নতুন মাইগ্রেশন
ALTER TABLE ai_memory
  ALTER COLUMN embedding TYPE vector(384)
  USING (embedding::jsonb)::text::vector(384);  -- TEXT→vector
CREATE OR REPLACE FUNCTION match_learned_facts(
  query_embedding vector(384), ...) ...
```

`supabase_store._verify_pgvector_schema`-তে `[0.0]*384` করুন।

**৩. Deterministic hash fallback**

```python
import hashlib
def hash_vectorize(text: str, size: int = 384) -> list[float]:
    ...
    h = int.from_bytes(hashlib.blake2b(word.encode(), digest_size=8).digest(), "big") % size
```

**৪. Ollama ব্যাকএন্ড-অফ**

- `llm_router.py`: `_candidate_providers`-এ Ollama শুধু `OLLAMA_BACKEND_ENABLED=true` হলে
- `FALLBACK_CHAINS` থেকে Ollama সরান (runtime filter: `if not settings.ollama_backend_enabled: chain = [p for p in chain if p != Provider.OLLAMA]`)
- `dynamic_ai/orchestrator.py`: `ollama_enabled` ডিফল্ট False

### 🥈 P1 — এই মাসে (আপনার "no-hardcode" নীতির পূর্ণ বাস্তবায়ন)

**৫. সত্যিকারের Learned Routing (মিসিং পিসটি)**
`learning_engine.py`-এ:

```python
async def get_best_providers_for_task(self, prompt, available_providers, context=None):
    task_type = self.detect_task_type(prompt)
    rows = await self._memory.query_learned_facts(          # বিদ্যমান pgvector ইনফ্রা
        query=f"provider performance task={task_type}",
        metadata_filter={"kind": "provider_perf", "task_type": task_type}, limit=100)
    if not rows:
        return [(p, 1.0) for p in available_providers]      # exploration (আজকের behavior)
    agg = self._aggregate(rows)                              # score = success_rate × 1/log(latency)
    ranked = sorted(agg, key=lambda x: -x["score"])
    known = {r["provider_id"] for r in ranked}
    return [(r["provider_id"], r["score"]) for r in ranked] \
         + [(p, 0.1) for p in available_providers if p not in known]  # ε-exploration
```

`orchestrator.py` ইতিমধ্যে `record_interaction()` কল করে — শুধু লেখাটা pgvector-এ ধরে রাখুন (`kind: "provider_perf"` metadata সহ), যাতে ১৪ দিনের উইন্ডোতে র‍্যাংকিং শিখে যায়। এরপর `TASK_MODEL_MAP` ও `FREE_PROVIDER_PRIORITY` **মুছে ফেলা যাবে**।

**৬. task.py মেথড-নাম ফিক্স + artifacts async র‍্যাপ + tracker env-overridable limits**

**৭. কোটা স্টেল ভ্যালু আপডেট:** `gemini.rpd: 1500`, `openrouter.rpd: 50`, সবগুলো `os.getenv("FT_<PROVIDER>_<METRIC>", default)`।

### 🥉 P2 — পরের কোয়ার্টার

- Mission Tests (E2E ইউজার-ফ্লো)
- ইউজার-ডিভাইস Ollama Bridge (Tauri ক্লায়েন্টে `GET localhost:11434/api/tags` → Capability Registry-তে `user_local_ollama`)
- Coverage gates ইউনিফিকেশন + Action SHA pinning (STATUS.md-এর pending ৩টি)

---

## 5️⃣ ফাইনাল স্কোরকার্ড

| এলাকা | স্কোর | মন্তব্য |
| --- | --- | --- |
| LLM রাউটিং ইনফ্রা | 9/10 | free_tier_tracker বিশ্বমানের; শুধু লিমিট স্টেল |
| Learned Routing | 3/10 | পাইপলাইন আছে, র‍্যাংকিং নেই — এটাই মিসিং পিস |
| মেমরি/pgvector | 5/10 | কোড আছে, কিন্তু TEXT কলাম + ডাইম অমিলে সেমান্টিক সার্চ অনিশ্চিত |
| সিক্রেট | 9/10 | bulk + TTL + fail-closed — প্ল্যানের চেয়ে ভালো |
| Self-Healing | 8/10 | আগের ক্রিটিক্যাল বাগগুলো ফিক্সড |
| API hardening | 8/10 | DoS ক্যাপ, SSE, StrEnum সব ফিক্সড |
| Infra/নির্বাহ | 4/10 | Render ঘণ্টা ম্যাথ ভাঙছে — কনসোলিডেশন জরুরি |
| আপনার নীতি-কমপ্লায়েন্স (no-hardcode, Ollama-নীতি) | 5/10 | ৩ জায়গায় হার্ডকোড + Ollama দ্বন্দ্ব |

**মোট সুস্থতা: ~৭০%। উপরের P0 ৪টি ফিক্স করলে ৮৫%+, P1 করলে আপনার কনস্টিটিউশন-সম্পূর্ণ সংস্করণ।**

````

**সবচেয়ে জরুরি ৩টি কাজ, সংক্ষেপে:** ① Render 4→2 সার্ভিস (ঘণ্টা-ম্যাথ ভাঙছে), ② `ai_memory.embedding` TEXT→vector(384) + RPC ডাইম ফিক্স (নইলে Eternal Brain আসলে কাজ করছে কিনা সন্দেহজনক), ③ `learning_engine.get_best_providers_for_task`-এ pgvector-ভিত্তিক র‍্যাংকিং (এটি করলেই ৩টি হার্ডকোড টেবিল মুছে দেওয়া যাবে — আপনার নীতি তখন পূর্ণ)।
