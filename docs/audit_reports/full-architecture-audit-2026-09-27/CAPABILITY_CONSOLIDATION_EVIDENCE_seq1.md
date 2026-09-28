# Capability Consolidation Evidence — seq:1 (#2427)

> **তারিখ:** 2026-09-28 · **এজেন্ট:** agent-3 (supremeai-coder-1-bot) · **বেস:** main @ `bacc31a`
> **Golden Invariant (Zero Capability Loss):** কোনো কোড ডিলিটের আগে ১০০% প্রমাণ — প্রতিটি রায়ের সাথে grep-প্রমাণ সংযুক্ত।
> **পদ্ধতি:** সম্পূর্ণ read-only যাচাই (`git grep` / `git ls-files` / লাইন-গণনা) + ১টি শূন্য-ঝুঁকি প্রুন। এই ডক নিজে কোনো কোড-পথ বদলায় না।

---

## ১. কেন এই ডক — পুরনো অডিটের drift-সংশোধন

`FULL_ARCHITECTURE_AUDIT_BN.md` (২০২৬-০৯-২৭) চমৎকার বেস, কিন্তু ২০২৬-০৯-২৭-এর পর রিপো এগিয়েছে (#2416/#2417 DRY-pipeline, #2418/#2420/#2426 toolkit-closeout, bacc31a roadmap)। #2427-এর কাজ শুরুর আগে প্রতিটি দাবি current-main-এ পুনঃযাচাই করা হলো। **ফল: audit-এর ৬টি দাবি উল্টে গেছে, ৫টি হুবহু প্রমাণিত, ৫টি নাম-উল্লিখিত ফাইল ইতোমধ্যেই অনুপস্থিত।**

## ২. Fresh Memory-Map (Section ২.১-এর পুনঃযাচাই — সব দাবি বর্তমান ✓)

| উপাদান | প্রমাণ (current main) | অবস্থা |
| :--- | :--- | :--- |
| Writer-1: `CascadeMemoryService.store_memory` | `services/memory_service.py:93` (store_memory :351, pooled PG) | জীবিত — **canonical** |
| Writer-2: module-level `save_memory` | `services/memory_service.py:916` (Supabase REST, ভিন্ন fallback) | জীবিত — একই ফাইলে দ্বিতীয় লেখক |
| Writer-3: `FreeTierOptimizedVectorStore` | `core/ai_memory/vector_store.py:32` | জীবিত — ভিন্ন id-scheme/column |
| Writer-4: `SupabaseVectorBackend`/`ExperienceDatabase` | `adaptive_engine/supabase_vector_backend.py:34` · `experience_db.py:89` | জীবিত |
| **Facade bypass = হুবহু ১৭ ফাইল** | grep-তালিকা: api/routes/{chat,deep_research,global_memory,memory,session_stream}.py, context/sources.py, core/ai_memory/retention.py, core/orchestration/conversation_orchestrator.py, core/startup/agents.py, core/unified_memory.py, engine/{memory_middleware,vector_db}.py, scripts/{store_ci_roadmap_to_memory,sync_knowledge}.py, services/{intent_deciphering,living_engine,self_correction}.py | **হুবহু প্রমাণিত (১৭)** |
| Facade-এর সরাসরি importer | `api/routes/browser/_health.py` · `core/unified_memory.py` (নিজে) | মাত্র ২ — bypass-ই প্রধান পথ |
| SQLite fallback ×৩ | `services/memory_service.py:146` (data/memory.db) · `memory/sqlite_store.py:12` + `core/kernel/audit_logger.py:73` (supreme_memory.db) · `memory/sliding_window.py:36` (sliding_window_memory.db) | জীবিত — schema-ভিন্ন |
| Retrieval "RPC zoo" | match_ai_memories · match_ai_memory · match_memories · AIMemory similarity (SQLAlchemy cosine) · match_experiences | জীবিত |
| Dimension-mismatch (1536 vs 384) | `supabase_vector_backend.py:162-168` — **migration `17_retype_match_experiences_384.sql` দিয়ে ইতোমধ্যে সংশোধিত** (কোড-কমেন্ট past-tense স্বীকার) | ✅ সংশোধিত — seq:2-তে এই আইটেম নেই |

**seq:2-এর জন্য সিদ্ধান্ত-ইনপুট:** ৪ writer → CascadeMemoryService-এ রুট করা; ১৭ bypass-কে facade-এ সরানো; ৩ SQLite → ১ স্ট্যান্ডার্ড ক্যাশ। প্রতিটি ধাপে boot-smoke + contract-test আবশ্যক (লাইভ Supabase sandbox-এ নেই — আচরণ-প্রমাণ CI-নির্ভর)।

## ৩. Audit-Drift সংশোধনী (ভুল দাবি → বাস্তব)

| Audit দাবি | বাস্তবতা (current main) | প্রমাণ |
| :--- | :--- | :--- |
| `unified_router.py` (604L) ডেড | **রিপোতেই নেই** — ইতোমধ্যে প্রুনড | `git ls-files` শূন্য |
| `ephemeral_executor.py` (515L), `parallel_agent_executor.py` (439L) ডেড | **রিপোতেই নেই** | একই |
| `env_validator.py` (691L), `evolution_orchestrator.py` (196L), behavioral_intelligence pkg ডেড | **রিপোতেই নেই** | একই |
| `engine/vector_db.py` + `memory_middleware.py` (217L wrapper chain) ডেড | **জীবিত** — `api/routes/task.py:29`: `from engine.memory_middleware import memory_mw` | import-line প্রমাণ |
| `memory/checkpoint_resume.py` thin-duplicate ডেড | **জীবিত** — `api/routes/memory.py` importer | import-প্রমাণ |
| `optimization/economic_optimizer` (147L) ডেড — "test canonical ডাকে, production অন্যটাকে" | **অর্ধেক উল্টো**: `brain/economic_optimizer.py` = জীবিত (admin.py:524, cognitive.py:6, living_brain.py:63, cognitive_router.py:3 — ৪ importer); আসল প্রোডাকশন-ডেড = `core/optimization/economic_optimizer.py` (শুধু `tests/services/test_economic_router.py` ডাকে) | importer-প্রমাণ |

## ৪. Verified-Dead তালিকা (fresh প্রমাণ, current main)

### ৪.১ এই স্লাইসেই প্রুনড (টেস্টহীন — test_guard প্রশ্নই আসে না)

| ফাইল | লাইন | প্রমাণ |
| :--- | ---: | :--- |
| `backend/tools/ensemble_router.py` | 47 | production+test+doc **শূন্য রেফারেন্স**; নিজের docstring-ই বলে "backward-compatible facade → canonical llm_gateway" — ব্যবহারকারী শূন্য, ক্যানোনিকাল গেটওয়ে অক্ষত |

### ৪.২ Prune-ready (~1,165L) — ০ production importer, কিন্তু নিজের টেস্ট আছে ⇒ `test_guard_policy.allow_deleted_paths` অনুমতি প্রয়োজন

| ফাইল | লাইন | টেস্ট রেফ | প্রমাণ |
| :--- | ---: | ---: | :--- |
| `backend/services/sandbox_service.py` | 181 | tests/services/test_sandbox_service.py | ০ prod importer |
| `backend/core/security/rate_limiter.py` | 155 | tests/unit_light/test_security_rate_limiter.py | ০ prod importer (exact-pattern grep) |
| `backend/core/optimization/economic_optimizer.py` | 147 | tests/services/test_economic_router.py | ০ prod importer |
| `backend/brain/performance_aware_router.py` | 122 | tests/services/test_performance_aware_router.py | ০ prod importer |
| `backend/core/resilience/predictive_circuit_breaker.py` | 100 | tests/core/test_predictive_resilience.py + test_batch4_contracts.py | ০ prod importer |
| `backend/core/rate_limit_quota.py` | 95 | tests/core/test_rate_limit_quota_fallback.py + unit_light | ০ prod importer |
| `backend/engine/smart_router.py` | 89 | tests/engine/test_smart_router.py | ০ prod importer |
| `backend/ecosystem/runtime_selector.py` | 75 | tests/test_runtime_selector.py | ০ prod importer |
| `backend/core/llm/distributed_budget.py` | 63 | tests/core/test_distributed_budget.py | ০ prod importer |
| `backend/core/plugins/capability_resolver.py` | 50 | tests/core/plugins/ + `backend/test_capabilities.py` (root script) | ০ prod importer |
| `backend/tools/preference_memory.py` | 68 | tests/tools/test_preference_memory.py | ০ prod importer (MODULES_LIST: "0 active callers, dormant") |

**maintainer-এর জন্য এক-লাইনের সিদ্ধান্ত:** allowlist-এ এই ১১ টেস্ট-পাথ যোগ হলে seq:2-তে ~1,165L এক ধাক্কায় সংকোচন (প্রতিটির টেস্টও তখনই অপসারণযোগ্য — টেস্ট-ম্যানিপুলেশন নয়, ডেড-টার্গেট সহ পরিবার-অপসারণ)।

### ৪.৩ Alive-ঘোষণা (ভুলভাবে ডিলিট হওয়া থেকে রক্ষা — Golden Invariant)

`circuit_breaker_manager` (llm_gateway ×৩ importer) · `core/cache/rate_limit_atomic` (lazy-import ×৩: security middleware, rate_limit, api_key_limiter) · `core/provider_rate_limiter` (api/dependencies.py) — এগুলো **ডিলিট-নিষিদ্ধ**।

## ৫. Kernel-অবস্থা (Section ২.৪ "Feed the Kernel"-এর ভিত্তি-মাপ)

- `core/kernel/` = dispatcher (210L) + interface (70L) + audit_logger (212L) + audit_chain (306L) — audit-primitive পর্যায়-4 (#2260) পর্যন্ত সংযুক্ত
- Dispatch-পথ: CircleScope → FCC federation (`governance.route`) → fallback legacy `circle_registry`
- seq:3-ব্লুপ্রিন্ট: task / agent-lifecycle / policy-engine ক্ষমতা federation-এ যুক্ত করা — কিন্তু **নতুন duplicate primitive তৈরি নিষিদ্ধ** (issue-র "unification without deletion" ব্যর্থ-প্যাটার্ন); প্রতিটি মাইগ্রেশনে পুরনো পথ ডিলিট-সহ যেতে হবে

## ৬. seq-রোডম্যাপ (এই ডকের প্রমাণে দাঁড়িয়ে)

1. **seq:1 (এই PR):** drift-সংশোধনী + fresh memory-map + 47L প্রুন + prune-ready টেবিল
2. **seq:2:** Single Writer Law — ৪ writer → CascadeMemoryService; ১৭ bypass → `UnifiedMemoryInterface` facade; ৩ SQLite → ১ (প্রতি-ফাইল diff + boot-smoke + contract-test)
3. **seq:3:** prune-ready ১১ ফাইল (maintainer allowlist-পরবর্তী) + Kernel-feed ধাপ-১ (task capability)
4. **seq:4:** Kernel-feed ধাপ-২ (agent-lifecycle + policy) + চূড়ান্ত zero-loss audit

*Report generated: 2026-09-28 · Method: fresh grep/line evidence on current main — কোনো কোড অন্ধভাবে সরানো হয়নি।*
