# SupremeAI — দর্শন-ভিত্তিক সরলীকরণ প্ল্যান (v2)

> **তারিখ**: 2026-09-27  
> **HEAD**: `11d02375`  
> **পূর্ববর্তী ডকুমেন্ট**: `SIMPLIFICATION_AUDIT_REPORT.md` (৮২ findings — কিন্তু দর্শন ছাড়া)  
> **এই ডকুমেন্ট**: সংবিধান ও দর্শন পড়ে প্ল্যান recreate

---

## কেন এই ডকুমেন্ট আগেরটার চেয়ে আলাদা

আগের অডিটে আমি জিজ্ঞেস করেছিলাম: **"কোথায় জটিলতা আছে?"** — ৮২টা জায়গা পেয়েছিলাম।  
কিন্তু আপনি ঠিক বলেছেন: "সব ফাইল মুছে দিলেও সিম্পল হয়" — সেটা simplification নয়, ধ্বংস।

এইবার আমি জিজ্ঞেস করছি: **"SupremeAI আসলে কী হতে চায়? আর বর্তমান জটিলতা কোথায় সেই উদ্দেশ্যকে সেবা করছে বনাম বাধা দিচ্ছে?"**

সংবিধান, মাস্টার প্ল্যান, FCC আর্কিটেকচার, রিস্ক-টায়ারড সেফটি — এই চারটি ডকুমেন্ট পড়ে আমি প্রোজেক্টের আত্মা বুঝেছি। নিচে সেই বোঝাপড়া, তারপর প্রতিটা আগের ফিল্ডিংকে দর্শনের কাঠগড়ায় দাঁড় করানো হলো।

---

## অংশ ১ — SupremeAI-এর আসল পরিচয় (দর্শন পড়ে যা বুঝলাম)

### সংবিধানের ১০ নীতি (সংক্ষেপে)

`docs/architecture/SUPREMEAI_CORE_CONSTITUTION.md` থেকে:

1. **গুরুত্বপূর্ণ নিয়ন্ত্রণ কেন্দ্রীভূত হবে** — distributed implementation ঠিক আছে, fragmented governance নয়।
2. **সম্পূর্ণ Circle তৈরি করো** — প্রতিটা capability সিস্টেমের সাথে কানেক্ট হবে + প্ল্যাটফর্ম শক্তি বাড়াবে।
3. **তৈরির আগে পুনরায় ব্যবহার করো** — নতুন infrastructure বানানোর আগে existing capability খোঁজো।
4. **Provider sovereignty ধরে রাখো** — external service replaceable, SupremeAI orchestration ধরে রাখে।
5. **Tenant ownership সংরক্ষণ** — প্রতিটা operation tenant + actor scope resolve করবে।
6. **কাজের আগে ভাবো** — risk, authorization, human approval → consequential action এর আগে।
7. **শেখার জন্য governance দরকার** — autonomous evolution এর আগে evidence + review।
8. **বিশ্বাসের আগে যাচাই** — গুরুত্বপূর্ণ ফলাফল/পরিবর্তন observable verification চায়।
9. **ইউজার চয়েস না কমিয়ে খরচ কমাও** — sustainable cloud-native, explicit performance choice সম্মান করো।
10. **গুরুত্বপূর্ণ behavior observable করো** — failure/degraded/decision/side-effect এর evidence থাকবে।

Execution order: `Discover → Resolve tenant/actor → Authorize/policy → Execute → Verify → Audit → Learn`

### মাস্টার প্ল্যানের মূল দাবি

`README.md` + `SUPREMEAI_MASTER_PLAN_CANONICAL.md` থেকে:

> **SupremeAI একটা chatbot নয় যার অনেক tool আছে।** এটা একটা governed, model-agnostic **task-execution system** যার দীর্ঘমেয়াদী উদ্দেশ্য: বাস্তব ইউজার সমস্যা সমাধান করা — capability আবিষ্কার, কম্পোজ, পুনরায় ব্যবহার, এবং সত্যিকারের প্রয়োজনে তৈরি করার মাধ্যমে। একই যন্ত্রপাতি SupremeAI-কে নিজেকে পরিচালনা, টেস্ট, মেরামত, শেখা ও নিরাপদে উন্নত করতে সক্ষম করবে।

