# SupremeAI — Full Architecture Audit Report
## "Capability Preservation + Implementation Consolidation" — Perfect Structure Roadmap

> **তারিখ:** 2026-09-27 · **ধরন:** Full-codebase architecture audit (backend + infrastructure + governance)
> **মূল প্রশ্ন:** Capability সব রেখে কীভাবে SupremeAI-কে clean, lean, capable, maintainable — এক কথায় **perfect structure**-এ আনা যায়?
> **পদ্ধতি:** ৫টি সমান্তরাল deep-audit (Memory, Browser, MCP, Kernel Primitives, Agent Governance) — production import-graph verification, route-mount mapping, এবং repo-র নিজস্ব আগের audit-গুলোর (M3 decision table, simplification audit, violation matrix) সাথে cross-check করা হয়েছে।

---

# ভাগ ১ — Executive Summary: রায়

## ১.১ Founder-এর analysis সম্পূর্ণ সঠিক — এবং এখন সংখ্যায় প্রমাণিত

> **"SupremeAI over-capable নয়; historically over-fragmented."**
> **"Problem হলো capability বেশি নয়; capability-এর চারপাশে historical layers বেশি।"**

এই দুইটা statement এখন পরিমাপযোগ্য fact:

| মাপকাঠি | ফলাফল | মানে |
|---|---|---|
| Backend production code | 2,033 Python file; `backend/core` একা 453 file / **96,862 lines** | একটা mega-monolith নিজের ভেতরেই ১০টা subsystem লুকিয়ে রাখে |
| Horizontal primitive duplication | ১০টা primitive-এর জন্য **~130 আলাদা implementation** | Kernel নেই বললেই চলে — প্রত্যেক subsystem নিজের মেশিনারি বানিয়েছে |
| Memory landscape | **~18,400 lines**, ~25% redundant; একই `ai_memory` table-এ **4টা writer**, 4+ retrieval path | "15+ competing memory stores" — repo-র নিজের planning doc-ই স্বীকার করেছে |
| Browser landscape | ~9,700 lines, **~30% redundant**; 71 route **দুইবার mount**, 4 endpoint **shadowed** (কখনো চলেই না), **10টা Playwright launch site** | একই browser capability-র ৩টা parallel execution paradigm |
| MCP footprint | ~25,000 lines (TS Tower + Python), **~30% একই কাজ দুইবার**; runtime-এ **৬টা policy engine**, ৩টা audit sink | একটা memory write দুইবার policy-check হয়, তিন জায়গায় audit হয় |
| Governance | **~48,600 lines instruction** (73 file), **130–150টা rule** ৬টা প্রতিযোগী rule-system-এ; মাত্র **6/24 rule system-enforced** | Control টানা হচ্ছে document দিয়ে, system দিয়ে নয় |
| Instruction : Enforcement ratio | **≈ 5 : 1** | Agent-কে মুখস্থ ১৩০ নিয়ম; system আসলে ৬টা জিনিসই আটকায় |
| Confirmed dead code (verified 0 production importer) | **26 file / ~5,200 lines** (mechanical deletion-এর floor) | এগুলো ছোঁয়ার ঝুঁকিই নেই |
| বাস্তবসম্মত consolidation deletion target | **~18,000–22,000 lines** | Capability না হারিয়ে যতটা ছোট হওয়া সম্ভব |

## ১.২ সবচেয়ে গুরুত্বপূর্ণ ৩টা discovery

**১. Kernel আসলে আছে — কিন্তু ক্ষুধার্ত (starved)।**
`backend/core/kernel/` (dispatcher + interface, 242 lines) wired আছে critical route-এর মাধ্যমে, federation + legacy-fallback design সহ। কিন্তু মাত্র **৩টা capability** migrate হয়েছে (health, chat, customer_support)। বাকি সব subsystem এখনো নিজের পুরনো পথে চলে। অর্থাৎ **kernel-consolidation শুরু হয়েছিল, শেষ হয়নি।**

**২. আগের দুইটা consolidation wave ব্যর্থ হয়েছে একইভাবে — নতুন file যোগ করেছে, পুরনো delete করেনি।**
- **PATCH 01:** `core/unified_router.py` (604 lines, docstring বলছে "consolidates 25+ router classes… reduces ~8,000 lines") → বাস্তবে মাত্র **1 importer**; ২৫টা পুরনো router সব বেঁচে আছে।
- **PATCH 05:** `core/unified_learning.py` (746 lines, "consolidates 8+ learning engines") → 7 importer পেয়েছে, কিন্তু ৮টা পুরনো engine-ই আজও বেঁচে আছে।
- ফল: **দুইটা "unified" layer এখন নিজেরাই আরেকটা duplicate।**

> **Lesson (এই audit-এর মূল সূত্র):** Consolidation-এর সফলতা = নতুন abstraction বানানো নয়; **পুরনো path-গুলো সত্যিই delete হওয়া।** এইবারের roadmap-এর প্রতিটা phase-এ "delete ও verify" বাধ্যতামূলক ধাপ।

**৩. "Full freedom + system control" মডেলটা ইতিমধ্যেই এই repo-তে বানানো আছে — শুধু dev-fleet governance তা ব্যবহার করছে না।**
Product-এর নিজের `external_agents/control/policy_engine.py` একটা **fail-closed PolicyEngine** (ALLOWED / POLICY_BLOCKED / HITL_REQUIRED), সাথে mesh lease system (10-min TTL, reap + failover), capability-scoped dispatch। অর্থাৎ তোমার "ঘুড়ি ওড়াও, নাটাই admin-এর হাতে" মডেলের enforcement chassis ঘরেই আছে — শুধু dev-agent fleet এখনো মুখস্থ ১৩০ নিয়মে চলছে।

## ১.৩ "৫০% smaller" দাবির সৎ হিসাব

| Claim | রায় | ভিত্তি |
|---|---|---|
| "একই capability রেখে হুবহু ৫০% কম হতো" (literal, clean-room) | **অপ্রমাণিত** — clean-room rebuild করে মাপা হয়নি, এটা এখনই fact নয় | — |
| "অনেক ছোট implementation footprint-এ একই breadth সম্ভব" (architectural) | **খুবই plausible, সংখ্যায় সমর্থিত** | ২৫–৩০% প্রমাণিত redundancy (memory/browser/MCP) + ১৩০→~২০ primitive consolidation + ৫,২০০ line proven-dead + ৪১k line governance-এর বড় অংশ system-gate-এ রূপান্তরযোগ্য। Backend production surface-এ **৩৫–৪৫% সঙ্কোচন** realistic; পুরো সিস্টেমে ৫০% ছোঁয়া **সম্ভব কিন্তু প্রমাণ করতে হবে phase ধরে** |

