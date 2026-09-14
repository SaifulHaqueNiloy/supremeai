```markdown
# 📊 SupremeAI Master Plan Analysis Report

**তারিখ:** ৪ সেপ্টেম্বর, ২০২৬
**সংস্করণ:** v1.1 (সংশোধিত — Tip 5 ও Tip 7 কনস্টিটিউশন-সামঞ্জস্যপূর্ণ করা হয়েছে)
**রিপোজিটরি:** github.com/SaifulHaqueNiloy/supremeai (main ব্রাঞ্চ, ৯৪৮ কমিট)
**বিশ্লেষক মোড:** কোডবেস অডিট + মাস্টার প্ল্যান রিভিউ + ফ্রি-টিয়ার অপটিমাইজেশন

> **v1.1 সংশোধনী নোট:**
> - **Tip 5 (পুরনো):** "Ollama কে Dev Fallback বানান" — ❌ বাতিল। SupremeAI Cloud-এ Ollama চলবে না।
> - **Tip 5 (নতুন):** User-Local Ollama Bridge — ইউজারের ডিভাইসে Ollama থাকলে তবেই ব্যবহার, Capability Discovery-র মাধ্যমে অটো-ডিটেক্ট। ব্যাকএন্ড প্রেসার কমানোর কৌশল।
> - **Tip 7 (পুরনো):** "Groq-কে Primary Fast Inference বানান" — ❌ বাতিল। এটি Hardcoded সিদ্ধান্ত, যা কনস্টিটিউশনের "Dynamic Discovery over brittle hard-coded inventories" নীতির পরিপন্থী।
> - **Tip 7 (নতুন):** Dynamic Model Performance Learning — সিস্টেম বাস্তব পারফরম্যান্স ডেটা থেকে শিখবে কোন মডেল কোন কাজে সেরা।

---

## 🎯 Executive Summary (এক্সিকিউটিভ সারসংক্ষেপ)

**সরাসরি উত্তর: হ্যাঁ, আপনার মাস্টার প্ল্যানটি কার্যকর — তবে এটি বর্তমানে প্রায় ৪০% বাস্তবায়িত, ৩৫% আংশিক, এবং ২৫% শুধু কাগজে-কলমে আছে। প্ল্যানে ৬টি বড় গ্যাপ চিহ্নিত হয়েছে এবং ফ্রি-টিয়ার থেকে সর্বোচ্চ সুবিধা পেতে ১২টি অ্যাকশনেবল টিপস দেওয়া হলো।**

আপনার প্রজেক্টের ভিশন — "Capability Before Construction" ও "Eternal Brain" — সত্যিই চিন্তাশীল ও দীর্ঘমেয়াদি। তবে `MISSING_SERVICES_INTEGRATION_PLAN_V4.1.md` এ বর্ণিত অনেক সার্ভিস এখনো "Configure হয়েছে কিন্তু Production-এ সক্রিয় নয়" অবস্থায় আছে। বিশেষ করে **Sentry Performance (০%), Cloudflare Workers (০.১৮%), Codespaces (০%)** কার্যত অব্যবহৃত। নিচে বিস্তারিত।

---

## 1️⃣ কোডবেস ওভারভিউ (Codebase Overview)

### ১.১ প্রযুক্তি স্ট্যাক (README.md অনুযায়ী)

| লেয়ার | প্রযুক্তি | বর্তমান অবস্থা |
|---|---|---|
| Frontend | React 19 + TypeScript + Vite 7 | ✅ সক্রিয় (MultiWorkspace) |
| Core API | Python 3.11 + FastAPI + Async SQLAlchemy 2.0 | ✅ সক্রিয় (Render Docker) |
| Database | PostgreSQL + pgvector (Supabase) | ✅ সক্রিয় (৩৬% ব্যবহৃত) |
| Cache/Queue | Redis / Upstash | ✅ সক্রিয় |
| LLM Gateway | Gemini, Groq, OpenRouter, Ollama | ✅ ফলব্যাক চেইন সক্রিয় |
| Browser | Playwright + Chromium | ✅ সক্রিয় (Scraping Node) |
| MCP Tower | Node.js MCP Server | ✅ সক্রিয় |
| Edge | Cloudflare Worker (Keep-Alive Cron) | ⚠️ ৪-নোড `*/8` ক্রন চলছে, কিন্তু ০.১৮% ব্যবহৃত |
| Hosting | Firebase Hosting | ✅ সক্রিয় |
| CI/CD | GitHub Actions + GHCR | ✅ সক্রিয় (৯৪৮ কমিট) |
| Secrets | Infisical | ⚠️ ৮৩% ক্যাপাসিটি ব্যবহৃত |
| Thin Clients | Tauri/Electron Desktop + VS Code Ext | ✅ Ready (Zero Key Exposure) |

### ১.২ বর্তমান অবস্থা (STATUS.md অনুযায়ী)

- **Active Phase:** Phase 3 — Self-Evolving & Multi-Agent Swarm
- **Production Readiness:** লোকাল Docker ক্লাস্টারে Verified; ক্লাউডে লাইভ
- **মোট কমপ্লিটেড মাইলস্টোন:** ১৫টি (AutoHealer, DB Indexing, HITL Ledger, ডিজাইন সিস্টেম ইত্যাদি)
- **High-Priority Pending:** ৩টি — Supabase `ai_memory` ভেরিফিকেশন, CI Coverage Gates, Action SHA Pinning

### ১.৩ Production Readiness Plan V3 যা বলছে

আপনার নিজের অডিটেই ধরা পড়েছে:
- **১৫টি Critical Bug** (যেমন `class ArtifactType(str, str)` duplicate base, ৭টি মিসিং `await`)
- **১০টি Performance Issue** (WebSocket unbounded connections, `_pref_locks` মেমরি লিক, per-request `httpx.AsyncClient`)
- **১০টি Dead Code আইটেম**
- **৪টি Capability Gap** (Ephemeral ChromaDB → রিস্টার্টে সব লার্নিং হারিয়ে যায়)

এটি প্রমাণ করে যে **প্ল্যান লেখা হয়েছে ঠিকঠাক, কিন্তু Execution-এর ছিদ্র এখনো আছে।**

---

## 2️⃣ মাস্টার প্ল্যান রিভিউ (Master Plan Review)

আপনার `MISSING_SERVICES_INTEGRATION_PLAN_V4.1.md` পাঁচটি কলামে সাজানো:

### ২.১ 🏛️ Infisical Secrets Vault — ⭐⭐⭐⭐⭐
- ✅ **Implementation Ready:** `backend/core/security/secret_vault.py`-তে TTL Cache, Circuit Breaker, Fail-Closed সবই লেখা
- ⚠️ **সমস্যা:** ২৫/৩০ সিক্রেট ব্যবহৃত (৮৩%) — প্রায় লিমিটে
- ✅ **প্ল্যানে সমাধান আছে:** সিক্রেটগুলো JSON Blob-এ গ্রুপ করে ~১০টিতে নামানো
- ⚠️ **Gap:** প্ল্যানে লেখা আছে কিন্তু `OptimizedSecretLoader` ক্লাসটি এখনো কোডে ইন্টিগ্রেট হয়নি

### ২.২ 💻 IDE Trio Pipeline (Gemini → Kilo → Cline) — ⭐⭐⭐⭐
- ✅ **Config সম্পূর্ণ:** `.env.example`, `.kiloignore`, `.clineignore` সব আছে
- ✅ **GeminiWriter কোড লেখা আছে** — rate limiter সহ
- ⚠️ **Gap:** Stage 2 (Kilo Reviewer) ও Stage 3 (Cline Checker)-এর `GuardianAgent` ইন্টিগ্রেশন এখনো placeholder (`return []`)
- ⚠️ **Bengali Compliance Check** আছে, কিন্তু এটি LLM-based নয় — শুধু কীওয়ার্ড ম্যাচিং

### ২.৩ 🧠 Supabase pgvector Eternal Brain — ⭐⭐⭐⭐⭐
- ✅ **Schema সম্পূর্ণ:** `ai_memory` (1536-dim) + `learned_facts` + `match_learned_facts` RPC
- ✅ **Local Embedding:** `all-MiniLM-L6-v2` (384-dim) → zero-pad করে 1536 — চতুর কৌশল, cosine similarity প্রিজার্ভ হয়
- ✅ **Retention Policy প্ল্যান করা:** CRITICAL=365d, EPHEMERAL=7d
- ⚠️ **Gap:** `MemoryRetentionPolicy.prioritize_and_prune()` কোডে আছে, কিন্তু **ডেইলি cron হিসেবে শিডিউল করা হয়নি**
- ⚠️ **Hidden Risk:** প্ল্যানে উল্লেখ নেই যে **Supabase Free Tier ৭ দিন ইনঅ্যাক্টিভিটির পর পজ হয়ে যায়**

### ২.৪ 📡 Sentry Observability — ⭐⭐⭐
- ✅ **Error Bus System** (`intelligent_silent_catcher.py`) লেখা আছে
- ✅ **Sentry Init Code** আছে (DSN-based)
- 🔴 **Gap:** `SENTRY_DSN` configured কিন্তু **Performance/APM ০%** — `traces_sample_rate` সেট হয়নি
- 🔴 **Gap:** `Langfuse` (LLM-specific tracing) ডায়াগ্রামে আছে কিন্তু **কোনো ইন্টিগ্রেশন কোড নেই**

### ২.৫ 🤖 Multi-Model AI (১০+ Providers) — ⭐⭐⭐⭐⭐
- ✅ **Provider Enum:** Gemini, Groq, HF, Ollama, DeepSeek, OpenAI, Moonshot, Together, NVIDIA, OpenRouter
- ✅ **Smart Router প্ল্যান:** Complexity Score (0-100) → ECONOMY/STANDARD/PREMIUM/ULTRA
- ✅ **HF Swarm:** ৭টি কাস্টম মডেল
- 🔴 **Gap:** `FreeTierAwareRouter` ক্লাস প্ল্যানে আছে, কিন্তু `_call_provider` এখনো **Mock**
- 🔴 **Gap:** প্ল্যানে `groq: 14400/day` hardcoded — ২০২৬-এ Groq এর বাস্তব লিমিট ৩০ RPM; এছাড়া **কোনো মডেল কোন কাজে ভালো — এই ম্যাপিংও hardcoded**, যা কনস্টিটিউশনের নীতির পরিপন্থী (সমাধান: Tip 7)

---

## 3️⃣ গ্যাপ অ্যানালাইসিস (Gap Analysis) — ৬টি বড় ফাঁক

### 🔴 Gap 1: "Aspirational vs Implemented" ফাঁক

| সার্ভিস | প্ল্যানে টার্গেট | বর্তমান ব্যবহার |
|---|---|---|
| Sentry Performance | 50% | **০%** 🔴 |
| Cloudflare Workers | 40% | **০.১৮%** 🔴 |
| GitHub Codespaces | 50% | **০%** 🔴 |
| Render Hours | 45% | **৬৯%** ⚠️ (ওভার-ইউজ) |
| Langfuse | Active | **Absent** 🔴 |

**কারণ:** প্ল্যান লেখা হয়েছে, কিন্তু **"Activation PR"** মার্জ হয়নি।

### 🔴 Gap 2: Render Free Tier Sleep + 69% Hour Usage
- Render Free Tier: **৭৫০ ঘণ্টা/মাস**, ১৫ মিনিট আইডলে Sleep
- ৪টি সার্ভিস × ২৪ ঘণ্টা × ৩০ দিন = **২,৮৮০ ঘণ্টা দরকার**, আছে ৭৫০
- **প্ল্যানে গ্যাপ:** কোনো কনক্রিট "Service Consolidation" প্ল্যান নেই

### 🔴 Gap 3: Supabase ৭-দিন Inactivity Pause (প্ল্যানে উল্লেখই নেই)
- ৭ দিন ডেটাবেস অ্যাক্টিভিটি ছাড়া থাকলে Supabase প্রজেক্ট পজ হয়ে যায়
- Eternal Brain (`ai_memory`) নিস্ক্রিয় থাকলে পুরো মেমরি সিস্টেম অচল
- **প্ল্যানে গ্যাপ:** এই রিস্কের কোনো মেনশন নেই

### 🔴 Gap 4: Multi-Account Resource Pooling এর টুথলেস প্ল্যান
- "Multi-account pools" আর্কিটেকচারে আছে, কিন্তু API Key Rotation, IP বাইন্ডিং, ToS কমপ্লায়েন্স — কোনো কনক্রিট গাইড নেই
- **রিস্ক:** ভুলভাবে করলে প্রোভাইডার অ্যাকাউন্ট ব্যান হতে পারে

### 🔴 Gap 5: Browser Automation এর রিসোর্স বাস্তবতা
- Render Free Tier: **৫১২ MB RAM, 0.1 CPU**
- Playwright + Chromium নিজেই ~৩০০-৪০০ MB RAM খায় → OOM অনিবার্য
- **সমাধান প্ল্যানে নেই:** Cloudflare Browser Rendering API বা Cloudflare Tunnel দিয়ে বাহ্যিক এক্সিকিউশন

### 🔴 Gap 6: Hardcoded মডেল-টাস্ক ম্যাপিং (নতুন সংযোজন)
- প্ল্যানে রাউটারের candidate list hardcoded: `[0-30] → Gemini, Groq, Ollama...`
- এটি কনস্টিটিউশনের **"Dynamic Discovery"** ও **"Memory Must Compound"** নীতির পরিপন্থী
- মডেল পরিবর্তন হলে (নতুন ভার্সন, নতুন কোটা, নতুন শক্তি) কোড বদলাতে হবে — সিস্টেম নিজে শিখবে না
- **সমাধান:** Tip 7 দেখুন

---

## 4️⃣ ফ্রি-টিয়ার প্রো টিপস (Free Tier Pro Tips) — ১২টি অ্যাকশনেবল

### 🥇 Tip 1: Render ঘণ্টা বাঁচান — Service Consolidation
**সমস্যা:** ৪টি আলাদা Render সার্ভিস = ৪× ঘণ্টা খরচ
**সমাধান:** একটি Dockerfile-এ Core + Worker একসাথে (Supervisor দিয়ে), Scraper আলাদা।
**ফলাফল:** ৪ সার্ভিস → ২ সার্ভিস = ৭৫০ ঘণ্টা যথেষ্ট।

```yaml
# render.yaml (snippet)
services:
  - type: web
    name: supremeai-combined
    env: docker
    dockerCommand: "./start-combined.sh"