**মূল স্থাপত্য নিয়ম**: নতুন সমস্যা এলে SupremeAI প্রথমে জিজ্ঞেস করবে — *আমার কাছে কী আছে?* — সেটা না জেনে যে *কী বানাতে হবে*।

### ৬টি নির্বাচিত Battlefield (যেখানে জিতবে)

| # | Battlefield | কেন জিতবে | কোন নীতি |
|---|------------|-----------|-----------|
| B1 | **Verified Reliability (pass^k)** | governed verify-loop, consistency > demo-grade pass@1 | #5, #10 |
| B2 | **Agentic Task Completion** | capability-composition + governed execution + repair/failover | #3 |
| B3 | **Cost Frontier** | zero-cost chain + Tier0 + cache + scout summarizer | #9 |
| B4 | **Compounding Memory** | hierarchical memory + Auto-RAG + learning loop | — |
| B5 | **Bengali + Regional Depth** | native Bengali tooling + Phase 3 adapter | #4 |
| B6 | **Integration Surface (MCP federation)** | governed MCP gateway + one-URL connect | #2 |

**যেখানে লড়া হবে না**: raw parameter count, frontier reasoning benchmarks, multimodal scale, pretraining size।

### FCC আর্কিটেকচার — "Central Small, Local Owned"

`docs/architecture/FCC_ARCHITECTURE.md` থেকে:

```
Global Governance Core (ছোট — শুধু cross-cutting)
identity · policy · approval · correlation · lifecycle · audit · realtime sync
   ↓
10টি Circle Center: LLM, Memory, Task, Browser, MCP, Admin, Realtime, Artifact, Evolution, Gateway
   ↓
প্রতিটা Circle-এর নিজস্ব adapter
```

**নিয়ম**: module কখনো সরাসরি module এর সাথে কথা বলে না। সব traffic: `module → own circle center → shared envelope → other circle center → module`। এটা N² connections trap এড়ায়।

**Centralized**: identity, policy, approval, correlation, lifecycle, audit, cross-circle events, realtime sync।  
**Local (প্রতিটা Circle-এর)**: registry, permissions, retries, health, caching, events, adapter selection, domain logic।

### রিস্ক-টায়ারড সেফটি — "Simple by default, deep by risk"

`docs/architecture/RISK_TIERED_AUTONOMOUS_SAFETY_PIPELINE.md` থেকে:

> **"Simple by default, deep by risk."**  
> সাধারণ/কম-ঝুঁকির কাজে সিস্টেম সুপারফাস্ট ও সস্তা; সংবেদনশীল/উচ্চ-ঝুঁকির কাজে বহু-স্তরের গভীর প্রতিরোধ + নিরপেক্ষ যাচাই।  
> **"SupremeAI নিজেকে অন্ধভাবে নিরাপদ মনে করবে না; নিজেকে ক্রমাগত পরীক্ষা করবে।"**

### Multi-Agent Operating Model — "Agents may work independently, but final codebase behaves as ONE system"

`docs/architecture/MULTI_AGENT_OPERATING_MODEL.md` থেকে:

> **PASS ≠ MERGE** — green test প্রমাণ করে না যে কোড final system-এ থাকা উচিত।  
> কোড যা "অদরকারী মনে হয়" তাও dependency না চেক করে delete করা যাবে না।

---

## অংশ ২ — "Core" বনাম "Accident" (কী থাকবে, কী যাবে)

দর্শন পড়ে আমি প্রতিটা স্তরকে দুই ভাগে ভাগ করেছি:

### 🟢 CORE (অবশ্যই থাকবে — দর্শন পূরণ করে)

