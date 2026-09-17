# SupremeAI সম্পূর্ণ পুনঃপরীক্ষা (Full Recheck) V3 — ২০২৬-০৯-১৭

**পরিধি:** মূল রিপো (root) থেকে সম্পূর্ণ recheck → নতুন defect বিশ্লেষণ → সম্পূর্ণ তালিকা (বাংলা)।
**ভিত্তি কমিট:** `c64ea07f` (V2 পোস্ট-ফিক্স সিরিজ `b6dd56ec..c64ea07f` — CI blocker ৪টি, latent test failure ২টি, Plan #005/#006 evidence refresh সহ)।
**পূর্বসূরি:** `SUPREMEAI_FULL_RECHECK_V2_2026-09-17_BANGLA.md` — V2-এর প্রতিটি open আইটেম এই অডিটে পুনঃযাচাই করা হয়েছে (নিচে per-item status)।

---

## পার্ট ১ — 🚨 এই অডিটের সবচেয়ে বড় আবিষ্কার: নাইটলি গেট প্রতি রাতে লাল, কেউ খেয়াল করেনি

লাইভ GitHub Actions রান-হিস্টরি টেনে দেখা গেল:

| Workflow | সর্বশেষ ফলাফল | রোগনির্ণয় |
|---|---|---|
| CI Pipeline (main, 08:28) | ✅ success | main সবুজ-পথে আছে |
| **Scheduled Deep Audit (08:29)** | ❌ **failure** | ২টি job লাল: Mission Reliability Gate + Heavy Analysis (Duplicate Detector) |
| DB Retention Prune (08:47) | ✅ success | — |

### B-V3-01: Mission Reliability Gate — পরিচয়প্রকাশ থেকেই প্রতি রাতে FAIL (deterministic)

- লক্ষণ: `pass^3 = 0.6699 < 0.8`, **তিনটি রানেই অভিন্ন 50/57** — ফ্লেকি নয়, deterministic ৭টি mission ভাঙা।
- মূল কারণ (রান-লগ + লোকাল পুনঃপ্রমাণ):
  1. `tests/missions/test_mission_orchestration.py::TestMissionsAPI` (৭টি টেস্ট)-এর `missions_api_tables` fixture **sqlite backend assert করে** (`assert engine.url.get_backend_name() == "sqlite"`);
  2. অথচ `scheduled-deep-audit.yml`-এর mission-reliability-gate জবে **postgres:16-alpine + redis service container** দেওয়া → ambient `DATABASE_URL` → postgres engine → ৭টি setup ERROR;
  3. L1 Reliability Moat (ধাপ ৩) চালুর দিন থেকেই এই গেট সবুজ হয়নি — **gate নিজেই ভাঙা অবস্থায় "রাতের পাহারা" ভান করছিল**। V2-এর শিক্ষার হুবহু পুনরাবৃত্তি: gate চলছে কিনা, সেটা আগে যাচাই করতে হয়।
- **লোকাল প্রমাণ:** `DATABASE_URL=sqlite+aiosqlite:///...` দিয়ে suite চালানো → **৫৭/৫৭ passed (21s)**।
- **ঠিক (এই সেশনে pushed):** জব থেকে অপ্রয়োজনীয় postgres+redis service বাদ + স্টেপে `DATABASE_URL: sqlite+aiosqlite:///./test.db` + কারণসহ বাংলা কমেন্ট।
- **শিক্ষা:** nightly gate-এর প্রথম লাল রাতেই নয়েফিকেশন/ট্রায়াজ দরকার — ৭ রাত ধরে লাল গেট = গেটটাই অর্থহীন।

### B-V3-02: Duplicate Logic Detector — ৩টি CRITICAL, nightly Heavy Analysis লাল

`--engine file_level import` রানে ৩টি critical (১০০%/৯৮%/৯০% জোড়া):

| # | জোড়া | যাচাই ফলাফল | সিদ্ধান্ত |
|---|---|---|---|
| 1 | `workspace_feature_routes_shim.py` ≡ `tier_s_routes.py` (**100% byte-identical**) | দুটোই `workspace_feature_routes.py`-এর re-export bridge; **shim-এর importer শূন্য** | ✅ **shim ডিলিট (pushed)** |
| 2 | `frontend/src/components/SupremeComponents.tsx` ≈ `ui/GlassUiPrimitives.tsx` (98%) | **দুটোরই সম্পূর্ণ repo-তে শূন্য রেফারেন্স** (import/স্ট্রিং-lazy সহ স্ক্যান) — দুটোই dead file | ✅ **দুটোই ডিলিট (pushed)**; `pnpm build` ✓ 11.55s |
| 3 | `core/plugins/experimental/base.py` ≈ `official/base.py` (90%) | ফাইলের নিজ docstring-এ **কারণসহ ডকুমেন্টেড**: official লেয়ার back-compat shim, re-export করলে package-level **import cycle** তৈরি হতো — M0-D সিদ্ধান্ত | ✅ **detector-এ `EXEMPT_FILE_LEVEL_PAIRS` ছাড় + কারণের উৎস কমেন্ট (pushed)**; কোড ডিলিট নয় |

- **লোকাল প্রমাণ:** ফিক্সের পর detector re-run → **critical = 0, exit 0**।
- নোট: `workspace_feature_routes.py ↔ tier_s_routes.py`-এর মধ্যে একটি অদ্ভুত **আন্তঃ-re-export চক্র** রয়ে গেল (bridge একে অপরকে import করে; কাজ করে কারণ lazy import) — সংহতির সুযোগ (P2-০৪)।

---

## পার্ট ২ — ✅ এই সেশনে ঠিক হওয়া (পুশকৃত, সবগুলো লোকাল প্রমাণ-সহ)

| ID | ফিক্স | ফাইল | প্রমাণ |
|---|---|---|---|
| B-V3-01 | Mission gate sqlite-সংযোজন + service বাদ | `.github/workflows/scheduled-deep-audit.yml` | লোকাল ৫৭/৫৭ (21s); লগ-নির্ণয় |
| B-V3-02 | ৩টি critical duplicate নিষ্পত্তি | ৩ ফাইল ডিলিট + `duplicate_detector.py` ছাড়-তালিকা | detector exit 0, critical 0; `pnpm build` ✓ |
| B-V2-03 **(V2-এর #1 ROI, এখন বন্ধ)** | `check_user_budget` **fail-closed** (production/staging), dev/test-এ fail-open + loud log; placeholder `redis://<your-redis-url>` এখন সৎ `RuntimeError` | `backend/core/llm/token_budget.py` | টেস্ট আপডেট: env-নীতি ৩ কেস + unconfigured-এ RuntimeError → **26/26 pass** |
| C-V2-03 (V3-এ পুনঃনিশ্চিত) | `maintenance.yml` erdantic-step-এর `ci_policy.py` পাথ `.github/...` → `../.github/...` — ERD-fail evidence এখন সত্যিই লেখা হয় | `.github/workflows/maintenance.yml` | লোকাল invoke: JSON evidence emit ✓ |
| D-V3-01 | `plan_registry.json` পুনঃজেনারেট — **PLAN_006 (এবং মোট 169 doc) এখন নিবন্ধিত**; V2-এর "registry-তে PLAN_006 নেই" বন্ধ | `docs/plans/plan_registry.json` | `lint_plans.py --json` re-run; দুটো id-ই উপস্থিত |

**স্যানিটি রান (ফিক্স-পরে):** `test_token_budget` 26/26 ✓ · `test_memory_pkg_integrity` (archive guard) ✓ · `test_module_operational_contracts` + missions orchestration 30/30 ✓ · backend ruff (পরিবর্তিত ফাইল) All checks passed ✓ · frontend build ✓

---

## পার্ট ৩ — 🔴 P0: এখনও খোলা, উচ্চ-ঝুঁকি (V2 থেকে পুনঃযাচাইকৃত)

| ID | অবস্থান | সমস্যা | আজকের যাচাই |
|---|---|---|---|
| B-V2-01 | `core/llm/llm_gateway/gateway.py:82-84` | `_router` ডিফল্টে **production-এ `MagicMock()`** — LLM hot path-এ fake object; `await`-এ TypeError → debug-লেভেলে swallow | ✅ পুনঃনিশ্চিত — `from unittest.mock import MagicMock; self._router_obj = MagicMock()` এখনও ওই লাইনে |
| B-V2-04 | `api/routes/admin_auth.py:19,58` | `_in_memory_jwt_blacklist` **শুধু পড়া হয়, কোথাও লেখা হয় না** → Redis-ছাড়া admin JWT revocation নীরব no-op | ✅ পুনঃনিশ্চিত — সমগ্র repo-তে কোনো `.add()`/set-পাথ নেই (শুধু check) |

---

## পার্ট ৪ — 🟠 P1: খোলা, গুরুত্বপূর্ণ

1. **Frontend ভুয়া-ডেটা অঞ্চল** — `components/admin/shared/DynamicPanel.tsx:51` এখনও `metrics?.latency_p50_ms || 42` — মেট্রিক না থাকলে **"42ms" ভান করে দেখায়**। V2-এর F-V2 তালিকার অন্য জোনগুলোও (guest "demo responder", মৃত profile button) অপরিবর্তিত। *(আজ পুনঃনিশ্চিত)*
2. **Frontend `: any` = ৬৫টি** (`src`-তে বর্তমান গণনা) — F-12-এর অবশিষ্টাংশ; টাইপ-সেফটি দুর্বল। *(আজ গণিত)*
3. **`@supabase/supabase-js` mcp package.json-এ অঘোষিত** — `dynamic/tool.registry.ts:35`-এ dynamic import; transitive resolution বদলালে DB-driven registry নীরবে `[]` ফেরত দেবে। *(আজ পুনঃনিশ্চিত: declared=False)*
4. **F-14 drift অপরিবর্তিত** — mcp package: typescript `^7.0.2`, zod `^4.5.4` (root frontend-এর সাথে অসঙ্গতি), ioredis `^6.0.0`; lockfile-জুড়ে shared package major-drift বহমান। *(আজ পুনঃনিশ্চিত)*
5. **plans governance lint লাল** — `lint_plans.py --check` = **597 error-level finding** (প্রধানত `SUPREMEAI_MASTER_PLAN_CANONICAL.md`-এর ৫টি broken `supersedes` link — `docs/archive/plans/architecture/`-এ টার্গেট নেই) + versioned-filename/unverified-claim সতর্কতা। সেই সাথে **১১৯ doc status-হীন** (V2)। এই চেক কোনো workflow-তে blocking নয় — তাই নীরব। *(আজ চালিত)*
6. **Workspace-স্তরের re-export চক্র** — `workspace_feature_routes.py` → `tier_s_routes.py` (bridge) → `workspace_feature_routes.py`; দুই bridge-ই একই `__all__` বহন করে। ক্যানোনিক্যাল মডিউলে `register_tier_s_routes` সরাসরি সংজ্ঞায়িত করে এক bridge বাদ দেওয়া উচিত।

---

## পার্ট ৫ — 🟡 P2: মাঝারি (V2-এ শনাক্ত, আজ পুনঃতালিকাভুক্ত; নতুন যাচাই ছাড়া)

1. **Unbounded in-memory store**: byoc `encrypted_vault`, markdown `jobs_db`, `RECENT_ACTIVITIES`, frontend alerts — maxlen/TTL নেই; Render 512MB tier-এ ভবিষ্যৎ leak-vector।
2. **MCP Control Tower টেস্ট কভারেজ ~৭%** (৮৯ static tool-এর মধ্যে assert-সহ ~৬); mutation/authority tool ১০টি (`policy.approve`, `autonomy.kill_switch`, `action.render_deploy`, `client.set_role`…) অটেস্টেড; ৬টি print-only suite দৌড়ায় কিন্তু কিছুই প্রমাণ করে না।
3. **CI evidence feedback loop নেই** (C-V2-06): ৬ workflow evidence JSON লেখে, পরবর্তী সিদ্ধান্ত কোনোটা পড়ে না — forensic trail আছে, প্রতিক্রিয়া নেই।
4. **secrets_registry.yaml ড্রিফট** (C-V2-04): ৩২ ব্যবহৃত-অনিবন্ধিত / ১৮ নিবন্ধিত-অব্যবহৃত।
5. **`load_exemptions()` মৃত** (C-V2-05): constitution-এর exceptions.yml স্কিমা কোথাও call হয় না।

---

## পার্ট ৬ — 🟢 P3: হাইজিন / ডকুমেন্টেশন সততা

1. **Meta-doc মৃত দাবি** (আজ পুনঃনিশ্চিত):
   - `STATUS.md:77` — মুছে-ফেলা `hierarchical_tree.py` + `context_collector.py`-কে এখনও "Implemented … 100% test coverage" বলছে;
   - `STATUS.md:110` — "Pending Tasks — **None!** All … 100% complete" — এই অডিটের তালিকাই বিপরীত প্রমাণ;
   - `README.md:68` — `MASTER_PLAN.md` লিংক **ফাইলটি রিপোতেই নেই** (ক্যানোনিক্যাল: `docs/plans/architecture/SUPREMEAI_MASTER_PLAN_CANONICAL.md`)।
2. **Log-less except বিশাল স্তর** — বর্তমান AST গণনা: **3,396 handler-এর মধ্যে 1,165-এ body-তে কোনো লগিং/ডায়াগনস্টিক কীওয়ার্ড নেই** (V2-এর ৬৭৬ কঠোর ক্রাইটেরিয়ায়)। বেশিরভাগ fail-closed কিন্তু নীরব; উচ্চ-ব্লাস্ট নমুনা (V2): `auth_middleware.py:65`, `rbac.py:125,255`, `auth.py:604` (`from None`), `supabase_vector_backend.py:148`, `n8n_webhooks.py:45`। **সাইলেন্ট pass-handler = ৪**, যার ২টি production (`ecosystem_admin.py:48` fall-through, `deep_research.py:344` reasoning isolation) — দুটোই ইচ্ছাকৃত + কমেন্টেড (B-12 ডকট্রিন অনুযায়ী বাংলা কমেন্ট-আপগ্রেড করা যায়); ২টি test-ফাইলে। বেয়ার `except:` = ১ (`examples/sample_buggy.py` — ইচ্ছাকৃত নমুনা)।
3. **`scripts/advanced_analysis/duplicate_detector.py` নিজেই ruff-অপরিষ্কার** (১৫টি pre-existing: F401/F541/S112/BLE001/PERF102/EXE001) — আজকের এডিট নয়, সব পুরনো লাইন; `scripts/` CI ruff-স্কোপে না থাকায় নীরব।
4. **unittest.mock ডিফেন্সিভ ব্যবহার**: `database/db_repository.py:5,43` (mock-rejection guard — গ্রহণযোগ্য), `services/llm/providers.py` (Bangla-কমেন্টেড কোয়ার্ড) — তবে `tools/self_planner.py`-র `_MockNetworkX` shim এখনও dormant।

---

## পার্ট ৭ — ✅ রিগ্রেশন যাচাই: পূর্ববর্তী ইনভেস্টমেন্টগুলো সুস্থ

| ইনভেস্টমেন্ট | আজকের অবস্থা |
|---|---|
| PLAN_002 Context Compaction / PLAN_001 Caching | কোড উপস্থিত; V2 থেকে কোনো regression রিপোর্ট নেই; CI Pipeline green |
| M3 ARCHIVE + `TestM3ArchiveGuard` | ✓ guard suite pass — ৬টি archive-কৃত মডিউল ফিরে আসেনি |
| PLAN_004 Memory Distillation | ✓ `unified_memory.py` kill-switch সহ উপস্থিত; PLAN_006 এখন registry-তে নিবন্ধিত |
| PLAN_003 Repo Map + CI consolidation | ✓ ci-mcp-build স্যুট রেফারেন্স অক্ষত |
| L1 Mission Gate | **সংশোধিত** — নীতি সঠিক ছিল, বাস্তবায়ন-পরিবেশ ভুল ছিল (পার্ট ১); এখন sqlite-বাইন্ডিং সহ সৎভাবে চলবে |
| L3 False-Assurance Purge / B-12 | ✓ নতুন AST স্ক্যানে **কোনো নতুন সাইলেন্ট pass-handler নেই**; production-এ ২টি ডকুমেন্টেড-ইচ্ছাকৃত |
| Plan #005/#006 | দুটোই `proposed` — বাস্তবায়ন অপেক্ষায়; registry-নিবন্ধন আজ ঠিক হলো |

---

## পার্ট ৮ — উন্নয়ন পরামর্শ: অগ্রাধিকার-ক্রম (মূল্য/প্রচেষ্টা)

1. ~~Token-budget fail-open~~ ✅ (আজ বন্ধ — B-V2-03)।
2. **Gateway-র MagicMock অপসারণ** (B-V2-01) — `_router=None` + honest error; সবচেয়ে ঝুঁকিপূর্ণ অবশিষ্ট আইটেম, পরিবর্তন ছোট।
3. **JWT revocation-কে বাস্তব করা** (B-V2-04) — logout/revoke endpoint থেকে blacklist-এ **লেখা** শুরু করা; Redis-ছাড়া মোডে সৎ warning ইতিমধ্যে আছে, লেখার পাথ দিলেই হবে।
4. **Nightly লাল-গেট নোটিফিকেশন** — Mission Gate/Heavy Analysis লাল হলে issue+notification; নইলে B-V3-01-এর মতো ৭ রাত নীরবতা আবার হবে।
5. **Frontend ভুয়া-ডেটা জোন** — `|| 42`-জাতীয় constant → loading/empty state; dead-file তালিকার আরও ~৮৫টি disposition।
6. **MCP critical-১০ tool-এ assert test** + `@supabase/supabase-js` ঘোষণা।
7. **plans governance পরিষ্কার** — MASTER_PLAN_CANONICAL-এর ৫টি broken lineage link ঠিক বা archive-টার্গেট তৈরি; এরপর `--check` কে maintenance-এ blocking করা।
8. **Unbounded cap-পাস** + workspace-bridge চক্র সংহতি।
9. **Meta-doc সততা পাস** — STATUS.md/README.md-এর মৃত দাবি মোছা; STATUS-কে generated-truth বানানো।

**যা করা উচিত নয় (V2 থেকে বহমান):** নতুন plan ডক লেখা (PLAN_005/006 বাস্তবায়ন ছাড়া); dead frontend কোড জমিয়ে রাখা; CI-তে নতুন `continue-on-error`; লাল nightly গেট উপেক্ষা করা।

---

## পার্ট ৯ — সততার স্বীকারোক্তি

- এই অডিট static analysis + লোকাল pytest সাবসেট + **লাইভ GitHub Actions রান-লগ/artifact**-এর উপর ভিত্তি করে; সম্পূর্ণ backend suite (৩,২৬৯+ handler) বা staging runtime-প্রমাণ এই সেশনে চালানো হয়নি।
- P2/P3-এর কিছু আইটেম V2 থেকে বহনকৃত (চিহ্নিত); "আজ পুনঃনিশ্চিত" লেখা আইটেমগুলো এই সেশনে সরাসরি যাচাইকৃত।
- Log-less except গণনা (1,165) heuristic-নির্ভর — কীওয়ার্ড-ভিত্তিক; ম্যানুয়াল ট্রায়াজ বাকি।
- Mission gate-ফিক্সের CI-প্রমাণ পরবর্তী nightly রানেই চূড়ান্ত হবে (লোকালে ৫৭/৫৭ প্রমাণিত)।
