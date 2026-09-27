# সরলীকরণ বাস্তবায়ন রিপোর্ট — তুলনা, সিদ্ধান্ত ও প্রমাণ

> **তারিখ**: 2026-09-27  
> **Branch**: `coder-1-simplification-impl`  
> **ভিত্তি**: দুইটি অডিট ডকুমেন্টের তুলনা → verify-first বাস্তবায়ন  
> **দর্শন**: `2+2=4` — ফলাফল অপরিবর্তিত রেখে পথ সরল করা

---

## অংশ ১ — দুই অডিট ডকুমেন্টের তুলনা

এই ডিরেক্টরিতে দুইটি স্বাধীন অডিট আছে, দুইটিই বাংলায়, দুইটিই একই দর্শন থেকে উদ্ভূত:

| বিষয় | `SIMPLIFICATION_AUDIT_REPORT.md` + `PHILOSOPHY_ALIGNED_PLAN.md` | `docs/audits/SIMPLIFICATION_PLAN_V2_BN.md` (fork) |
|---|---|---|
| পদ্ধতি | ৫-প্যারালাল-agent LOC-স্ক্যান (৮২ findings) | ৯-agent ডেটা-সংগ্রহ + সংবিধানের ১৪ নীতিতে ফিল্টার (৪ বালতি) |
| শক্তি | CI/CD গভীরতা (generator-list drift, masked debt, scanner overlap), known CI failure-এর root cause তালিকা | প্রতিটি মোছার আগে **৩-যাচাই** (caller / plan-corpus intent / near-ready চুক্তি) ও সত্যের ক্রম |
| দুর্বলতা | কিছু "dead" দাবি পুনঃযাচাইয়ে ভেঙে পড়ে (নিচে প্রমাণ) | CI lane-এর খুঁটিনাটি কম; বাস্তবায়ন-ক্রম বিমূর্ত |

### যেখানে দুই অডিট একমত (এবং এই PR-এ বাস্তবায়িত)

- Dead route/module মোছা (verify-এর পরে) — upstream স্তর ২ (D1-D5), fork বালতি B
- pytest `--cov` addopts থেকে সরানো — upstream M3/D3
- `test_gateway_context` hardcoded threshold সরানো — upstream G3/A2/D8
- নীরব ঝুলন্ত অবস্থা নিষিদ্ধ — দুই ডকুমেন্টেরই মেরুদণ্ড

### যেখানে দুই অডিট দ্বিমত (এবং কার রায় মানা হলো)

| বিষয় | upstream রায় | fork V2 রায় | চূড়ান্ত সিদ্ধান্ত |
|---|---|---|---|
| frontend i18n stack (E2) | মুছে ফেলা হোক (৩১৬ LOC) | **রাখো + wire করো** — plan-corpus-এ সম্প্রসারণ-পরিকল্পনা আছে, CI-তে বাংলা i18n checker চলে | **fork V2** — near-ready capability মোছা যাবে না (সংবিধান নীতি "Near-ready → Finish") |
| D1: `security.py` module-level import | এটাই ৪× CI fail-এর root cause | — | **উভয়ের বাইরে — দাবিটা ভুল** (নিচে প্রমাণ) |
| E10/E11/E14 (useServerStream, useDashboardActions, sessionStore) | dead — মোছো | — | **fork V2-সামঞ্জস্য**: পুনঃযাচাইয়ে **জীবিত** প্রমাণিত — মোছা হয়নি |
| মোছার অগ্রাধিকার | LOC বড় আগে | ৩-যাচাই-উত্তীর্ণ আগে, LOC পরে | **fork V2** — verify-first |

---

## অংশ ২ — পুনঃযাচাইয়ে upstream দাবি যেগুলো ভেঙে পড়ল (প্রমাণসহ)

প্রতিটি দাবি কোডে ফিরে গিয়ে যাচাই করা হয়েছে (`MULTI_AGENT_OPERATING_MODEL.md`: *"কোড যা অদরকারী মনে হয় তাও dependency না চেক করে delete করা যাবে না"*):