| স্তর | Core উপাদান | কোন নীতি/Battlefield |
|------|------------|---------------------|
| **গভর্নেন্স** | HITL engine, audit ledger, RLS tenant isolation, policy-gated MCP, constitution CI | #5, #6, #7, #8 |
| **Capability Discovery** | capability_inventory, route_consumer_inventory, orphan gate | #3 "reuse before creation" |
| **Verify Loop** | pass^k estimator (`core/self_benchmark.py`), mission suite | B1, #8 |
| **Zero-cost chain** | Tier0 fast path, semantic cache, token compression, scout summarizer | B3, #9 |
| **Memory** | pgvector, Auto-RAG, hierarchical memory tree | B4 |
| **FCC boundaries** | GovernanceCore, Circle centers, ExecutionEnvelope (tenant+actor), test_fcc_boundaries | #2, #5 |
| **Tenant isolation** | RLS, actor context propagation, tenant_id enforcement | #5 |
| **MCP federation** | governed gateway, capability registry | B6, #2 |
| **Bengali native** | BengaliNormalizer, Bangla docs, Phase 3 adapter path | B5 |
| **Observable** | append-only audit, correlation_id, fail-closed trio, STATUS_PROOF | #10 |
| **Multi-agent governance** | NO_CLAIM_NO_CODE, 1-issue-1-PR, NO_SELF_MERGE, NO_TEST_MANIPULATION | AGENTS §2 |

### 🔴 ACCIDENT (থাকার কোনো দর্শন-ভিত্তিক কারণ নেই — জমা হয়েছে)

| স্তর | Accident উপাদান | কেন accident |
|------|----------------|-------------|
| **ডুপ্লিকেট scanners** | ৩টা route↔frontend scanner, ৪টা generator list | #1 "centralize" লঙ্ঘন — একই কাজ ৪ জায়গায় |
| **Dead code** | external_agents (২৮৭৩), AutoCacheProxy, SwarmConsensusEngine, dead frontend hooks | #2 "complete circles" লঙ্ঘন — incomplete, disconnected |
| **Masked pre-existing debt** | regression_scanner ৫টা localhost, validate_domain_boundaries test→prod false positive | #8 "verify before trust" লঙ্ঘন — যাচাই broken |
| **Hardcoded thresholds** | test_gateway_context `total >= 12`, expected route-files set | #1 লঙ্ঘন — নিয়ন্ত্রণ hardcoded, centralized নয় |
| **Inconsistent auth posture** | get_current_admin (৩৮ files, কোনো revocation check নেই) vs require_admin_token (১১ files, revocation-checked) | #6 "think before acting" লঙ্ঘন — একই sensitivity, ভিন্ন নিয়ন্ত্রণ |
| **Heavy test setup** | ১০+ test `from core.app import app` (পুরো lifespan init) | B1 "verified reliability" লঙ্ঘন — test flaky হওয়াই যাচাই দুর্বল |
| **Function-level import bug** | security.py:261 (monkeypatch bypass → security_rate_limit ৪× CI fail) | #8 লঙ্ঘন — যাচাই কাজ করছে না |
| **Orphan route accumulation** | ৪টা orphan route fix করতে হলো (stream_voice, websocket_agent, merge-learning, render-ticket) | #3 লঙ্ঘন — capability graph incomplete |
| **i18n dead stack (frontend)** | ৩১৬ LOC, শুধু dead Header consume করে | B5 লঙ্ঘন — Bengali depth আছে কিন্তু i18n framework dead |
| **Boilerplate sprawl** | ৩৬ identical @property in config_secrets, ৫ identical prompt router | #9 "sustainable cost" — maintenance cost বাড়ছে |
| **Fragmentation** | ৭ agent route ফাইল, ৫ admin route ফাইল, ৬ auth dep | #1 "centralize" — scattered governance |

---

## অংশ ৩ — আগের ৮২ ফিল্ডিংকে দর্শনের কাঠগড়ায় দাঁড় করানো

প্রতিটা ফিল্ডিংকে এখন প্রশ্ন করা হলো: **"এটা core-কে সেবা করে, নাকি accident?"**

### ✅ যথাযথ — KEEP (দর্শন পূরণ করে, সরল করার দরকার নেই)

এই ফিল্ডিংগুলো **প্রকৃত সরলীকরণ** কিন্তু **দর্শন পূরণ করে না** — বরং সরল করলে দর্শন ভাঙবে।