---

# ভাগ ২ — প্রমাণ: কোথায় কী Fragmentation (Subsystem-wise)

## ২.১ Memory — "Eternal Brain" যেটা ৪টা হাতে লেখা হচ্ছে

**Canonical ঘোষণা আছে** (`docs/plans/M3_MEMORY_STORE_CONSOLIDATION_DECISION_TABLE.md`): long-term store = Supabase `ai_memory` (pgvector) via `CascadeMemoryService` → `UnifiedMemoryInterface` facade। এবং সেটা আংশিক কাজ করেছে (L2 orphan-spine pass-এ ৫টা dead store delete হয়েছে)। কিন্তু বাকিটা:

**একই `ai_memory` table-এ ৪টা স্বাধীন writer (৩টা incompatible row-shape সহ):**
1. `services/memory_service.py:387` — CascadeMemoryService.store_memory (pooled PG)
2. `services/memory_service.py:929` — একই file-এর ভেতরেই module-level `save_memory` (Supabase REST, ভিন্ন fallback)
3. `core/ai_memory/vector_store.py:60` — FreeTierOptimizedVectorStore (ভিন্ন id-scheme, ভিন্ন column set)
4. `adaptive_engine/supabase_vector_backend.py:109` — ExperienceDatabase-র writer (**schema-drifted** column)

**৪+টা semantic retrieval path একই memory-র উপর:** `query_context` (match_ai_memories RPC) · module-level `recall_memories` (match_ai_memory RPC) · `FreeTierOptimizedVectorStore.similarity_search` (match_memories RPC) · `AIMemory.similarity_search` (SQLAlchemy cosine) · `SupabaseVectorBackend.query` (match_experiences RPC — legacy SQL-এ VECTOR(1536), caller-রা 384-dim — dimension-mismatch documented)। repo-র নিজের schema audit এটাকে ডেকেছে **"The RPC zoo"**।

**আরও:**
- **৩টা স্বাধীন SQLite fallback engine**, schema-ই diverge করে গেছে (`data/memory.db` / `data/supreme_memory.db` / `data/sliding_window_memory.db`)
- **২টা parallel "recall-inject" middleware:** `core/memory/auto_rag_injector.py` (chat path) vs `engine/memory_middleware.py` → `engine/vector_db.py` (wrapper-এর-উপর-wrapper, swarm path)
- **Facade bypass:** `UnifiedMemoryInterface`-কে বাইপাস করে `services.memory_service`-কে সরাসরি **~17 production file** import করে; facade-এর direct importer মাত্র ৪টা (M3 doc-ই স্বীকার করেছে: "facade adoption is the bottleneck")
- **Dead:** `tools/preference_memory.py` (0 importer), `checkpoint_resume.py` (thin duplicate), `engine/vector_db.py`+`memory_middleware.py` (217 lines wrapper chain)
- **Test ত্রিগুণ:** একই `CascadeMemoryService`-এর জন্য ৩টা `test_memory_service.py` (~1,300 lines redundant)

**সংখ্যা:** ~18,400 lines landscape → **~২৫% redundant** (~২,০০০ production + ~১,৭০০ test lines এখনই অপসারণযোগ্য)।

## ২.২ Browser — একই capability, ৩টা execution paradigm, ১০টা launch site

- **দুইটা `/api/browser` router:** package `api/routes/browser/` (2,416 lines, 71 route) vs legacy `browser_routes.py` (867 lines) — এবং package-এর ৭১টা route **দুইবার mount হয়** (`create_app()` + `ALL_ROUTERS` — mount hygiene test নিজেই এটাকে "documented owner-decision exception" বলে skip করে!)
- **৪টা endpoint permanently shadowed:** `POST /api/browser/ai-action`, `/security-scan`, `/screenshot`, `/browse-session` — `browser_routes.py`-এর ২০০+ line-এর implementation **কখনো চলেই না** (পরে mount হওয়ায় প্রথমটা জেতে)
- **`GET /api/browser/health` দুইবার mount**, দুই জায়গার comment দুজনকে দোষারোপ করে
- **২টা `BrowserAgent` class** (`core/agents/live/browser_agent.py` vs `services/scraper/browser_agent.py` — পরেরটার docstring নিজেই স্বীকার করে সেটা আগেরটা থেকে "extracted")
- **২টা `BrowserSessionManager`** (async owner-scoped vs sync persistent-context, Windows-profile default `C:/SupremeAI_Automation_Profile`!)
- **২টা `WebScraper`**, **২টা stealth-fingerprint implementation** (একই spoofing JS দুইবার), **১০টা আলাদা Playwright launch site** (মাত্র ১টা shared singleton)
- **LIVE BUG (frontend-wired একমাত্র path-এ):** `core/browser_session_manager.py:30`-এ `allowed_actions = ("navigate","screenshot","content","extract")` — কিন্তু route আর frontend `click/fill/type` advertise করে ⇒ **প্রতিটা interactive action 403 ফেরত দেয়** (MODULE_04 P-A, এখনো unfixed)
- **জন্মেই মৃত HITL takeover:** `session_takeover.py:408` এমন method ডাকে (`get_or_create_session`) যা `PlaywrightBrowserAgent`-এ অস্তিত্বহীন ⇒ AttributeError, screencast কখনো শুরুই হয় না
- **তৃতীয় parallel layer:** `mcp_adapters/playwright_bolt.py` — নিজস্ব persistent context + নিজস্ব session vault; শুধু নিজের test file-এর জন্য বেঁচে (production importer শূন্য)
- **Verified dead:** `services/browser/` microservice, `integrations/browser_use_adapter.py` (self-declared orphan), `tools/browser/mcp_tools.py`, `web_fallback_agent.py`, unmounted `websocket_hitl.py`
- **ভাঙা test:** root `tests/test_browser_session_manager.py` অস্তিত্বহীন নাম (`AUTOMATION_HOST`) import করে — run-ই হয় না