```

### 🥈 Tip 2: Cloudflare Workers কে Edge Gateway বানান (০.১৮% → ৪০%)

- **Request Router:** `/api/*` Render-এ প্রক্সি, ক্যাশেবল GET রেসপন্স CF Edge-এ ক্যাশ
- **DDoS Protection + Rate Limiting:** ফ্রি টিয়ারে বিল্ট-ইন
- **Cloudflare KV** দিয়ে Session Cache

```javascript
// Cloudflare Worker
export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (request.method === "GET" && url.pathname.startsWith("/api/cacheable")) {
      const cached = await env.CACHE_KV.get(url.pathname);
      if (cached) return new Response(cached);
    }
    // Proxy to Render...
  }
}
```

### 🥉 Tip 3: Supabase ৭-দিন Pause ঠেকাতে GitHub Actions Cron

```yaml
# .github/workflows/supabase-keepalive.yml
name: Supabase Keep-Alive
on:
  schedule:
    - cron: "0 6 * * *"
jobs:
  ping:
    runs-on: ubuntu-latest
    steps:
      - run: |
          curl -X POST "${{ secrets.SUPABASE_URL }}/rest/v1/rpc/ping" \
            -H "apikey: ${{ secrets.SUPABASE_ANON_KEY }}"
```

### 💡 Tip 4: Multi-Account LLM Pooling (নিরাপদভাবে)

একাধিক Google Cloud Project খুলে আলাদা `GEMINI_API_KEY` (ToS-safe):

- প্রতি প্রজেক্ট: ১,৫০০ RPD (Flash) → ৫ প্রজেক্ট = ৭,৫০০ RPD ফ্রি

```python
class GeminiPool:
    def __init__(self, keys: list[str]):
        self.keys = keys
        self._quotas = {k: ProviderQuota(k, 1500, 0, ...) for k in keys}

    async def get_key(self) -> str:
        # কম ব্যবহৃত available key নির্বাচন (dynamic, hardcoded নয়)
        available = [k for k, q in self._quotas.items() if q.status == "available"]
        return min(available, key=lambda k: self._quotas[k].used_today)
```

### 💡 Tip 5 (সংশোধিত): User-Local Ollama Bridge — ইউজারের ডিভাইস হোক ক্যাপাসিটি প্রোভাইডার

**মূলনীতি:** SupremeAI Cloud কখনোই ধরে নেবে না যে Ollama আছে। Ollama একটি **ইউজার-অনুমোদিত লোকাল ক্যাপাসিটি**, যা Capability Discovery-র মাধ্যমে অটো-ডিটেক্ট হয়। এটি আপনার README-র এই লাইনের সরাসরি বাস্তবায়ন:
> *"User-authorized external capabilities"* — Capability Surface-এর একটি স্তর।

**কেন শক্তিশালী:**

- ইউজারের লোকাল ইনফারেন্স = **Cloud-এর কোনো LLM কোটা খরচ হয় না**
- Render-এর কম্পিউটে কোনো চাপ পড়ে না (ইনফারেন্স ইউজারের CPU/GPU-তে হয়)
- ইউজারের ডেটা তার নিজের ডিভাইসেই থাকে — Privacy সুবিধা
- ইন্টারনেট বিচ্ছিন্ন হলেও (Ollama লোকাল) সিস্টেম আংশিক কাজ করবে — আপনার "Graceful Degradation" নীতির সাথে সামঞ্জস্যপূর্ণ

**আর্কিটেকচার (আপনার বিদ্যমান Thin Client-এর সুবিধা নিয়ে):**

```
┌──────────────────────────────────────┐
│ ইউজারের ডিভাইস                        │
│  ┌────────────────┐  ┌────────────┐  │
│  │ SupremeAI      │  │  Ollama    │  │
│  │ Desktop (Tauri)│─▶│ :11434     │  │
│  │ / VS Code Ext  │  │ (লোকাল)    │  │
│  └───────┬────────┘  └────────────┘  │
└──────────┼───────────────────────────┘
           │ ১. Ollama ডিটেক্ট: GET localhost:11434/api/tags
           │ ২. Capability রেজিস্ট্রেশন (ইউজারের অনুমতি নিয়ে)
           ▼
┌──────────────────────────────────────┐
│ SupremeAI Cloud (Render)             │
│  Capability Registry:                │
│  { id: "user_local_ollama",          │
│    owner: user_id,                   │
│    type: "llm",                      │
│    scope: "user-only",               │
│    online: bool }                    │
│                                      │
│  Router: সহজ টাস্ক + ইউজারের         │
│  নিজের অনুরোধ → user_local_ollama    │
│  বাকি সব → ক্লাউড প্রোভাইডার          │
└──────────────────────────────────────┘
```

**ডিটেকশন কোড (Desktop Client-এ):**

```typescript
// Tauri/Desktop ক্লায়েন্টে — ইউজারের সম্মতির পরেই চলবে
async function discoverLocalOllama(): Promise<LocalCapability | null> {
  try {
    const res = await fetch("http://localhost:11434/api/tags", {
      signal: AbortSignal.timeout(2000),
    });
    if (!res.ok) return null;
    const data = await res.json();
    return {
      id: "user_local_ollama",
      type: "llm",
      models: data.models?.map((m: any) => m.name) ?? [],
      scope: "user-only",       // শুধু এই ইউজারের টাস্ক
      registeredAt: Date.now(),
    };
  } catch {
    return null; // Ollama নেই — কিছুই করবে না, ক্লাউড স্বাভাবিক চলবে
  }
}
```

**ক্লাউড-সাইড রাউটিং নিয়ম (Dynamic, Hardcoded নয়):**

- Capability Registry-তে `user_local_ollama` **অনলাইন** থাকলে এবং টাস্কটি ইউজারের নিজের হলে → লোকালে পাঠানোর **প্রস্তাব** দেখাও (HITL-সামঞ্জস্যপূর্ণ)
- লোকাল কল fail/timeout হলে → স্বয়ংক্রিয়ভাবে ক্লাউড ফলব্যাক ("No Silent Failure")
- Ollama অফলাইন হলে Registry থেকে `online: false` মার্ক হবে

**ফলাফল:** ব্যাকএন্ড প্রেসার ↓, LLM কোটা সাশ্রয় ↑, ইউজার Privacy ↑ — এবং কোনো Hardcoded Assumption নেই।

### 💡 Tip 6: HuggingFace Serverless Inference — বাস্তব সীমা বুঝুন

- **Cold Model Loading ৩০-৬০ সেকেন্ড** লাগে — রিয়েল-টাইম কাজে অনুপযুক্ত
- **Tip:** শুধু আপনার **নিজের কাস্টম মডেল** (supreme-coder-3b ইত্যাদি) এর জন্য ব্যবহার করুন, ব্যাচ/অ্যাসিঙ্ক টাস্কে
- সিদ্ধান্ত নেবেন না আগে থেকে — Tip 7-এর Learner নিজেই বলবে HF কোন টাস্কে মূল্যবান কি না

### 💡 Tip 7 (সংশোধিত): Dynamic Model Performance Learning — কোনো Hardcoded Routing নয়

**মূলনীতি:** "কোন মডেল কোন কাজে ভালো" — এই সিদ্ধান্ত **কেউ কোডে লিখবে না।** সিস্টেম নিজেই প্রতিটি কলের বাস্তব ফলাফল পরিমাপ করে, Eternal Brain-এ জমা রাখে, এবং সেই ডেটা থেকে রাউট করে। এটি আপনার কনস্টিটিউশনের সরাসরি বাস্তবায়ন:
> *"Memory Must Compound: Task → Result → Experience → Memory → Better Future Planning"*

**বর্তমান সমস্যা (আপনার প্ল্যানে):**

```python
# ❌ বর্তমান (hardcoded candidate lists):
if complexity_score <= 30:
    return ['ollama', 'gemini', 'groq', 'huggingface']  # কেন? কে বলল?
```

**সমাধান: `ModelPerformanceLearner`**

```python
# backend/services/llm/performance_learner.py
"""
Dynamic Model Performance Learner
কোনো মডেল-টাস্ক ম্যাপিং hardcoded থাকবে না।
প্রতিটি LLM কলের বাস্তব ফলাফল পরিমাপ → Eternal Brain-এ জমা →
পরবর্তী রাউটিং সিদ্ধান্ত সেই ডেটা থেকে।
"""
class ModelPerformanceLearner:
    async def record_outcome(
        self,
        task_type: str,          # runtime-এ শ্রেণীবদ্ধ, hardcoded নয়
        provider: str,
        model: str,
        latency_ms: float,
        tokens_in: int,
        tokens_out: int,
        success: bool,
        quality_score: float | None,  # verifiable টাস্কে স্বয়ংক্রিয় স্কোর
    ):
        """প্রতিটি কলের পর একবার কল হবে — llm_gateway থেকে"""
        fact = (
            f"model_performance: task={task_type} provider={provider} "
            f"model={model} latency_ms={latency_ms:.0f} success={success} "
            f"quality={quality_score} at {datetime.utcnow().isoformat()}"
        )
        await self.memory.store_learned_fact(   # আপনার বিদ্যমান learned_facts + pgvector
            fact_text=fact,
            embedding=self.embedder.embed_text(fact),
            metadata={
                "kind": "model_performance",
                "task_type": task_type,
                "provider": provider,
                "model": model,
                "latency_ms": latency_ms,
                "success": success,
                "quality": quality_score,
                "window": "recent",
            },
        )

    async def recommend_models(self, task_type: str, k: int = 3) -> list[dict]:
        """
        মেমরি থেকে historical best performers — কোনো hardcoded তালিকা নেই।
        ডেটা না থাকলে → exploration mode (সব available প্রোভাইডারে সমান সুযোগ,
        ফলাফল রেকর্ড হবে; কয়েকদিনেই সিস্টেম শিখে যাবে)।
        """
        results = await self.memory.query_learned_facts(
            query=f"model performance for task {task_type}",
            metadata_filter={"kind": "model_performance", "task_type": task_type},
            limit=50,
        )
        if not results:
            return []  # exploration mode চালু হবে
        # সাম্প্রতিক ডেটার weighted score: success × quality ÷ latency
        scored = self._aggregate_recent(results, window_days=14)
        return sorted(scored, key=lambda s: s["score"], reverse=True)[:k]
```

**রাউটার ইন্টিগ্রেশন (আপনার বিদ্যমান `smart_model_router`-এ):**

```python
async def route_request(self, task, complexity_score: int):
    task_type = await self.classifier.detect(task)          # runtime শ্রেণীবদ্ধ
    learned = await self.learner.recommend_models(task_type)
    candidates = (
        [m["model"] for m in learned]                       # ১. শেখা ডেটা আগে
        or await self.registry.list_available()             # ২. না থাকলে exploration
    )
    # প্রতিটি প্রচেষ্টার ফলাফল learner-এ ফিডব্যাক — লুপ বন্ধ
    for candidate in candidates:
        result = await self.try_provider(candidate, task)
        await self.learner.record_outcome(task_type, candidate, result)
        if result.success:
            return result
    return self.degrade_gracefully(task)                    # Honest failure
```

**Quality Score যেভাবে আসবে (verifiable টাস্কে, বাড়তি LLM খরচ ছাড়া):**

- কোড জেনারেশন → সিনট্যাক্স পার্স + টেস্ট পাস (আপনার IDE Trio Stage 3 ইতিমধ্যে এটা করে!)
- সামারাইজেশন → আউটপুট দৈর্ঘ্য/কাঠামো হিউরিস্টিক + ইউজার রেটিং
- Retrieval/RAG → সাইটেশন হিট রেট
- অন্যান্য → latency + success rate যথেষ্ট সিগনাল

**সুবিধা:**

- মডেল আপডেট/নতুন প্রোভাইডার এলে **কোড বদলাতে হবে না** — সিস্টেম ১-২ দিনে নতুন ডেটা শিখে নেবে
- কোটা শেষ হলে স্বয়ংক্রিয়ভাবে পরবর্তী সেরা বিকল্পে যাবে (আপনার "Graceful Degradation")
- "পুরনো ধারণা" নিজেই মুছে যাবে — Retention Policy পুরনো পারফরম্যান্স ফ্যাক্ট prune করবে
- Groq, Gemini, HF — **কোনোটাই বিশেষ মর্যাদা পাবে না**; যে ডেটায় সেরা, সে-ই জিতবে

### 💡 Tip 8: Vercel vs Firebase Hosting (ফ্রন্টএন্ডের জন্য)

- **Vercel Hobby:** Unlimited Static, ১০০ GB ব্যান্ডউইথ, Preview Deployments (ফ্রি)
- **Firebase Hosting:** ১০ GB ব্যান্ডউইথ — কম
- **Tip:** এখনই Firebase থাকুক; ট্রাফিক বাড়লে মাইগ্রেশন ভাবুন

### 💡 Tip 9: Cloudflare R2 — Artifacts স্টোরেজ (১০ GB ফ্রি, Egress ফ্রি)

- `artifacts` ফাইল R2-তে রাখুন
- ১০ GB ফ্রি, **কোনো Egress Fee নেই**
- Render-এর ephemeral disk সমস্যার স্থায়ী সমাধান

### 💡 Tip 10: Upstash Redis Free Tier সঠিকভাবে ব্যবহার

- **১০,০০০ Commands/দিন** ফ্রি
- ব্যবহার: Session Cache, Rate Limiting, Distributed Lock, Semantic Cache
- **সাবধান:** Keyspace Notification চালু করলে দ্রুত কোটা শেষ হয়

### 💡 Tip 11: Modal/Replicate/Together ফ্রি ক্রেডিট

ভারী টাস্কের জন্য (3D Model, Video, Heavy Compute):

- **Modal:** $৩০/মাস ফ্রি ক্রেডিট
- **Replicate:** নতুন অ্যাকাউন্টে ফ্রি ট্রায়াল
- **Together AI:** $২৫ ফ্রি ক্রেডিট
- আপনার `Burst Compute` লেয়ারে এগুলো যোগ করুন — কিন্তু এগুলোও Tip 7-এর Learner-এর মাধ্যমেই মূল্যায়িত হবে

### 💡 Tip 12: Langfuse Self-Hosted (LLM Observability)

- **Option A:** Langfuse Cloud ফ্রি (১০K observations/মাস)
- **Option B:** Self-host on Render — সম্পূর্ণ ফ্রি, সীমাহীন
- **বোনাস:** Langfuse-এর ট্রেস ডেটাই Tip 7-এর Learner-এর ইনপুট হতে পারে (provider latency, token usage)

```python
from langfuse import Langfuse
langfuse = Langfuse()

# LLM কলের পর:
langfuse.trace(
    name="chat_completion",
    input=prompt,
    output=response,
    metadata={"provider": provider, "model": model, "latency_ms": latency},
)
```

---

## 5️⃣ প্রায়োরিটি অ্যাকশন আইটেম (Priority Action Items)

### 🔴 এই সপ্তাহে (This Week)

| # | অ্যাকশন | সময় | Impact |
| --- | --- | --- | --- |
| 1 | Render সার্ভিস কনসোলিডেশন (4→2) | ২ ঘণ্টা | ৭৫০ ঘণ্টা বাঁচবে |
| 2 | Supabase Keep-Alive GitHub Action | ১৫ মিনিট | ৭-দিন Pause ঠেকাবে |
| 3 | Sentry `traces_sample_rate=0.5` চালু | ১০ মিনিট | ২০K ট্রানজ্যাকশন ফ্রি |
| 4 | Infisical Secrets JSON-এ গ্রুপ | ৩০ মিনিট | ৮৩% → ৫০% |
| 5 | `ModelPerformanceLearner`-এর ভিত (record_outcome + pgvector) | ২ ঘণ্টা | Hardcoded রাউটিং দূর হবে |

### 🟡 এই মাসে (This Month)

| # | অ্যাকশন | সময় |
| --- | --- | --- |
| 6 | Learner ↔ Router সম্পূর্ণ ইন্টিগ্রেশন + Exploration Mode | ৩ ঘণ্টা |
| 7 | User-Local Ollama Bridge (Desktop Client ডিটেকশন + Registry) | ৪ ঘণ্টা |
| 8 | Langfuse Self-Host ডিপ্লয় | ২ ঘণ্টা |
| 9 | CF Worker কে Edge Gateway বানানো | ৪ ঘণ্টা |
| 10 | Cloudflare R2 দিয়ে Artifact Storage | ২ ঘণ্টা |
| 11 | `MemoryRetentionPolicy` ডেইলি ক্রন শিডিউল | ১ ঘণ্টা |

### 🟢 দীর্ঘমেয়াদি (Next Quarter)

| # | অ্যাকশন |
| --- | --- |
| 12 | Browser Automation কে Cloudflare Browser Rendering-এ মাইগ্রেট |
| 13 | Mission Tests — এন্ড-টু-এন্ড ইউজার ফ্লো টেস্ট |
| 14 | Production Readiness Plan V3-এর ১৫টি Critical Bug Fix |
| 15 | Learner-এর ডেটা দিয়ে মাসিক "Model Report Card" জেনারেশন |

---

## 6️⃣ চূড়ান্ত মূল্যায়ন (Final Verdict)

### ✅ প্ল্যান যা ঠিক আছে

1. **Capability Composition Model** — "Reuse before Create" দর্শন প্রফেশনাল
2. **Multi-Provider Abstraction** — Vendor Lock-in মুক্ত
3. **Local-first Embedding (MiniLM + zero-pad)** — চতুর কৌশল
4. **Governance (HITL + RBAC + Audit)** — Enterprise-grade চিন্তা
5. **ডকুমেন্টেশন সংস্কৃতি** — `AGENTS.md`, `STATUS.md`, `LESSONS_LEARNED.md`
6. **Thin Client স্থাপত্য** — Tip 5-এর Ollama Bridge-এর জন্য পারফেক্ট ভিত ইতিমধ্যেই আছে

### ⚠️ প্ল্যান যা দুর্বল

1. **Aspiration vs Implementation Gap** — অনেক কিছু "configured" কিন্তু "active" নয়
2. **Resource Reality Check নেই** — Render-এর ৫১২ MB RAM-এ Chromium চলবে না
3. **Supabase ৭-দিন Pause Risk** — সম্পূর্ণ উপেক্ষিত
4. **Quota মিথ:** Groq ১৪,৪০০/day ধরা হয়েছে, বাস্তবে ৩০ RPM
5. **Hardcoded মডেল-টাস্ক ম্যাপিং** — নিজের কনস্টিটিউশনের "Dynamic Discovery" নীতির পরিপন্থী (Tip 7 সমাধান)
6. **User-Local Capability প্ল্যানে অব্যবহৃত** — ইউজারের ডিভাইস (Ollama) ক্যাপাসিটি প্রোভাইডার হিসেবে ব্যবহারের পরিকল্পনা নেই (Tip 5 সমাধান)

### 🎯 শেষ কথা

আপনার মাস্টার প্ল্যান **স্বপ্ন দেখার জন্য চমৎকার, Execution-এর জন্য ৬০% প্রস্তুত।** উপরের ১২টি টিপস বাস্তবায়ন করলে আপনি মাসে **$0-১০** খরচে একটি Production-Ready AI Platform চালাতে পারবেন। সবচেয়ে গুরুত্বপূর্ণ দুটি স্থাপত্যিক সিদ্ধান্ত:

1. **Tip 7 (Performance Learner):** সিস্টেম যেন ডেটা থেকে শেখে, কোড থেকে নয় — এটিই "Eternal Brain" দর্শনের প্রকৃত প্রমাণ।
2. **Tip 5 (User-Local Bridge):** ইউজারের ডিভাইসই হোক প্রথম ক্যাপাসিটি প্রোভাইডার — ক্লাউড খরচ ন্যূনতম, Privacy সর্বোচ্চ।

> **"The compounding capability graph — not the number of individual services — is the real product."**
> — আপনার নিজের README থেকে। এই গ্রাফে এখন নতুন দুটি নোড যুক্ত হলো: **ইউজারের ডিভাইস** এবং **সিস্টেমের নিজস্ব শেখা ডেটা**।

---