| ID | আগের ফিল্ডিং | কেন KEEP (দর্শন পূরণ করছে) |
|----|-------------|--------------------------|
| C10 | get_current_admin vs require_admin_token inconsistency | এটা **প্রকৃত security bug**, simplification নয়। আলাদা security PR দরকার (revocation check universal করতে হবে)। দর্শন #6 "think before acting" পূরণ করতে এটার উপরেই কাজ করতে হবে, নিচে নয়। |
| B2 (আংশিক) | ৫টা prompt router | যদি প্রতিটা ভিন্ন domain serve করে (chat vs reasoning vs tool-use), তাহলে unification করলে capability specialization হারাবে। **আগে verify করো** প্রতিটা router আলাদা capability দেয় কিনা। যদি না দেয়, তবে simplify। |
| D2 | multicloud 403 (JWTAuthMiddleware) | এটা **by-design external auth কিনা** আগে নিশ্চিত করো। যদি Firebase/Supabase external auth হয়, তাহলে টেস্টটাই ভুল — simplify নয়, behavior question। |

### 🟡 পুনরায় শ্রেণীবদ্ধ — REFRAME (দর্শন পূরণ করে কিন্তু আগের framing ভুল ছিল)

এই ফিল্ডিংগুলো সরল করা ঠিক আছে, কিন্তু আগের justification দর্শন-বিহীন ছিল। নতুন framing:

| ID | আগের ফিল্ডিং (ভুল framing) | নতুন framing (দর্শন-ভিত্তিক) |
|----|---------------------------|----------------------------|
| A1 | "৪ generator list → ১, ~150 LOC" | **নীতি #1 (centralize) পূরণ**: এখন ৪ জায়গায় list drift করে — সেটা "fragmented governance" যা সংবিধান নিষিদ্ধ করে। simplification নয়, **centralization mandate**। |
| A5 | "regression_scanner baseline JSON" | **নীতি #8 (verify) পূরণ**: এখন pre-existing debt কে red করে — সেটা "false verification signal" যা সংবিধান নিষিদ্ধ করে। নতুন debt ধরাই target, পুরোনো ধরা নয়। |
| A2/D8 | "test_gateway_context hardcoded সরাও" | **নীতি #1 পূরণ**: hardcoded threshold = "hardcoded control", সংবিধান centralized control চায়। `BASELINE=0` ratchet সেটাই করে — hardcoded addition শুধু noise। |
| D1 | "security.py module-level import" | **নীতি #8 (verify) পূরণ**: এখন monkeypatch bypass করে → test মিথ্যা সবুজ/লাল → verification অকার্যকর। এটা bug fix, simplification নয়। |
| D3 | "pytest --cov সরাও, ২০-৩০% দ্রুত" | **নীতি #9 (sustainable cost) পূরণ**: প্রতিটা unit test run এ coverage overhead = developer time waste = cost। কিন্তু CI coverage gate থাকবে — প্রতিটা local run এ নয়। |
| B1 | "৩৬ @property → __getattr__" | **নীতি #9 পূরণ**: boilerplate maintenance = প্রতিটা নতুন secret এ আরেকটা ৬-লাইন block যোগ = cost growth। `__getattr__` + key map হলে শূন্য boilerplate, একই API। |
| B13/B14 | "২ DeclarativeBase → ১" | **নীতি #5 (tenant ownership) পূরণ**: alembic silent-miss hazard = tenant data corruption risk। এটা security fix, simplification নয়। |
| C3 | "৩× /api/v1/health mount → ১" | **নীতি #10 (observable) পূরণ**: ৩টা health endpoint = ambiguity কোনটা live। একটাই canonical health = single source of truth। |
| C12 | "websocket_hitl.py dead delete" | **নীতি #2 (complete circles) পূরণ**: dead route = incomplete circle = "alive-looking but dead" (যা Phase 0 এর gate ছিল "zero alive-looking dead")। |
| E2 | "i18n dead stack delete (৩১৬ LOC)" | **নীতি B5 (Bengali depth) পূরণ**: i18n framework dead কিন্তু Bengali native হতে চায় — সেটা paradox। হয় i18n live করো বা dead মুছে Bengali-native পথ বানাও। |
| B12 | "external_agents/ ২৮৭৩ LOC dead" | **নীতি #2 + #4 পূরণ**: এটা capability surface দাবি করে কিন্তু কোনো consumer নেই = "alive-looking but dead"। Phase 0 gate লঙ্ঘন। কিন্তু **আগে verify করো** কোনো feature flag দ্বারা enable কিনা। |