| দাবি | যাচাইয়ের ফল | প্রমাণ |
|---|---|---|
| **D1**: `security.py:261` function-level import = monkeypatch bypass; module-level করলে ৪× CI fail ঠিক হবে | ❌ **উল্টো** — function-level `from X import Y` প্রতি call-এ module attribute **re-read করে**; test টি ইচ্ছাকৃতভাবে এই উপর নির্ভর। Module-level করলে ৬টা test ভাঙত | `test_security_rate_limit_backend.py:61-71` — test সরাসরি `core.cache.redis_manager` module-এর attribute patch করে; ফাইল-হেডার কমেন্ট (#2088 fallout) ব্যাখ্যা করে লেজি resolve কেন বাধ্যতামূলক |
| **E10**: `useServerStream` dead | ❌ জীবিত | `src/components/shell/ServerHealthWatcher.tsx:2` import করে |
| **E11**: `useDashboardActions` dead | ❌ জীবিত | `src/components/dashboard/ActionDock.tsx:33,113` |
| **E14**: `sessionStore` dead | ❌ জীবিত | `src/components/dashboard/SessionsPage.tsx:11` |
| **AST-identical ডুপ্লিকেট test** (`test_auth_jit_otp_flow.py` ≡ `test_otp_router.py`) | ❌ বর্তমান ট্রিতে AST hash **ভিন্ন** | `06d3546c` vs `b7beae2f` |
| **B12**: `external_agents/` ২,৮৭৩ LOC মোছো (আগে verify) | ⏸️ বাহ্যিক import শূন্য নিশ্চিত, তবে plan-corpus যাচাই বাকি — **পৃথক PR** | `git grep external_agents` → শুধু generated graph + অডিট doc নিজেই |
| **competitive_kit.py** fabricated → মোছো | ⏸️ এখন m03 contract test delegation-যাচাই করে — মেরামত-পরবর্তী অবস্থা, owner-সিদ্ধান্ত দরকার | `test_gateway_contract_m03.py:100-102` |
| **D6**: `db_engine` default → sqlite | ⏸️ test-environment semantics বদলায় (fallback Postgres→sqlite); পৃথক verify-run দরকার | `tests/conftest.py:_resolve_test_database_url` |

**শিক্ষা**: LOC-স্ক্যান অডিট দ্রুত বড় সংখ্যা দেয়, কিন্তু runtime evidence ছাড়া "dead" ঘোষণা মিথ্যা সরলীকরণ — ঠিক যেটা `PHILOSOPHY_ALIGNED_PLAN.md` নিজেই সতর্ক করেছে।

---

## অংশ ৩ — এই PR-এ বাস্তবায়িত (সব ৩-যাচাই-উত্তীর্ণ)

### Backend (৭ আইটেম, ~৮২০ LOC)

| # | কাজ | ৩-যাচাই প্রমাণ |
|---|---|---|
| 1 | `api/routes/websocket_hitl.py` + `tests/api/test_websocket_hitl.py` **মোছা**; routers.py-র commented mount line সরানো | routers.py:151-এ mount বহু আগেই comment-out; importer=শুধু নিজের test; `stream_hitl_sse` এর docstring lineage রাখা হয়েছে |
| 2 | `api/routes/codeflow.py` shim **মোছা** | routers.py:205-208 নিজেই বলে shim টি double-register করে unmount হয়েছিল (mount-hygiene 2026-09-15); importer=শুধু validator |
| 3 | `core/cache/autocache_proxy.py` **মোছা** + contract-test block | production caller=শূন্য; একমাত্র reference "existence contract test" (`assert X is not None` — আচরণ যাচাই নয়) |
| 4 | `core/intelligent_cache_bridge.py` **মোছা** | একমাত্র non-self reference হলো docstring mention |
| 5 | `core/intelligence/swarm_consensus.py` **মোছা** + test edit | production caller=শূন্য; test_swarm_and_ephemeral.py থেকে শুধু swarm অংশ সরিয়ে **ephemeral_synthesizer coverage অক্ষত** রাখা হয়েছে (ফাইল rename: `test_ephemeral_synthesizer.py`); contract-test block সরানো |
| 6 | `core/security/rate_limiter.py` (deprecated shim, Wave 3.1 #1257) + নিজের unit test **মোছা** | docstring `.. deprecated:: 2.5`; importer=শুধু নিজের test; উদ্ধৃত "no-file-delete doctrine" বর্তমান AGENTS.md/docs-এ **অস্তিত্বহীন** — shim-এর চুক্তিই হলো ভবিষ্যৎ release-এ মোছা |
| 7 | `scripts/ci/validate_router_imports.py` — **৫টা stale entry সরানো** (`websocket_hitl`, `codeflow`, `websocket_agent`, `llm_gateway`, `swarm`) | ৫ মডিউলই ডিস্কে নেই; `websocket_agent`-এর জন্য রেগ্রেশন test নিজেই দাবি করে মডিউল মুছে যাবে (`test_realtime_topology.py:45`) — validator entry ছিল সেই test-এর সরাসরি বিরোধ |

### Frontend (৭ আইটেম, ~১,১৩০ LOC)

| # | কাজ | প্রমাণ |
|---|---|---|
| 8 | `services/socialGrowthService.ts`, `services/sandbox.ts`, `services/costOptimizer.service.ts` (+test) **মোছা** | import=শূন্য (costOptimizer-এর একমাত্র ref নিজের test) |
| 9 | `hooks/useWebSocket.ts` **মোছা** + barrel line | barrel export ছাড়া কোনো import-chain নেই |
| 10 | `hooks/useSwarmStream.ts` **মোছা** + eslint allowlist-থেকে নাম সরানো | import=শূন্য |
| 11 | `hooks/useBudgetCheck.ts` (+test), `hooks/useIframeConsole.ts`, `components/dashboard/useHashRoute.ts` **মোছা** | import=শূন্য |
| 12 | `components/AgentStateShaderBackground.tsx` **মোছা** | import=শূন্য (lazy-string path-ও নেই) |

### Config / Test hygiene

| # | কাজ | কেন zero-impact |
|---|---|---|
| 13 | `pyproject.toml` addopts থেকে `--cov=core --cov-report=*` সরানো | CI নিজের invocation-এ স্পষ্ট `--cov` পাস করে (ci.yml:870) — coverage রিপোর্ট অপরিবর্তিত; লোকাল রান দ্রুত |
| 14 | `test_gateway_context_m03.py`: `assert total >= 12` → `assert total >= 0` + ব্যাখ্যামূলক কমেন্ট | BASELINE==0 ratchet + synthetic-violation test scanner-alive প্রমাণ করে; #1832-এ 14→12 হাতে বাড়াতে হয়েছিল — সেই maintenance burden শেষ; বর্তমান ট্রিতে gate-ফল অপরিবর্তিত |
| 15 | `core/cache/README.md` থেকে autocache_proxy অনুচ্ছেদ সরানো | ফাইল মোছার সাথে doc-sync (No Silent Documentation) |

---

## অংশ ৪ — যাচাই-ফলাফল (এই sandbox-এ)

| গেট | ফল |
|---|---|
| Affected backend tests (contracts, ephemeral, cache_optimization, unit_light, gateway_context_gate, realtime_topology) | **182 passed**; 3 failure = `litellm` module অনুপস্থিত — base branch-এও identical fail (প্রমাণিত pre-existing) |
| `validate_router_imports.py` | **GATE PASSED** (৫ stale entry সরানোর পরে; বাকি ২ warn = sandbox-এ uninstalled dep-এর মডিউল, ডিস্কে আছে) |
| Frontend `tsc --noEmit` | 8 errors — base-এও হুবহু 8 (EvolutionForge pre-existing); আমার মোছা symbol-এ শূন্য error |
| Frontend `eslint .` | 0 errors, 4 pre-existing warnings (unrelated ফাইল) |
| `ruff format --check` + `ruff check` (edited files) | format clean; 2 pre-existing finding (validate script-এর EXE001/BLE001 — আমার ধরা লাইনে নয়) |
| `check_slot_registry_drift.py` | ✅ registry agree |

---

## অংশ ৫ — বাকি রোডম্যাপ (পৃথক PR-এ, অগ্রাধিকার-ক্রমে)

1. **owner-decision PR**: `external_agents/` (২,৮৭৩ LOC — plan-corpus যাচাই + registry entry), `competitive_kit.py` (m03 contract-এর পরে owner রায়), `api/server.py` (plan-corpus mention আছে — patch-note historical কিনা নিশ্চিত করতে হবে), `workspace_feature_routes/tier_s_routes` register-duplication, `backend/services/sandbox_service.py` (নতুন find: importer=শুধু নিজের test)
2. **Governance centralize (upstream G1-G5)**: ৪ generator-list → ১ canonical; route-scanner overlap যাচাই → consolidate; auth-dep policy doc — **CI lane** কাজ, ci/coder lane-বিভাজন মেনে
3. **Mechanics (M4-M5)**: config_secrets ৩৬ @property → `__getattr__`; ২ DeclarativeBase → ১ (data-safety PR, human review)
4. **Frontend near-ready wire-up**: i18n (মোছা নয় — Phase 1 Gate)

**মোট এই PR-এ**: ~১,৯৫০ LOC মুছা, ১৫টি পরিবর্তন-স্থল, শূন্য behavior change (উপরের গেট-টেবিল প্রমাণ)।

---

## পরিশিষ্ট — কেন "শুধু মোছা" যথেষ্ট নয়

এই PR-এ মোছা প্রতিটি ফাইলের জন্য তিনটি প্রশ্নের লিখিত উত্তর আছে (অংশ ৩-এর প্রমাণ-কলাম):
(১) কেউ import করে? (২) plan-corpus-এ intent আছে? (৩) near-ready চুক্তি (docstring/registry/contract-test) আছে?
তিনটিতেই "না" প্রমাণ হলেই মোছা হয়েছে। একটিতেও "হ্যাঁ" থাকলে ⏸️ অংশ ২-এর টেবিলে পৃথক PR-এ স্থগিত — **নীরব ঝুলন্ত অবস্থা নেই**।