**সংখ্যা:** ~9,700 production lines → **~৩০% redundant** (~২,৬০০–৩,১০০ lines) + ৭১ route-এর double registration + ৩টা parallel session paradigm।

## ২.৩ MCP Tower — একই নিয়ন্ত্রণ-ব্যবস্থা দুই ভাষায়, তিন কোডবেসে

Tower (`infrastructure/mcp-control-plane/`, 124 TS file / ~13.5k lines) সত্যিই deployed ও আংশিকভাবে load-bearing (render.yaml, ৯টা CI suite)। কিন্তু:

- **Policy engine নিজে নিজে ঘোষণা করে duplicate:** `core/mcp_policy.py`-এর docstring হুবহু: *"Python mirror of the TypeScript RiskEngine + PolicyEngine"* — একই R0–R6 ladder দুইবার maintain, এবং **drift শুরু হয়ে গেছে** (Python-এ ৪টা provider TS-এ নেই)
- **Runtime-এ মোট ৬টা policy স্তর:** TS risk/policy engine + TS mcp-access classification + Python mcp_policy mirror + Python mcp_allowlist + Python ToolPolicyGateway + Tower client-registry RBAC। একটা memory write Tower দিয়ে গেলে **দুইবার policy-evaluate, তিন audit sink-এ** (TS in-memory — restart-এ হারায়! + Python file/Supabase + Python hash-chain) লগ হয়
- **Client registry ×২, tenant registry ×২:** Tower `/clients`+`/tenants` CRUD vs Python `mcp_hub.py` Postgres `McpTenant/McpClient/McpSlug` — একই concept-এর দুইটা admin surface
- **Heartbeat protocol ৩টা codebase-এ hand-sync হয়:** Tower `agent_heartbeat.ts` (90s online/300s TTL) + Python `core/agent_heartbeat.py` + `scripts/agents/mcp_tower_client.py` — Redis contract shared-by-design, কিন্তু একই নিয়ম তিনবার লিখতে হয়
- **Task dispatch ×২:** Tower `orchestrator_dispatch.ts` (event→role→assign) vs Python `task_router.py` (CAS claim + 600s lease) — ভিন্ন semantics
- **Agent messaging ×২:** Tower `/messages` + review-workflow vs Python `agent_mailbox.py` + mesh_mailbox
- **GitHub/Supabase/Telegram adapter ×২ করে** (Tower TS + Python tools/mcp) — দুই credential path
- **মারাত্মক mis-wiring:** `client/supreme-node/config.yaml` Tower-কে পয়েন্ট করে (`heartbeat_path: /api/v1/nodes/heartbeat`, `tower_ws_url: wss://.../ws/node`) — **ওই route-গুলো Tower-এ অস্তিত্বহীন** (সেগুলো Python backend-এ) ⇒ out-of-the-box mesh daemon 404 খায়
- **AGENTS.md Rule 19 (mandatory tower connect + 45s heartbeat) সম্পূর্ণ unenforced:** `mcp_tower_client.py`-এ default URL সরানো হয়ে গেছে (env var ছাড়া প্রতিটা subcommand fail), কোনো CI/hook/startup check নেই — লঙ্ঘনের কোনো automated consequence-ই নেই। আর "no-auth SSE" বলে যেটা লেখা, সেটাও stale — এখন key-auth + guest=public_viewer

**সংখ্যা:** ~25k lines combined → **~৩০% একই কাজ দুইবার**; Tower-এর ভেতরেই ৩৫–৪০% module-এর Python counterpart আছে।

## ২.৪ Kernel Primitives — ১০টা জিনিস বানাতে ১৩০টা implementation

এটাই তোমার analysis-এর হৃদয়: "policy, memory access, agent lifecycle, provider access, audit, routing, execution, state, retry, registry — বিভিন্ন জায়গায় আলাদা abstraction-এ ছড়িয়ে আছে।" গোনা হয়ে গেছে:

| # | Primitive | Implementation সংখ্যা | অবস্থা |
|---|---|---|---|
| 1 | **Policy engine** | **19** (~4,100 lines) | Canonical ৩টা (tool_gateway, circles governance, mcp_policy); kernel-এর জন্য বানানো `contracts/policy.py` কখনো wire-ই হয়নি (0 importer); নিজস্ব ৩টা self-evolution governance stack |
| 2 | **Registry** | **23** (~5,000 lines) | Provider/model registry-ই ৪টা (brain/model_registry, llm_gateway/registry, dynamic_ai/provider_registry, external_agents/providers); dead ২টা |
| 3 | **Audit logger** | **9** (~1,800 lines) | ৪টা স্বতন্ত্র persistence-style trail; মজার কথা — AUD-3 audit নিজেই ধরেছিল security audit logger-এর production caller ছিল শূন্য |
| 4 | **LLM router/gateway** | **18 routing layer** (~7,600 lines) | একটা call ৪–৫ layer পার করে; `services/llm/providers.py` (852 lines) হলো **দ্বিতীয় সম্পূর্ণ provider stack** (httpx) আসল litellm gateway-এর পাশে; `llm_router.py`-এর ভেতরে legacy `LLMGateway` class আসলটাকে shadow করে; dead router ৫টা + failed unified_router |
| 5 | **Retry/Circuit/Budget/Rate-limit** | **25** (~4,300 lines) | **২টা LIVE circuit breaker** ভিন্ন semantics-এ (chat path পুরনোটা ব্যবহার করে — সবচেয়ে বিপজ্জনক overlap); dead ৮টা |
| 6 | **State/Sandbox/Executor** | **16** (~4,400 lines) | **একই নামে ২টা live `DockerSandbox` class** দুই জায়গায়; dead executor ২টা (ephemeral 515, parallel 439) |
| 7 | **Orchestrator** | **~14** (~6,800 lines) | **৪টা আলাদা "swarm" system**; MasterCognitiveOrchestrator আসলে 19-line shim একটা 315-line dispatcher-এর সামনে |
| 8 | **Config** | ১৩ file (~6,900 lines) | **২টা competing startup validator**, দুজনেই নিজেকে canonical দাবি করে; dead: env_validator (691), config_control_plane |
| 9 | **Capability/Plugin** | ৩টা capability system + plugin system | Kernel path (৩টা capability) vs de-facto `adaptive_engine/capability_registry` (9 importer) — দ্বৈত ক্ষমতা; plugin-এর official/* হলো experimental/*-এর shim |
| 10 | **Evolution/Healing/Learning** | ৭ package / **~23,200 lines** | Evolution engine ৫টা, healer ৪টা, learning system ৯+টা — PATCH 05-এর "unified learning" এখন ১০ম সিস্টেম |

**Proven-dead 26 file (~5,200 lines):** `unified_router.py` (604), `env_validator.py` (691), `ephemeral_executor.py` (515), `parallel_agent_executor.py` (439), `evolution_orchestrator.py` (196), `smart_router`, `performance_aware_router`, `intelligence/router`, `ensemble_router`, `runtime_selector`, ২টা dead circuit breaker, ৩টা dead rate limiter, `distributed_budget`, ২টা dead registry, dead plugin জোড়া, `sandbox_service.py`, behavioral_intelligence package (315), `optimization/economic_optimizer` (147 — যাকে test file "canonical" ডাকে, production wire করে অন্যটাকে!)…

**Monolith-এর ভেতরের সবচেয়ে বড় file-রাও একই গল্প বলে:** `config_classification.py` (2,425), `zero_cost_patch_phase1_4.py` (2,299) — প্রতিটা "phase patch" জমা হয়ে আছে, ওয়াশ হয়নি।

## ২.৫ Governance — ১৩০ নিয়মের সংবিধান, ৬টা দাঁত

- **Instruction surface: ~48,600 lines / ~73 file** — AGENTS.md (110) + docs/agents (948) + master_docs (40,246) + .agents (2,240) + .clinerules (2,724) + .specify (776) + .lingma + docs/audits (1,314) + .github/constitution (200)
- একটা agent-কে মাথায় রাখতে হয় **130–150টা নিয়ম, ৬টা প্রতিযোগী rule-system-এ** — এবং সেগুলো পরস্পরবিরোধী (`.lingma` বলছে "push directly, no permission"; AGENTS.md Rule 1/8 বলছে PR-only। Golden Rules-এর শিরোনাম "৮টা", ভেতরে ১০টা। Charter-এর ২৩টা invariant আলাদা নম্বরিং-এ)
- **Rule-by-rule enforcement audit-এর ফল:** মাত্র **~৬টা rule সত্যিই system-enforced** (issue-link, 1-issue-PR, gates-green, test-manipulation guard, branch-naming partial, protected-scope partial) · ৪টা partial/reactive · **১৪টা instruction-only**
- **২টা rule মিথ্যা বলছে:** Rule 16 দাবি করে "PR title format CI দ্বারা blocked হবে" — কোনো gate নেই; Rule 23 `rules_version` field-এর কথা বলে — যে field AGENTS.md-এ অস্তিত্বহীন
- **সবচেয়ে দুঃখের সত্য:** enforcement chassis আগে থেকেই আছে — pr-gate contract synthesizer, collision detector (strict BLOCK), learning guards, merge-train gate, priority ledger, stale-mutex sweeper, per-slot GitHub App credentials। ফাঁকটা শুধু **wiring**-এর
- **Merge train-এর default state = human-approval deadlock:** auto-land বন্ধ থাকায় প্রতিটা green batch কপি-পেস্ট merge command-এর অপেক্ষায় দাঁড়িয়ে, আর single-flight পুরো queue আটকে রাখে
- **Dev-fleet vs Product governance-এর duplication:** role taxonomy ×৪ (fleet lanes, swarm roles, framework departments — `AgentDepartment` class নিজেই দুই জায়গায়! — bot slots), heartbeat ×২, registry ×৩+

---

# ভাগ ৩ — Diagnosis: কেন এমন হলো

```
Problem A → build subsystem A (নিজস্ব state, route, helper, memory, execution)
Problem B → build subsystem B (নিজস্ব policy, adapter, audit, registration)
Problem C → build subsystem C (নিজস্ব store, retrieval, wrapper)
Later     → A+B+C connect করতে গিয়ে নতুন unification layer (যেটা পুরনোগুলোকে replace করে না, বসে যায় তাদের উপরে)
```

এই pattern-এর ৬টা প্রমাণিত রূপ এই codebase-এ:

1. **Unification-without-deletion:** PATCH 01/05 নতুন "unified" layer এনেছে, পুরনোগুলো বাঁচিয়ে রেখেছে — ফলে দুই "unified" layer নিজেরাই এখন duplicate (ভাগ ১.২)।
2. **Facade-declared-but-bypassed:** `UnifiedMemoryInterface` ঘোষিত, কিন্তু ১৭টা caller সরাসরি ভেতরের service ধরে আছে — কারণ কাউকে migrate করার বাধ্যবাধকতা ছিল না।
3. **Mirror-drift:** একই policy দুই ভাষায় লিখে রাখা হয়েছে ("Python mirror of the TS engine") — এক জায়গায় বদলালে আরেক জায়গায় বদলায় না।
4. **Governance-by-prose:** যে control দরকার ছিল, সেটা doc-এ লেখা হয়েছে rule হিসেবে, workflow gate হিসেবে নয় — ১৪/২৪ rule এখন obedience-dependent, ২টা মিথ্যা enforcement-দাবি সহ।
5. **Test-বনাম-production সত্য-বিরোধ:** test একটা module-কে "canonical" ঘোষণা করে (economic_optimizer), production wire করে অন্যটাকে — দুটোই বেঁচে থাকে।
6. **Mount-order নীরব বিজয়:** একই path দুইবার register হলে প্রথমটা জেতে, দ্বিতীয়টা চিরকাল dead হয়ে যায় — কোনো error ছাড়াই (browser-এর ৪টা endpoint, ৭১টা double-mount)।

**মূল রোগনির্ণয়:** এটা খারাপ engineering-এর ফল নয় — এটা **incentive-এর ফল।** প্রতিটা দল/agent যখন নতুন কিছু বানায়, fastest path ছিল নিজের ছোট মেশিনারি গড়ে নেওয়া (kernel ব্যবহার করতে গেলে migrate করতে হয়, review সহ্য করতে হয়)। ফলে সুইটি সর্বদা "নতুন duplicate বানানো"-র দিকে ঝুঁকেছে। **এই incentive না বদলালে যেকোনো consolidation আবার PATCH 01/05-এর মতো পচে যাবে।** সমাধান ভাগ ৫-এ।

---

# ভাগ ৪ — Target Architecture: "Perfect Structure"

## ৪.১ নীতিবাক্য (এই report-এর এক লাইনের সারাংশ)

> **Make the shared foundation SMALL and STRONG. Keep capability breadth BIG.**
> **Don't make the subsystems smaller — delete their repeated machinery.**

```
Capability breadth:        BIG ✅ (রয়ে যাবে — সব MCP, Browser, Memory, Evolution, CI, Deployment)
Implementation footprint: TOO BIG ⚠️ (~130 primitive impl → ~২০)
Future target:             BIG capability + SMALL kernel
```

## ৪.২ Kernel Blueprint (target)

```
                         ┌──────────────────────────────┐
                         │      SUPREMEAI KERNEL         │
                         │  (backend/core/kernel — বর্তমান  │
                         │   ক্ষুধার্ত kernel-কে এখানে পূর্ণ   │
                         │   করা হবে)                    │
                         └──────────────┬───────────────┘
                                        │
      ┌───────────┬───────────┬────────┴──────┬────────────┬───────────┐
      │           │           │               │            │           │
   Task/Run    Agent      Capability       Policy       Memory       Audit
   (runs/ এর   (একটাই     (একটাই registry,  (একটাই       (একটাই       (একটাই
    lifecycle  lifecycle,  kernel-registered) fail-closed  Cascade+     hash-chain
    machine —  একটাই                         engine,      facade —     sink —
    আছে; সবাই  presence —                     R0–R6 এক     সব caller     সব থেকে
    এটা ব্যব-   mesh lease-                   source of    facade        লেখা
    হার করবে)   ভিত্তিক)                       truth)       দিয়ে)        হবে)
      │           │           │               │            │           │
      └───────────┴───────────┴───────┬───────┴────────────┴───────────┘
                                     │
                              EXECUTION CORE
                       (retry · circuit · budget · rate-limit
                        — প্রতি primitive-র ১টা canonical impl)
                                     │
        ┌────────────────┬───────────┴───┬─────────────────┐
        │                │               │                 │
     PROVIDER         BROWSER        MCP GATEWAY      EXTERNAL
   (llm_gateway    (এক Playwright   (এক policy,       AGENTS
    + model_       entry: core/     এক registry,      (external_agents
    router facade  playwright_      এক audit-bridge,   PolicyEngine
    — সব caller    manager; সব      TS→Py generate)   ইতিমধ্যে এই
    এগিয়ে হয়ে     surface এই                          মডেলে আছে)
    যাবে)           এক পথে নামবে)    │                 │
        │                │           │                 │
        └────────────────┴───────────┴─────────────────┘
                                     │
                          VERIFY / AUDIT (এক hash-chain)
                                     │
                    GOVERNANCE GATE (fail-closed:
                    ALLOW / POLICY_BLOCKED / HITL_REQUIRED)
                                     │
                                    MAIN
```

## ৪.৩ প্রতিটা primitive-এর বিজয়ী (canonical) নির্বাচন — এখনই সিদ্ধান্ত

| Primitive | বিজয়ী (canonical) | হারানো সালিশ (retire/absorb তালিকা) |
|---|---|---|
| Policy (tool) | `core/security/tool_gateway.py` | ১৬টা বাকি engine → হয় gateway-এর ক্লায়েন্ট, নয়তো delete |
| Policy (kernel path) | `core/circles/governance_core.py` | `contracts/policy.py` wire করা হবে **না** — delete (কখনো বাঁচেনি) |
| Policy (MCP) | TS engine = source of truth; **Python mirror generated হবে** | hand-maintained `mcp_policy.py` |
| Registry | `core/circles/registry.py` + `llm_gateway/registry` (provider-only) | ২০টা বাকি → merge/delete (৪টা provider registry → ১) |
| Audit | `core/observability/audit_logger.py` (PG write-behind) + **MCP hash-chain একমাত্র tamper-evidence** | security/audit_logger (Redis), mcp_audit (file), TS in-memory audit |
| LLM access | `core/llm/llm_gateway` + `brain/model_router` facade | `services/llm/providers.py` (852) + legacy LLMGateway class + ৫ dead router + unified_router |
| Circuit breaker | `core/resilience/circuit_breaker.py` | `core/circuit_breaker.py` (351 — ৬ caller migrate) + বাকি সব |
| Rate limit | edge `middleware/rate_limiter` + `cache/rate_limit_atomic` | ৩ dead + `provider_rate_limiter` → gateway resilience |
| Budget | `core/cost_guard.py` + `llm/token_budget` | ৬টা বাকি budget module |
| Sandbox | `core/orchestration/cloud_sandbox_orchestrator.py` | `DockerSandbox` ×২ → ১, microvm, fuzz, orphaned sandbox_service |
| Executor | `runtime/task_executor` + `local_code_executor` | ephemeral_executor, parallel_agent_executor (dead) |
| Orchestrator | `conversation_orchestrator` (chat) + `cognitive_pipeline_dispatcher` (pipeline) + **একটাই swarm engine** | ৪টা swarm system → ১; kaggle/reasoning special-purpose গুলো kernel-এর Task primitive-র উপর বসবে |
| Config | `core/config.py` facade + `config_classification.py` (SSoT) | ২ validator → ১, env_validator + control_plane delete |
| Capability | `core/kernel` + `circles/registry` (একটাই path) | `adaptive_engine/capability_registry` → kernel-এ merge; plugin official-shims সরাও |
| Evolution | `core/self_evolution/` (একটাই) | `evolution/` root pkg (2,636 — artifact gate রেখে), `evolution_module` (365), tier8 dup (344) |
| Learning/Experience | `adaptive_engine/experience_db` + `core/learning/store` → একটাই experience store | ৯+ system → ২ (experiential + skill), unified_learning নিজেও delete তালিকায় |
| Memory | `CascadeMemoryService` → `UnifiedMemoryInterface` facade (M3 সিদ্ধান্ত বহাল) | ৪ writer → facade-এর ভেতরে ১; RPC zoo → Phase C অনুযায়ী ৩ RPC; ৩ SQLite fallback → ১ |
| Browser | `core/playwright_manager` (একমাত্র launch) + `api/routes/browser/` package (একমাত্র router) + `core/browser_session_manager` (একমাত্র session) | browser_routes.py-র shadowed অংশ, ২য় BrowserAgent, ২য় WebScraper, ২য় stealth, mcp_adapters playwright_bolt + vault, dead microservices |
| Presence/Heartbeat | **Mesh lease model** (10-min TTL + reap — product-এ প্রমাণিত) | Tower-এর নিজস্ব heartbeat slot-model; supreme-node-এর ভাঙা URL config |
| Governance (dev fleet) | **System gates** (ভাগ ৫) + ১টা machine-readable rule registry | ৬টা rule-system, ৪১k lines-এর বেশিরভাগ prose |

## ৪.৪ থামবে না / কাটবে না — স্পষ্ট সীমানা

**কাটা হবে না (capability অক্ষুণ্ণ):** MCP Tower-এর ২৯টা tool, federation, HITL approval + HMAC link, guardian, health fleet · Browser-এর semantic DOM, vision grounding, autonomous/swarm browsing, stealth, credentials vault · Memory-র episodic/semantic/long-term/checkpoint স্তর, distillation (PLAN-004), consolidation (PLAN-006) · Evolution-এর fitness, canary, self-updater, digital twin · CI-র merge train, collision guard, learning guards · Product-এর fail-closed PolicyEngine।
**কাটা হবে শুধু:** প্রতিটার **নিচের দ্বিতীয়/তৃতীয় copy**, dead path, shadowed route, hand-maintained mirror, prose-নিয়ম।

---

# ভাগ ৫ — AGENTS.md v2: "Full Freedom" Constitution (ঘুড়ি-নাটাই মডেল)

## ৫.১ দর্শনের অনুবাদ

> **"Agent যত খুশি উড়ুক — নাটাই admin-এর হাতে।"**
> Agent-কে আর বলতে হবে না "এই ২৭টা rule follow করো।" System নিজেই বলবে: "No access" / "No permission" / "Approval required" / "Secret unavailable"। Agent শুধু ঠিক করবে **"কীভাবে সমস্যা সমাধান করবে"** — সেটাই তার স্বাধীনতা।

## ৫.২ নতুন AGENTS.md (সম্পূর্ণ draft — বর্তমান ১১০ লাইনের বদলে ~৫০ লাইন)

```markdown
# SupremeAI — AGENTS.md v2 (Full-Freedom Bootstrap)

> তোমার একটাই কাজ: চেয়ে নেওয়া issue সাবলীলভাবে সমাধান করা।
> নিয়ন্ত্রণ তোমার হাতে নয় — SYSTEM-এর হাতে। তাই তোমাকে নিয়ম মুখস্থ করতে হবে না।
> যা করতে পারবে না, system নিজেই আটকাবে এবং কারণ বলে দেবে।

## Bootstrap (৩ ধাপ)
1. `python scripts/agents/acquire_role_slot.py --role <lane>` → slot + mesh lease (lease না থাকলে push-ই হবে না)
2. `./scripts/agents/next_claimable.sh <lane>` → সর্বোচ্চ-অগ্রাধিকার unclaimed issue চেয়ে নাও
3. কাজ করো। উড়ো। যেভাবে ভালো বোঝো সেভাবে সমাধান করো।

## System যা আটকাবে (মনে রাখার দরকার নেই — শুধু জেনে রাখো কেন আটকালো)
| Gate | কখন আটকাবে |
|---|---|
| Lease-gate | mesh lease মেয়াদ শেষ হলে claim/push বন্ধ |
| Scope-gate | claim-এ declare করা file-এর বাইরে বদল আনলে PR BLOCK |
| Collision-gate | অন্য PR-এর file-এর সাথে overlap হলে BLOCK |
| Self-merge-gate | নিজের PR নিজে approve/merge করলে BLOCK |
| Test-guard | test delete/skip/threshold-নামানো হলে BLOCK |
| Policy-engine | যে capability/tool/secret তোমার role-এর নয় — access-ই পাবে না |
| Post-merge watch | merge-এর ১৫ মিনিটে main লাল হলে auto-revert |

## তোমার স্বাধীনতা (কেউ আটকাবে না)
- সমাধানের approach নিজে বেছে নাও — architecture, pattern, library (stack অগ্রাধিকার মানলে ভালো, বাধ্য না)
- যেকোনো unclaimed issue চেয়ে নাও (lane-অগ্রাধিকার advisory, আটকানো নয়)
- আটকে গেলে blocker issue খোলো এবং পরের কাজে যাও — চুপচাপ বসে থেকো না
- ভুল হলে LESSONS_LEARNED.md-তে এক লাইন যোগ করো — শাস্তি নেই, পুনরাবৃত্তি-প্রতিরোধই লক্ষ্য

## একমাত্র কঠিন নিয়ম (মোট ৩টা, বাকি সব system-এর ভার)
1. সৎ থাকো — কাজ "দেখতে ভালো" না, "সত্যিই ভালো" হতে হবে (test manipulation = সর্বোচ্চ অপরাধ)
2. পরমাণু থাকো — এক PR এক উদ্দেশ্য
3. চলমান থাকো — শেষ হলে পরের issue; আটকালে জানাও

> সম্পূর্ণ machine-readable rule registry: `.github/constitution/rules.yml` (CI এটা থেকে gate চালায়)।
> এই file-টি registry থেকে GENERATED — হাতে এডিট করবে না।
```

## ৫.৩ Rule → System-Gate রূপান্তর তালিকা (২৩+ নিয়মের ভাগ্য)

| পুরনো Rule | নতুন জায়গা | Mechanism (chassis বেশিরভাগ আগেই আছে) |
|---|---|---|
| 1 (main touch), 15 (force-push), 18 (cross-branch) | **Server-side GitHub rulesets** + per-slot GitHub App credential শুধু নিজের branch-prefix-এ scoped | `push_as_agent.py`-এর credential map সম্প্রসারণ — **impossible** বানাও, forbidden নয় |
| 2 (claim ছাড়া code), 20 (file declaration) | pr-gate contract step + collision detector এ "Touching files:" parse → undeclared overlap = BLOCK | `cross_pr_collision_detector.py` already strict — শুধু claim-comment parser যোগ |
| 12 (self-merge) | pr-gate-এ ১ job: author vs approvals তুলনা; সাথে GitHub required-reviews ruleset | ~২০ লাইনের gate |
| 13 (one claim) | issue-ops job: actor-এর আগের in-progress থাকলে নতুন claim strip | label-automation সেটাপ আছেই |
| 16/17 (PR title/description — **যেগুলো এখন মিথ্যা**) | pr-gate regex + body length check | মিথ্যা claim সরাও, সত্যি gate বসাও |
| 19 (tower heartbeat) | **Lease-conditional claim/slot**: mesh lease জীবিত না থাকলে `next_claimable.sh` খালি ফেরত দেবে, push credential কাজ করবে না | product-এর lease+reap মেশিনারি fleet-এ আনো |
| 22 (post-merge revert) | integration-gate land job + ১৫-মিনিট verification window + `git revert` | land job আছেই |
| 23 (rules_version) | rules.yml → AGENTS.md generator (CI-তে stamp) | generated-doc pattern |
| 5 (narrowest change) | scope-gate (declared files) — advisory থেকে BLOCK-এ উন্নতি | ৫.৩-এর ২০ নং-এর সাথেই আসে |
| 10 (never idle), 11 (discovery) | স্বাধীনতা-তালিকায় রূপান্তরিত (prose → nudge) — enforcement নয়, culture | — |

**Net effect:** ১৩০–১৫০ মুখস্থ নিয়ম + ৬ সিস্টেম → **৩টা সত্যিকারের নিয়ম + ১টা generated registry + ৭টা gate।** নির্দেশনা-enforcement অনুপাত ৫:১ থেকে উল্টে **~১:৩** হয়ে যায়।

## ৫.৪ Incentive-ফিক্স (ভাগ ৩-এর রোগের ওষুধ) — সবচেয়ে গুরুত্বপূর্ণ সিদ্ধান্ত

> **"New-duplicate tax":** এখন থেকে kernel primitive (policy/registry/audit/retry/circuit/budget/memory-route/provider-route) হিসেবে নতুন class/module define করা **নিষিদ্ধ — architecture gate দিয়ে**।

বাস্তবায়ন: `scripts/ci/`-তে একটা **kernel-allowlist check** — import-graph scan করে দেখবে কোনো PR কি canonical primitive-র বাইরে নতুন policy/registry/logger/router class define করছে কিংবা non-canonical পথ import করছে। করলে BLOCK + বার্তা: "kernel primitive ব্যবহার করো: `<canonical path>`।" এটাই PATCH 01/05-এর পুনরাবৃত্তি ঠেকাবে — **কারণ এবার duplicate বানালে জমার সুইটি নেই, আটকাবেই।**

---

# ভাগ ৬ — Execution Roadmap (Rewrite নয় — Progressive Shrink)

```
Existing huge system
  → Find repeated primitives (DONE — এই report)
  → Choose canonical implementation (DONE — ভাগ ৪.৩)
  → Make everyone use it  ← এখন এখান থেকে
  → Delete duplicate paths
  → Retire dead wrappers / registries / memory routes / browser paths
  → Shrink progressively
```

## Phase 0 — সত্য ও জীবন্ত বাগ মেরামত (১–২ দিন, ঝুঁকি শূন্যের কাছে)
| কাজ | কেন |
|---|---|
| Browser `allowed_actions`-এ `click/fill/type` যোগ (MODULE_04 P-A) | Frontend-wired একমাত্র path এখন 403 দেয় |
| `session_takeover.py`-এর মৃত method-call ঠিক করা বা route retire | জন্ম থেকেই ভাঙা |
| Root test-এর `AUTOMATION_HOST` import ঠিক | Test run-ই হয় না |
| `supreme-node` tower URL config ঠিক/নথিভুক্ত deprecate | Out-of-the-box 404 |
| AGENTS.md Rule 16/23-এর মিথ্যা enforcement-দাবি সরানো | সংবিধানে মিথ্যা থাকবে না |

## Phase 1 — Dead-code sweep (৩–৫ দিন, ঝুঁকি ~শূন্য, **~5,200 lines**)
২৬টা verified 0-importer file delete — repo-র নিজের route/module wiring audit + import-graph CI এটা guard করবে।

## Phase 2 — যা PATCH 01/05 শেষ করতে পারেনি (১–২ সপ্তাহ, **~4,000–6,000 lines**)
- `services/llm` provider-stack বন্ধ → ১৫ caller-কে `brain/model_router`-এ migrate → `providers.py` (852) + legacy LLMGateway delete
- Circuit breaker একত্রীকরণ: `core/circuit_breaker.py`-র ৬ caller → `core/resilience/` → delete (351)
- Rate-limiter ৮→২, budget ৮→২, dead validator/registry যা Phase 1-এ বাদ পড়েনি
- **প্রতিটা ধাপে:** migrate → verify (CI) → **delete** → আবার verify (route-inventory + import-graph test green)

## Phase 3 — Horizontal দখল: primitive-এর বিজয়ীদের রাজ্য (২–৪ সপ্তাহ, **~8,000–10,000 lines**)
- Learning/experience ৯→১ (experience_db + learning/store merge; unified_learning delete সহ) — সবচেয়ে বড় single win
- Evolution ৫→১, healer-গুলো auto_healer (lifespan-wired) কেন্দ্রে
- Registry ২৩→~৬, audit ৪→১ (hash-chain কেন্দ্রে), config validator ২→১
- Memory-র M3 বাকি কাজ: **facade-first mandate** (নতুন caller facade ছাড়া import করলে kernel-allowlist gate BLOCK করবে), ৩ SQLite fallback → ১, RPC zoo-র বর্জিত RPC-গুলোর caller শূন্য করে খারিজ
- Browser: `browser_routes.py`-র ৩টা unique endpoint package-এ port → পুরো file retire; double-mount একটাতে নামানো (role-aware সিদ্ধান্ত); ২য় BrowserAgent/WebScraper/stealth merge; mcp_adapters+vault archive

## Phase 4 — Kernel-এ capability ফেরত আনা (চলমান, structural)
- `core/kernel/`-এ Task/Run/Policy/Memory/Audit/Execution primitive উঠবে — **নতুন code নয়, ভাগ ৪.৩-এর বিজয়ী canonical file-গুলোই kernel package-এ বসবে + dispatcher সেগুলো ডাকবে**
- মাইগ্রেশন ক্রম: যে primitive-র caller সবচেয়ে কম (audit) → যেটার সবচেয়ে বেশি (provider route)
- প্রতি wave-এ kernel-registered capability count বাড়বে (৩ → ৮ → ১৫ → …) এবং **dispatcher-এর legacy fallback path shrink হবে** — fallback-এর দৈর্ঘ্যই হবে অগ্রগতির মাপকাঠি

## Phase 5 — Governance flip: prose → gate (১ সপ্তাহ, ভাগ ৫ বাস্তবায়ন)
- `rules.yml` (machine-readable) লিখুন → gates wire (৫.৩-এর তালিকা) → AGENTS.md v2 generated করে বসান
- Lease-conditional claim/slot চালু (Rule 19-এর সত্যিকারের রূপ)
- Merge train auto-land সিদ্ধান্ত: guardian-verdict সবুজ হলে অটো, নাহলে human — প্রথমে এই নিরাপদ সংস্করণই
- ৬ rule-system-এর ৪টা (`.lingma`, `.clinerules`-এর duplicate অংশ, `.agents/rules`, docs/agents-এর পুরনো নথি) → archive; বাকি সব rules.yml-এ absorb

## Phase 6 — MCP unification (১–২ সপ্তাহ, Phase 3–4-এর পরে)
- Policy: TS engine = SSoT; `core/mcp_policy.py` **generate হবে** (schema থেকে, CI-তে drift check)
- Tower-এর in-memory audit → Python hash-chain sink-এ pipe
- Client/tenant registry: Tower = data path, hub = control plane (docstring-এর ঘোষণা সত্য করো — Tower-এর CRUD হঠাৎ সরাবে না, আগে read-only করো)
- Mesh-vs-Tower উপস্থিতি/কাজ: **mesh lease model জেতে** (product-প্রমাণিত); Tower heartbeat নিজে mesh lease পড়বে
- GitHub/Supabase/Telegram-এর Python duplicate adapter → dormant তালিকায় (owner-review সিদ্ধান্ত বহাল)

## Verification discipline (প্রতিটা phase-এ, বাধ্যতামূলক)
1. Pre: route-inventory + import-graph baseline capture
2. Post-migrate: full CI + merge train batch সবুজ
3. Post-delete: **একই baseline আবার তুলনা** — যে path delete হয়েছে তার caller শূন্য প্রমাণ
4. LESSONS_LEARNED.md-তে এক লাইন
5. সব পরিবর্তন atomic PR-এ (১ issue = ১ PR) — নিজেদেরই সংবিধান মেনে

---

# ভাগ ৭ — Success Metrics (নিজেকে ধোঁকা দেওয়া বন্ধ)

| মাপকাঠি | এখন | Target (Phase 6 শেষে) |
|---|---|---|
| Horizontal primitive implementation | ~130 | **~20** |
| Policy engine | 19 (৬ runtime layer/ধাপ) | ৩ declared + ১ generated mirror |
| Registry | 23 | ~6 |
| Audit trail | ৯ module / ৪ persistence style / ৩ MCP sink | ১ + ১ hash-chain |
| `ai_memory` writer | ৪ (৩ incompatible shape) | **১** (facade-এর ভেতরে) |
| Browser route-mount | ৭১×২ + ৪ shadowed + health×২ | ৭১×১, shadow = 0 |
| Playwright launch site | ১০ | **১** |
| Live circuit breaker | ২ (chat পুরনোটায়) | ১ |
| Swarm engine | ৪ | ১ |
| Dead code | ~5,200 lines proven (+ অনাবিষ্কৃত) | 0 (import-graph CI জাবেদা ধরবে) |
| Agent-instruction surface | ~48,600 lines / 130–150 rules / 6 system | **<2,000 lines / ৩ নিয়ম / ১ generated registry** |
| System-enforced rule | 6/24 | **সব (যা বলা হয়, তা-ই হয়)** |
| Instruction:enforcement | 5:1 | **~1:3** |
| Backend production surface | ~208k lines (core 97k) | **~১৩০–১৪৫k** (−৩৫–৪৫%) |

**এবং সবচেয়ে বড় মাপকাঠি:** নতুন agent-এর bootstrap time — এখন ১১০+৯৪৮+৪০k লাইনের সংস্কৃতি-পাঠ; target: **৩ লাইনের bootstrap + system নিজে শেখাবে (gate-এর error message-ই documentation)।**

---

# পরিশিষ্ট A — এই audit-এর নিজস্ব সীমাবদ্ধতা (সততা)

1. সংখ্যাগুলো static import-graph + route-mount analysis থেকে; runtime tracing (যে code আসলে execute হয়) করা হয়নি — তাই "dead" তালিকায় হাত দেওয়ার আগে প্রতিটা আইটেমের শেষ sanity check (env-gated lazy import) Phase 1-এ করতে হবে।
2. "৫০% ছোট" দাবির বাস্তব যাচাই হবে phase শেষে line-count তুলনায় — আগে নয়।
3. TS Tower-এর অভ্যন্তরীণ quality deep-dive হয়নি — শুধু Python counterpart-এর সাথে overlap মাপা হয়েছে।
4. এই report audit-only: **কোনো code পরিবর্তন করা হয়নি।** প্রতিটা সংখ্যা যাচাইযোগ্য — উৎস হিসেবে প্রতিটা ভাগে concrete file:line উল্লেখ আছে।

# পরিশিষ্ট B — মূল উৎস-নথি (repo-র নিজের audit যারা একই কথা বলে)

- `docs/plans/M3_MEMORY_STORE_CONSOLIDATION_DECISION_TABLE.md` (canonical memory সিদ্ধান্ত + বাকি ঝুঁকি)
- `docs/audit_reports/simplification-audit-2026-09-27/` (নিজেদের ~6.2–7.4k line redundancy অনুমান — এই report-এর dead-code floor-এর সাথে সামঞ্জস্যপূর্ণ)
- `docs/audits/violation-matrix.md` (49 violation vector, ১৭টার enforcement নেই — এই report-এর ১৪/২৪ instruction-only ফলাফলের সাথে মিলে যায়)
- `docs/database/AI_MEMORY_SCHEMA_AUDIT.md` (RPC zoo + ৪ writer-এর আসল বিবরণ)
- `docs/plans/crown_jewel_series/MODULE_04_BROWSER_AUTOMATION_POWER_UP.md` (browser ভাই-রাউটার + মৃত takeover আগেই ধরা)

---

*Report generated: 2026-09-27 · Method: 5 parallel deep-audits + cross-verification against repo's own audit corpus · No code was modified.*