### ❌ বাদ দাও — DROP (সরল করলে ফলাফল পরিবর্তন হবে বা কোনো লাভ নেই)

| ID | আগের ফিল্ডিং | কেন DROP |
|----|-------------|----------|
| A4 | ARCH-001 এ `_BLOCKED` denylist carve-out | ARCH-001 নিজেই false-positive তৈরি করে (localhost-as-denylist-token)। সঠিক fix = ARCH-001 rewrite করা (semantic-aware), carve-out নয়। carve-out হলো symptom-patching। |
| A7 | "৩ route scanner → ১ canonical" | যদি প্রতিটা ভিন্ন concern scan করে (frontend inventory vs backend consumer vs contract drift), তাহলো merge করলে capability loss। **আগে verify করো** প্রতিটা ভিন্ন কাজ করে কিনা। |
| A12 | "pr-gate.yml inline Python → scripts" | এটা LOC shift, simplification নয় — same logic অন্য ফাইলে যাবে। maintainability কিছুটা ভালো, কিন্তু দর্শন পূরণ করে না। |
| B5/B6/B8/B9/B10 | dead code delete (AutoCacheProxy, IntelligentCacheBridge, SlidingWindowRateLimiter, SwarmConsensusEngine, ৪ messaging files) | এগুলো **KEEP-এর candidate** নয় — এগুলো dead, delete করাই দর্শন (#2 complete circles)। কিন্তু আগের audit এগুলোকে "simplification" বলেছিল — আসলে এটা **dead code removal** (Phase 0 "stop the bleeding"-এর continuation)। |
| E6 | "unifiedStore.ts dead flag strip" | এটা behavior change risk — প্রতিটা flag আলাদাভাবে verify করো। shotgun strip করলে UI regression হতে পারে। |

---

## অংশ ৪ — দর্শন-ভিত্তিক প্ল্যান (সারাংশ)

### প্ল্যান নীতি: **"Centralize governance, simplify mechanics, preserve capability"**

আগের প্ল্যান ছিল "LOC কমাও"। নতুন প্ল্যান হলো তিনটি অক্ষে:

```
১. GOVERNANCE সেন্ট্রালাইজ করো   (নীতি #1 পূরণ)
২. DEAD/INCOMPLETE সাফ করো         (নীতি #2 "complete circles" পূরণ)
৩. MECHANICS সরল করো                (নীতি #9 "sustainable cost" পূরণ)
```

প্রতিটা কাজ এই তিন অক্ষের কোন একটাকে পূরণ করবে — নাহলে সেটা simplification নয়।

### স্তর ১ — GOVERNANCE সেন্ট্রালাইজ (সর্বোচ্চ অগ্রাধিকার)

এটা whack-a-mole-এর root fix। সংবিধান #1 বলছে "fragmented governance নিষিদ্ধ" — কিন্তু এখন ৪ জায়গায় generator list, ৩টা overlapping scanner, ৬টা ভিন্ন auth dep।

| কাজ | কী পূরণ করে | প্রচেষ্টা | ঝুঁকি |
|-----|------------|-----------|--------|
| **G1**: ৪ generator list → ১ canonical `regen_all_artifacts.sh` (A1) | নীতি #1 — একই কাজ এক জায়গায় | M | low |
| **G2**: `validate_domain_boundaries` test-source exemption + baseline ratchet (A5 + নতুন) | নীতি #8 — verify শুধু নতুন regression ধরে, পুরোনো false positive নয় | S | low |
| **G3**: `test_gateway_context` hardcoded threshold/set সরাও (A2/D8) — `BASELINE=0` যথেষ্ট | নীতি #1 — নিয়ন্ত্রণ data-driven, নয় hardcoded | S | low |
| **G4**: `regression_scanner` এ baseline JSON ratchet (A5) | নীতি #8 — pre-existing debt red না করে, শুধু নতুন debt | S | low |
| **G5**: ৬টা auth dep audit → একটা `auth_policy.md` decision doc (C10 reframe) | নীতি #6 — প্রতিটা sensitivity স্তরের জন্য স্পষ্ট policy | M | med |
| **G6**: `record_merge_learning` exit 0 যখন PR open (DONE — c89c0006) | নীতি #10 — observable but not false-failure | — | — |

### স্তর ২ — DEAD/INCOMPLETE সাফ করো (Phase 0-র continuation)

সংবিধান #2 "complete circles" + Phase 0 "zero alive-looking dead" গেট। এখনও অনেক dead/incomplete আছে।

| কাজ | কী পূরণ করে | প্রচেষ্টা | ঝুঁকি |
|-----|------------|-----------|--------|
| **D1**: backend dead code delete — external_agents (verify first), AutoCacheProxy, SwarmConsensusEngine, ৪ messaging files, SlidingWindowRateLimiter (B5/B6/B8/B9/B10/B12/B16) | নীতি #2 — incomplete circles সাফ | M | med (verify first) |
| **D2**: frontend dead delete — i18n stack, ৩ service, ৩ realtime hook, ৫ component, ২ dashboard file (E2/E8/E10/E11/E13/E14) | নীতি #2 + B5 — dead i18n সাফ করে Bengali-native পথ খোলে | S | low |
| **D3**: dead route delete — websocket_hitl, codeflow shim, duplicate /api/v1/health, /admin/rules, deprecated alerts (C3/C5/C8/C12/C13) | নীতি #2 — orphan capability সাফ | S | low |
| **D4**: stale validate_router_imports.py entries (C14/C15) | নীতি #8 — যাচাই সঠিক রাখো | S | low |
| **D5**: `audit_module_wiring.py` + `sync_modules_list.py` wire বা delete (A9) | নীতি #10 — observability consistent | S | low |
| **D6**: STATUS.md এ `qa-live-smoke` → `nightly-ops` (DONE — a5e16e72) | নীতি #10 — doc truth | — | — |
| **D7**: ১২টা shadow endpoint dedupe (C-pattern) | নীতি #1 — এক path এক handler | M | med |
| **D8**: ১১টা stale sentinel_agent skip — delete বা rewrite (D7 from test audit) | নীতি #8 — test যাচাই করে কিছু, নয় noise | S/L | low/med |

### স্তর ৩ — MECHANICS সরল করো (maintenance cost কমাও)

সংবিধান #9 "sustainable cost" — কিন্তু শুধু তখনই যখন capability অপরিবর্তিত থাকে।

| কাজ | কী পূরণ করে | প্রচেষ্টা | ঝুঁকি |
|-----|------------|-----------|--------|
| **M1**: `security.py` module-level import (D1-test) — security_rate_limit ৪× CI fail fix | নীতি #8 — যাচাই কাজ করবে | S | low |
| **M2**: ১০+ test `from core.app import app` → minimal `FastAPI()+include_router` (D4) | নীতি #8 — test collection robust | M | low |
| **M3**: pytest `--cov=core` addopts থেকে সরাও, আলাদা coverage step এ (D3) | নীতি #9 — local run দ্রুত | S | low |
| **M4**: ৩৬ identical @property → `__getattr__` + key map (B1) | নীতি #9 — boilerplate শূন্য | M | low |
| **M5**: ২ DeclarativeBase → ১ (B13/B14) | নীতি #5 — tenant data safe | M | med |
| **M6**: `db_engine` local default → sqlite (D6) | নীতি #8 — local test robust | S | low |

---

## অংশ ৫ — বাস্তবায়ন ক্রম (দর্শন-ভিত্তিক)

আগের প্ল্যানে "Quick Wins আগে" ছিল — কিন্তু দর্শন বুঝে নতুন ক্রম:

### ধাপ ১ — VERIFY আগে (১-২ দিন)

সব কাজের আগে, যেগুলো "dead" দাবি করা হয়েছে সেগুলো verify করো। `MULTI_AGENT_OPERATING_MODEL.md` বলছে: *"কোড যা অদরকারী মনে হয় তাও dependency না চেক করে delete করা যাবে না।"*

| Verify কাজ |
|------------|
| external_agents/ — কোনো feature flag / env / dispatch দ্বারা enable কিনা |
| ৫টা prompt router — প্রতিটা ভিন্ন domain বা specialization serve করে কিনা |
| ৩টা route scanner — প্রতিটা ভিন্ন concern scan করে কিনা |
| multicloud 403 — by-design external auth কিনা (Firebase/Supabase) |
| ১২টা shadow endpoint — কোনোটা versioned API (v1 vs v2) কিনা |

### ধাপ ২ — GOVERNANCE CENTRALIZE (৩-৫ দিন)

স্তর ১ (G1-G6)। এটা whack-a-mole এর root fix — করলে ভবিষ্যতে rollup-এ এই cascade আর ঘটবে না। সব S/M effort, low risk।

### ধাপ ৩ — DEAD/INCOMPLETE সাফ (verify পরে) (২-৩ দিন)

স্তর ২ (D1-D8)। শুধু verify হওয়া dead code। Phase 0 "zero alive-looking dead" গেট পূরণ।

### ধাপ ৪ — KNOWN CI FAILURES FIX (১ দিন)

- M1 (security.py module-level import) → security_rate_limit ৪× fail ঠিক
- M2 (test minimal FastAPI) → collection robust
- G3 (gateway test hardcoded সরাও) → maintenance burden দূর
- multicloud 403 → ধাপ ১ verify-র ফলাফল অনুযায়ী (external auth হলে test reframe, নাহলে middleware add)

### ধাপ ৫ — MECHANICS সরল (পৃথক PR, ১-২ সপ্তাহ)

স্তর ৩ (M3-M6)। প্রতিটা পৃথক PR। দর্শন পূরণ করে কিন্তু breaking change হতে পারে — সাবধানতার সাথে।

### ধাপ ৬ — SECURITY/ARCHITECTURE (দীর্ঘমেয়াদী)

- C10 (auth dep policy unify) — security PR
- B13/B14 (DeclarativeBase unify) — data safety PR
- প্রতিটা আলাদা PR, human review mandatory

---

## অংশ ৬ — মেট্রিক্স: "সরল হয়েছে" কীভাবে জানব

আগের মেট্রিক্স ছিল "LOC কমল"। নতুন মেট্রিক্স দর্শন-ভিত্তিক:

| মেট্রিক্স | বর্তমান | টার্গেট | কোন নীতি |
|----------|---------|---------|-----------|
| Generator list সংখ্যা | ৪ | ১ | #1 centralize |
| Route scanner সংখ্যা | ৩ | ১ (verify পরে) | #1 centralize |
| Auth dep সংখ্যা | ৬ | ২-৩ (policy doc সহ) | #6 think before acting |
| Hardcoded CI threshold | ২+ (gateway_context) | ০ | #1 centralize |
| "Alive-looking but dead" feature | ১০+ | ০ | #2 complete circles |
| Pre-existing CI failure (masked) | ৫ (multicloud + ৪ security) | ০ | #8 verify |
| Function-level import (monkeypatch bypass) | ১ (security.py) | ০ | #8 verify |
| Shadow endpoint (same path, diff handler) | ১২ | ০ | #1 centralize |
| Dead code LOC (verified) | ~৫,০০০ | ০ | #2 complete circles |
| Boilerplate property সংখ্যা | ৩৬ identical | ১ `__getattr__` | #9 sustainable cost |
| Test env-dependent failure | ২+ confirmed | ০ | B1 verified reliability |

---

## অংশ ৭ — "NOT Simplification" তালিকা (স্পষ্ট)

এই প্ল্যানে যা simplification হিসেবে গণ্য নয়:

1. **capability deletion without verification** — দর্শন #2 "complete circles" লঙ্ঘন
2. **test softening to make CI green** — AGENTS.md §2.21 "NO TEST MANIPULATION" লঙ্ঘন
3. **auth dep unification without policy doc** — দর্শন #6 লঙ্ঘন (কোনটা কখন use স্পষ্ট না থাকলে এখনও worse)
4. **5 prompt router unification without specialization check** — capability loss risk
5. **manualChunks / bundle optimization** — UI behavior (bundle size) পরিবর্তন
6. **MCP federation consolidation** — external integration contract, breaking
7. **pgvector → alternative migration** — data layer, breaking
8. **Bengali normalizer rewrite** — B5 battlefield, native depth

---

## উপসংহার

আগের অডিট ছিল **"জটিল জিনিস খুঁজে সরল করো"** — ৮২ findings, কিন্তু কোনো দর্শন ছাড়া।

এই প্ল্যান হলো **"সংবিধান পূরণ করো, mechanics সরল করো, capability ধরে রাখো"**। তিনটি অক্ষে সাজানো — Governance Centralize, Dead/Incomplete সাফ, Mechanics সরল — যেখানে প্রতিটা কাজ একটি নির্দিষ্ট নীতি পূরণ করে।

**মূল insight**: আগের whack-a-mole এর root cause হলো সংবিধান #1 "centralize governance" লঙ্ঘন — ৪টা আলাদা generator list, ৩টা overlapping scanner, ৬টা ভিন্ন auth dep। এটাই প্রথম fix করতে হবে (স্তর ১)। তাহলে ভবিষ্যতে rollup-এ এই cascade আর ঘটবে না।

**"সব ফাইল মুছে দিলে"** simplification নয় — সেটা capability ধ্বংস। সংবিধান বলছে capability ধরে রাখো (#2 "complete circles"), শুধু governance centralize করো (#1) আর cost সাস্টেইনেবল রাখো (#9)। সেটাই এই প্ল্যান।

---

## রেফারেন্স — পড়া দর্শন ডকুমেন্ট

1. `docs/architecture/SUPREMEAI_CORE_CONSTITUTION.md` — ১০ সার্বজনীন নীতি
2. `AGENTS.md` — ২৩টি operational rule + ৭ agent lane
3. `README.md` — "Capability Before Construction" + ৬ battlefield
4. `docs/plans/architecture/SUPREMEAI_MASTER_PLAN_CANONICAL.md` — Phase 0-6 roadmap
5. `docs/architecture/MODULAR_MONOLITH_TARGET.md` — ৯টি domain boundary
6. `docs/architecture/MULTI_AGENT_OPERATING_MODEL.md` — "PASS ≠ MERGE" দর্শন
7. `docs/architecture/FCC_ARCHITECTURE.md` — central small, local owned
8. `docs/architecture/RISK_TIERED_AUTONOMOUS_SAFETY_PIPELINE.md` — "simple by default, deep by risk"
9. `docs/architecture/GOVERNED_MULTI_AGENT_DECISION_ARCHITECTURE.md` — cost-minimized + continuous security
10. `docs/agents/GOLDEN_RULES.md` — ১০ one-liner rule
11. `architecture-rules.yml` — cross-circle forbidden imports (data-driven)
12. `docs/architecture/module_contract.schema.yaml` — module MUST declare what
13. `LESSONS_LEARNED.md` — ভুল + শেখা ইতিহাস
14. `docs/architecture/service_registry.yaml` — ৩rd-party service কেন আছে

---

## পরিশিষ্ট — আগের ৮২ ফিল্ডিং ম্যাপিং

| শ্রেণী | সংখ্যা | কী করব |
|--------|-------|--------|
| ✅ KEEP (দর্শন পূরণ করে, simplify করার দরকার নেই) | ৩ | আলাদা security/architecture PR |
| 🟡 REFRAME (দর্শন-ভিত্তিক নতুন justification) | ১২ | নতুন প্ল্যানে অন্তর্ভুক্ত |
| ❌ DROP (ফলাফল পরিবর্তন বা কোনো লাভ নেই) | ৬ | বাদ |
| 🔵 RECLASSIFY as DEAD REMOVAL (Phase 0 continuation) | ১১ | স্তর ২ এ অন্তর্ভুক্ত |
| 🟠 RECLASSIFY as MECHANICS (sustainable cost) | ৭ | স্তর ৩ এ অন্তর্ভুক্ত |
| ⚪ বাকি (যথাযথ simplification) | ৪৩ | স্তর ১-৩ এ ছড়িয়ে আছে |

**মোট কাজ**: ~৫০টি (আগের ৮২ থেকে কম, কারণ কিছু merge হয়েছে, কিছু drop)। সবই একটি নির্দিষ্ট নীতি পূরণ করবে — নাহলে simplification নয়।
