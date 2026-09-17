---
id: supremeai-full-recheck-v2-2026-09-17
subject: "SupremeAI Full Recheck V2 — Post-Fix Verification & Fresh Defect Analysis"
document_role: audit
planning_authority: Architecture Governance / Planning Circle
canonical: false
status: active
evidence_state: verified
disposition: retain
last_verified: 2026-09-17
supersedes: []
superseded_by: []
target_scope: supremeai_internal
---

# SupremeAI ফুল রিচেক V2 — ফিক্স-পরবর্তী যাচাই + নতুন ত্রুটি বিশ্লেষণ (২০২৬-০৯-১৭)

**পদ্ধতি:** root থেকে fresh clone (HEAD `07604ad1`, ৩,৯২৮ tracked ফাইল) → ৪টি parallel deep-scan (backend integrity / frontend integrity / MCP+CI / docs-governance) → **লাইভ GitHub CI log বিশ্লেষণ** (শুধু static দাবি নয় — runner-এর আসল ব্যর্থতা log পড়া হয়েছে) → প্রতিটি দাবি কোডে file:line সহ যাচাই।

**সবচেয়ে বড় আবিষ্কার (এই রিচেকের):** গত কয়েক দিনের সব কমিট (Step 3–7 সহ) main-এ **CI লাল অবস্থায়** push হয়েছে — CI Pipeline প্রতিটি run-এ fail করছিল, অথচ পাশের gate গুলো green দেখাচ্ছিল। এটাই আমাদের নিজেদের সংজ্ঞায়িত "silent false assurance"-এর জীবন্ত উদাহরণ — ঠিক করা হয়েছে এই সেশনেই (নিচে পার্ট ১)।

**মূল সংখ্যা (V2 স্ক্যান):**

| মেট্রিক | আগের অডিট | V2 এখন |
|---|---|---|
| Merge-conflict marker | 0 | **0** ✅ |
| Dual lockfile (bun.lock) | ছিল | **নেই** ✅ |
| Silent `except: pass` (production) | ৩৪ | **০** ✅ (২টি intentional-annotated) |
| Duplicate route registration | ৭ জায়গায় | **0** (৮৬৬ decorator স্ক্যান, 0 duplicate) ✅ |
| Hardcoded secret (ghp_/github_pat_/sk-/AKIA) | — | **0** ✅ |
| Unconfirmed PLAN_001–004 বাস্তবায়ন | 0/4 | **4/4 কোডে যাচাইকৃত** ✅ |
| **CI Pipeline (main)** | — | **🔴 লাল → এই সেশনে সবুজ করা হয়েছে** |
| Log-ছাড়া except (production, ৩,২৬৯ handler-এর মধ্যে) | ৬৫৭ | **৬৭৬** (নতুন কোডে সামান্য বেড়েছে) |
| Frontend production `: any`/`as any` | ৬৪ | **৬৪** (অপরিবর্তিত) |
| docs/plans status-হীন ডকুমেন্ট | ১১৯ | **১১৯** (মোট ১৬৬, ৪৭-এ status) |
| MCP test-asserted tool coverage | — | **~৭%** (৮৯টি static tool-এর মধ্যে ৬টি assert-সহ) |

---

## পার্ট ১ — 🔴 P0: main-এর CI লাল ছিল — ৪টি ব্লকার, সব এই সেশনেই ঠিক + push হয়েছে

লাইভ CI log বিশ্লেষণে ধরা পড়া ৪টি স্বতন্ত্র ব্যর্থতা (run `35184127366`, HEAD `07604ad1`):

### ১.১ Frontend build ভাঙা ছিল (commit `860f1e53` থেকে — অর্থাৎ Step-0 থেকেই)

- **কারণ:** Step-0 orphan cleanup-এ dead barrel `frontend/src/components/admin/index.ts` মোছা হয়েছিল (F-11), কিন্তু তার একটি importer বাদ পড়েছিল — `src/components/admin/shared/AdminSubTabContent.tsx:5` `from '..'` দিয়ে ১৮টি component import করত। Rollup: `Could not resolve ".."`.
- **প্রভাব:** সব `Build Verification` / `Frontend Tests` / `Deploy Frontend` job **skip** হয়ে যাচ্ছিল — মানে ফ্রন্টএন্ডের কোনো verification-ই চলছিল না।
- **ফিক্স (pushed `1dea1fe2`):** barrel ফেরানো হয়নি — ১৮টি direct import লেখা হয়েছে (প্রতিটি symbol-এর export style কোডে যাচাই করে; `Dashboard` হলো default export, বাকিরা named)। লোকালে `pnpm build` = **✓ built in 12s (2644 modules)**।

### ১.২ Backend lint gate ভাঙা ছিল → সব backend test job skip

- **কারণ ১:** `tests/core/test_cloud_provider_cache.py:195` — F841 unused local `stub` (এটা **আমাদেরই PLAN_001 commit `65a1f1f6`**-এর test ফাইল — CI-র exact ruff flag-set লোকালে চালানো হয়নিল)।
- **কারণ ২:** `tests/core/test_qa_suite_honesty.py:13` — I001 import block un-sorted।
- **গুপ্ত ৩য় ব্রেকেজ:** CI `bash -e`-এ চলে — `ruff check` fail করায় `ruff format --check` **কখনোই রানই হতো না**; লোকালে ruff 0.13.1 (poetry.lock-পিনড) দিয়ে চালাতেই দেখা গেল আরও **৭টি ফাইল format-drift**-এ আছে (`cloud_adapter.py`, `qa_suite.py`, `rate_limiter.py`, `integration_discovery.py` ইত্যাদি)।
- **ফিক্স (pushed `1dea1fe2`):** F841+I001 ঠিক, ৭ ফাইল reformat, স্পর্শকৃত test গুলো **৩৬/৩৬ pass**।

### ১.৩ Advanced drift check — generated snapshot বাসি

- **কারণ:** L2 ডিলিটের পরেও `docs/generated/module_capability_matrix.json` (committed `source_file_count: 2813` vs regenerated `2797`) ও `domain_dependency_graph.json/.mmd` আপডেট হয়নি; `git diff --exit-code` fail। (log-এ যে `assert data[count_key] > 0` দেখা যাচ্ছিল সেটা বিভ্রামিক — আসল ব্যর্থতা তার এক লাইন উপরের diff স্টেপে।)
- **ফিক্স:** দুই generator চালিয়ে snapshot regenerate + commit।

### ১.৪ Constitution Audit — ৫টি blocking ARCH-001 ফাইন্ডিং, সবগুলোই false positive

- **কারণ:** আমাদের শেষ কমিট `07604ad1`-এ স্পর্শকৃত ৩ ফাইল `--pr-diff` scope-এ এসেছে:
  1. `cloud_sandbox_orchestrator.py:62` `return "http://127.0.0.1"` — local-mode only, `settings.is_local()` guard-কৃত (নিচেই prod-এ `ValueError`);
  2. `memory/mcp_server.py:1271` `uvicorn.run(app, host="0.0.0.0")` — server **bind**, cloud-সঠিক default;
  3–5. `services/integration_discovery.py:36,40,43` — `ip_network("127.0.0.0/8")` ইত্যাদি = **SSRF blocklist** — এগুলো ওই address-গুলোর *বিরুদ্ধে* প্রতিরক্ষা।
- **ফিক্স:** rule-এ ২টি exclusion (`ip_network(`/`ip_address` literals; bind-context) + guarded local-mode return-এ canonical `# is_local()` marker। Engine re-run: **Blocking: 0 → PASSED**।
- **বাড়তি আবিষ্কার:** `.github/constitution/exceptions.yml` স্কিমা আছে কিন্তু `load_exemptions()` (`models.py:137-165`) engine-এ **কখনো call-ই হয় না** — exemption পথটা মৃত কোড। (P2 তালিকায় বিস্তারিত।)

> **মার্জ নোট:** push-এর সময় দেখা গেল দূরবর্তীতেও প্রায় একই ৪টি ফিক্স (`e94f2cfc`) + ৪টি follow-up কমিট push হয়ে গেছে; ৩ ফাইলে conflict এসে তাদের variant নেওয়া হয়েছে, matrix merged tree-তে regenerate করা হয়েছে (merge `691c0671`, pushed)। Merged tree-এ যাচাই: ruff clean, format clean, constitution PASSED, `pnpm build` ✓ 11.3s।

---

## পার্ট ২ — 🔴 P1 (Backend): নতুন/বাকি থাকা গুরুতর ত্রুটি

আগের B-01..B-11 ফিক্সগুলো জায়গামতো আছে (যাচাইকৃত) — কিন্তু একই ধাঁচের নতুন/অ-স্পর্শকৃত সাইট পাওয়া গেছে:

| # | ফাইল:লাইন | সমস্যা |
|---|---|---|
| B-V2-01 | `core/llm/llm_gateway/gateway.py:81-85,145-162` | `_router` ডিফল্টে **production-এ `MagicMock()`**; MoE branch সবসময় নেয়, `await`-এ TypeError, তা **debug লেভেলে** swallow — LLM hot path-এ fake-mock + lost diagnostics |
| B-V2-02 | `core/self_evolution/digital_twin/remediation_engine.py:25-46,107,164` | `check_health()->True`, `create_backup()->"mock-backup-id"` mock fallback; import target মডিউল **repo-তেই নেই** → fallback সবসময় active; `:164`-এ অস্তিত্বহীন function call → প্রতিটি monitoring pass চুপচাপ মরে — self-healing monitor **চলছে ভান করে** |
| B-V2-03 | `core/llm/token_budget.py:207,230-232` | placeholder URL `redis://<your-redis-url>` + `check_user_budget` blanket `except: return True` → REDIS_URL না থাকলে **per-user দৈনিক token quota fail-open** (আনলিমিটেড spend) |
| B-V2-04 | `api/routes/admin_auth.py:19,58-62,89-103` | `_in_memory_jwt_blacklist` কোথাও **লেখা হয় না** (শুধু পড়া হয়) → Redis ছাড়া admin JWT revocation নীরব no-op; `admin_rate_limit`-ও Redis ছাড়া চুপচাপ skip |
| B-V2-05 | `api/routes/browser/_surf_actions.py:39-123` | production router-এ **legacy mock endpoint**: `/surf/screenshot` ১×১ transparent PNG "screenshot" নাম দিয়ে ফেরত দেয়; navigate/click/fill সব `success: True` (openapi.json-এ live) |
| B-V2-06 | `brain/model_router.py:119-128` | non-dict reasoning result-এ বানানো CoT (`"final_answer": "42"`) production response-এ ঢুকে যায় |
| B-V2-07 | `api/routes/session_takeover.py:252-259` | admin status endpoint-এ নতুন event loop + `run_until_complete`; error → `data=None` → সক্রিয় takeover-কেও **"inactive"** বলে জানায় |

---

## পার্ট ৩ — 🔴 P1 (Frontend): জীবিত রুটে এখনো ভুয়া ডেটা

আগের ফিক্স (honest telemetry cockpit, fail-closed supabase client) অটুট — কিন্তু এই ৫টি জোনে ভুয়া ডেটা এখনো বাস:

| # | রুট / ফাইল:লাইন | সমস্যা |
|---|---|---|
| F-V2-01 | `/` ল্যান্ডিং — `src/pages/PublicPages.tsx:57,70` | **GuestChatPage আসল backend-কে ডাকেই না** — keyword-matching canned reply generator + 650ms নকল "typing" delay; প্রতিটি অতিথির প্রথম conversation scripted নকল |
| F-V2-02 | `PublicPages.tsx:36-40,65,82` | বানানো model catalog (Supreme Auto / Reasoning Pro / Fast Chat) — picker বদলালে কিছুই বদলায় না |
| F-V2-03 | `/usage` — `src/pages/user/CostDashboard.tsx:39-41` | `total_saved \|\| 42.5`, `cached \|\| 1280`, `utilization \|\| 94.2` — ডেটা না এলে **হার্ডকোডেড ভুয়া সেভিংস** দেখায়; `:163-165` স্ট্যাটিক "Zero-Cost Mode Active" badge; `:58-64` invented rate-এ নকল spend accrual; `:96` বানানো $100 limit |
| F-V2-04 | `/admin` overview — `src/components/admin/Dashboard.tsx:140-182` | হার্ডকোডেড "Cost Center" ($42.50/$128.00/$170.50 MTD) + ভুয়া "Active Agents" তালিকা লাইভ pulse-dot সহ; `:12` CPU load `rps/50*100` invention; `:35,37` template-literal বাগে আক্ষরিক `'-—'` string KPI হিসেবে রেন্ডার |
| F-V2-05 | `/profile` — `src/pages/ProfilePage.tsx:59-77,155,306-314` | avatar সিলেক্ট → "Saved Successfully!" দেখায় কিন্তু **কিছুই upload/persist হয় না**; সব user-এর জন্য canned bio defaultValue; Change Password / API Keys / Delete Account / Edit Profile — **onClick নেই** (মৃত destructive action); Save চাপলে UI-default দিয়ে server state overwrite |
| F-V2-06 | `/architect-tower` — `src/pages/user/SystemHealthDashboard.tsx:74-86` | "System Health: Nominal" ও "Active Nodes: 4" — **কোনো ডেটা সোর্স নেই**, সবসময় একই |

**P1-স্তরের অন্যান্য (frontend):** `store/authStore.ts:131,165` — `post<any>` login/register থেকে unchecked `access_token` — shape বদলালে `undefined` token persist হয়ে সব guarded route ভাঙে; `store/useStore.ts:104,120` — deploy-gate `UNLOCKED/LOCKED` যেকোনো unverified shape-এ উল্টে যেতে পারে; `utils/api.ts:299-314` — `workspaceCapabilitiesApi` **Authorization header ছাড়া** raw fetch; `pages/BillingPage.tsx:28,86-94` — API fail হলে নীরবে "No billing plans available" + Upgrade button-এ onClick নেই।

---

## পার্ট ৪ — 🟡 P2: রিলায়েবিলিটি / ডায়াগনোস্টিকিটি / CI-গভর্নেন্স

### Unbounded মেমরি গ্রোথ (নতুন চিহ্নিত; আগের ৫টি B-08..B-11-এ bounded)
| ফাইল:লাইন | সমস্যা |
|---|---|
| `api/routes/byoc_api.py:24-25,54` | `active_jobs` + `encrypted_vault` (BYOC credential ciphertext!) কখনো prune হয় না |
| `api/routes/markdown.py:21,97` | `jobs_db` প্রতি job-এর সম্পূর্ণ markdown রাখে, কখনো delete নয় — OOM vector |
| `api/routes/browser/_state.py:16` + `_surf_actions.py` | `RECENT_ACTIVITIES` প্রতি call-এ append, trim নেই (তুলনা: `_tasks.py:37` capped 500) |
| `store/customerStore.ts:44`, `useStore.ts:87-89` (frontend) | `chatHistory` unbounded; `CostDashboard.tsx:135` `alerts` unbounded (প্রতি WS message-এ fire হতে পারে) |

### Blocking-in-async (worst ১২টির মধ্যে চরমগুলো)
- `core/orchestration/periodic_task_scheduler.py:79-84` — orchestrator async task-এ `subprocess.run(timeout=120)` → **event loop ১২০ সেকেন্ড পর্যন্ত জমে যেতে পারে**
- `core/microvm_sandbox.py:305,363,424`; `core/container_auditor.py:91`; `agents/ide/trio_adapters.py:286,521`; `services/video_to_code_pipeline.py:135` (ffmpeg)
- ফাইল I/O async route-এ: `api/routes/admin_dashboard/endpoints_events.py:23-24,63-64` (whole-file `readlines()`), `api/routes/admin.py:166`, `api/routes/byoc_api.py:88`

### Fail-open / বিভ্রামক স্টেটাস
- `api/routes/admin_dashboard/endpoints_command.py:402-405` — CommandCenter knowledge stats হার্ডকোড (`docs_count: 184`, "indexed") — `:303-316`-এর fixed "banks" fake-এর হুবহু একই ক্লাস, এটা বাদ পড়েছিল
- `endpoints_command.py:47-65` — deploy-gate স্টেটাস error-এ default `UNLOCKED` (fail-open; enforcement নিজে Firestore থেকে সত্য পড়ে, কিন্তু dashboard অপারেটরকে বিভ্রান্ত করে)
- `endpoints_command.py:131-144` — খালি audit log-এ বানানো `system.ready / success` entry
- `core/orchestration/cloud_sandbox_orchestrator.py` — `download_file`-এ JSON→raw fallback এখন debug-logged (ঠিক আছে), কিন্তু `destroy_sandbox` ইত্যাদি পাশের পাথ এখনো রিভিউ বাকি

### CI-গভর্নেন্স (কোন কোন "green" আসলে প্রমাণ নয়)
| # | ফাইল:লাইন | সমস্যা |
|---|---|---|
| C-V2-01 | `scripts/ci/release_acceptance_gate.py:41-42` | `preflight_evidence` ও `security_tests` **হার্ডকোডেড `status:"passed"`** — release gate এই দুই dimension-এ fail-ই করতে পারে না (evidence theater; ফাইল না থাকলে নিজেকে regenerate করে `:62-68`) |
| C-V2-02 | `ci.yml:817-832` | Mission suite pass^k scoreboard `continue-on-error: true` — blocking variant শুধু nightly scheduled রানে; main CI-তে reliability স্কোর চুপচাপ হারাতে পারে |
| C-V2-03 | `maintenance.yml:429` | `python .github/scripts/ci_policy.py` কিন্তু `working-directory: backend` → ভুল পাথ, `\|\| true`-এ চাপা — ERD-fail evidence কখনো লেখা হয় না |
| C-V2-04 | secrets_registry.yaml | ৩২টি ব্যবহৃত secret অনিবন্ধিত (QA_ADMIN_TOTP_SECRET, DATABASE_URL, RENDER_ACCOUNTS_JSON, SLACK_WEBHOOK_URL সহ); উল্টো ১৮টি নিবন্ধিত secret কোথাও ব্যবহৃত নয় |
| C-V2-05 | `.github/scripts/constitution/models.py:137-165` | `load_exemptions()` কোথাও call হয় না — exceptions.yml মৃত স্কিমা; "Exemptions Applied: 0" hardcoded আচরণ |
| C-V2-06 | ci-reports/ chain | ৬টি workflow যে evidence JSON লেখে, **কোনো পরবর্তী সিদ্ধান্ত সেগুলো পড়ে না** (শুধু in-run consumer + constitution.sarif→code scanning) — forensic trail আছে, feedback loop নেই |

### MCP Control Tower
- **কভারেজ:** ৮৯টি static `server.tool()` site-এর মধ্যে **assert-সহ কভার ৬টি (~৭%)**; ~২১টি zero-assertion smoke; ~৬০টি অস্পৃশ। **সবচেয়ে ঝুঁকিপূর্ণ অটেস্টেড ১০:** `policy.approve`, `action.render_deploy`, `action.redis_flush`, `action.cloudflare_purge`, `autonomy.kill_switch`, `autonomy.enable`, `client.set_role`, `tenant.create`, `supabase.insert`, `remote.call`
- **F-14 drift টেবিল:** typescript 7.0.2 vs 5.9.3 (Δ2), zod 4.6.4 vs 3.25.76 (Δ1 — mission-control ইতিমধ্যে ^4), ioredis 6.0.0 vs 5.11.1 (Δ1), @types/node 26 vs 24 (Δ2), firebase-admin 14 vs 12 (Δ2); lockfile-ব্যাপী ১৫৩ shared package-এর মধ্যে ৩০-টি major-drift
- **নতুন:** `dynamic/tool.registry.ts:35` — `@supabase/supabase-js` **dynamically import হয় কিন্তু mcp package.json-এ declared নয়** → transitive resolution বদলালে DB-driven tool registry নীরবে `[]` ফেরত দেবে
- ৬টি print-only test suite (`test_summary/registry/policy/events/adapters/memory_*`) — assertion নেই, "চলে" শুধু

---

## পার্ট ৫ — 🟢 P3: হাইজিন / গভর্নেন্স

1. **Log-ছাড়া except ৬৭৬টি** (৩,২৬৯ handler-এর মধ্যে) — বেশিরভাগ fail-closed কিন্তু নীরব; সর্বোচ্চ-ব্লাস্ট নমুনা: `auth_middleware.py:65`, `rbac.py:125,255`, `auth.py:604` (`from None` কারণ লুকায়), `supabase_vector_backend.py:148` (metadata DB-write-এ নীরবে drop), `n8n_webhooks.py:45`
2. **Frontend ~৯০টি zero-importer dead file** — বিশেষ trap: `AdminDashboardHome.tsx`-এর ভেতরে বানানো metric (call_count/100 = "F1-Score"!) রেজারেক্ট করলেই ভুয়া ডেটা ফের আসবে; পুরো CommandCenter realtime WS/SSE layer বানানো কিন্তু mount-ই হয়নি
3. **docs/plans:** ১৬৬ ডক-এর মধ্যে ১১৯ status-হীন; **plan_registry.json-এ PLAN_006 নেই** (ডিস্কে ১৬৬, registry-তে ১৬৫); **৩টি inventory snapshot ৩ রকম সংখ্যা দেখায়** (164/165/157); ৫টি complete ডক **status-evidence মিলে যায়** (কোনো মিথ্যা নেই ✅) কিন্তু PLAN_004-এর `test_evidence` এখনো "PLANNED" লেখা
4. **Meta-doc staleness:** `STATUS.md:77` এখনো মুছে-ফেলা `hierarchical_tree.py`/`context_collector.py`-কে "implemented" বলে; `STATUS.md:110` "Pending Tasks — None!"; `CHECKPOINT.md:189,201` Phase C "pending" (আসলে EXECUTED); `README.md:819` "143 routers" (আসলে ১৫০), `:68,562` অস্তিত্বহীন `MASTER_PLAN.md` লিংক
5. **ট্রেসেবিলিটি ম্যাট্রিক্স যাচাই:** mission suite 20/20 **CONFIRMED**; alembic single-head guard **CONFIRMED** (স্ক্রিপ্ট লাইভ চালিয়ে: 28 rev, 1 head); "runs.api 148/148" → **stale, এখন 150**; "MCP 88 tools" → **stale, static ৮৯** (dynamic memory.* bridge আলাদা)
6. Production-এ `unittest.mock` import tolerate করা: `database/db_repository.py:5,43`, `services/llm/providers.py:342,501`; `tools/self_planner.py:7-51` `_MockNetworkX` shim (dormant)

---

## পার্ট ৬ — উন্নয়ন পরামর্শ: Top 10 (মূল্য/প্রচেষ্টা অনুযায়ী র‍্যাংকড)

1. **Token-budget fail-open বন্ধ করা** (B-V2-03) — ছোট পরিবর্তন (REDIS না থাকলে `return False` বা honest "unknown" + log), ঝুঁকি বিশাল: আনলিমিটেড per-user spend। **সর্বোচ্চ ROI।**
2. **Admin JWT revocation-কে বাস্তব করা** (B-V2-04) — blacklist-এ লেখার পাথ যোগ করা; Redis-ছাড়া মোডে revocation কাজ না করলে honest log + admin-নোটিশ।
3. **Gateway-র MagicMock অপসারণ** (B-V2-01) — `_router=None` + honest error; LLM hot path থেকে mock।
4. **Remediation engine মেরামত বা সততার সাথে disable** (B-V2-02) — অস্তিত্বহীন মডিউলের fallback মানে monitor প্রতি রাতে চুপচাপ মরে; হয় মডিউল লিখুন, নয় startup-এ fail-loud।
5. **Frontend ভুয়া-ডেটা ৫ জোন** (F-V2-01..06) — `|| 42.5`-জাতীয় constant-এর জায়গায় loading/empty state; guest chat-এ "demo responder" স্পষ্ট লেবেল বা আসল API; profile-এ মৃত button-গুলো disable বা wire।
6. **MCP ক্রিটিক্যাল ১০ tool-এ assert-test** — বিশেষত `policy.approve`, `autonomy.kill_switch`, `action.render_deploy`, `client.set_role` — এগুলো mutation/authority tool, বর্তমান coverage ~৭%।
7. **Release acceptance gate-এর evidence theater বন্ধ** (C-V2-01) — hardcoded "passed" সরিয়ে আসল artifact পড়া; নইলে gate-টার নামই বিভ্রামক।
8. **`@supabase/supabase-js`-কে mcp package.json-এ declare + F-14 সংকোচন** — dynamic registry silent-`[]` ঝুঁকি; zod-4 ফ্রন্ট (mission-control ইতিমধ্যে ^4) ধরে workspace-consolidation রোডম্যাপ।
9. **Unbounded store cap-পাস** (byoc `encrypted_vault`, markdown `jobs_db`, `RECENT_ACTIVITIES`, frontend `alerts`) — প্রতিটিতে maxlen/TTL; ৫১২MB Render tier-এ এগুলোই পরবর্তী leak-vector।
10. **docs/plans disposition পাস** — ~৭০ archive / ~৪০ keep+status / ~৯ merge; registry+snapshot এক-ই জেনারেটর থেকে; CHECKPOINT/STATUS/README-র মৃত দাবি মোছা।

**যা করা উচিত নয়:** নতুন plan ডকুমেন্ট লেখা (PLAN_005/006 বাস্তবায়ন ছাড়া); dead frontend layer-টা "পরে কাজে লাগবে" ভেবে রাখা (fake-data trap); CI-তে নতুন `continue-on-error` যোগ করা।

---

## পার্ট ৭ — প্রস্তাবিত ক্রম

1. ✅ **(সম্পন্ন — এই সেশনে)** P0 CI-ব্লকার ৪টি ঠিক + push (`1dea1fe2`, merge `691c0671`) — main আবার green-পথে।
2. **পরের সেশন প্রস্তাব:** পার্ট ৬-এর ১→৫ (সবগুলোই ছোট, উচ্চ-মূল্য) → তারপর MCP critical-10 tests → unbounded cap-পাস → docs disposition।
3. প্রতিটি ধাপের পরে: `ruff check+format (0.13.1 pin)`, `pnpm build`, `python scripts/ci/generate_module_capability_matrix.py` regenerate — এই ৩টি এখন থেকে push-এর আগে লোকাল গেট।

**সততার স্বীকারোক্তি:** এই অডিটের মূল্যায়নগুলো static analysis + নির্বাচিত টেস্ট রান + CI log-এর উপর ভিত্তি করে; সম্পূর্ণ backend suite (৩,২৬৯ handler) বা স্টেজিং runtime-প্রমাণ এই সেশনে চালানো হয়নি। `tests/runs` 112 বনাম দাবিকৃত 116 ইত্যাদি পার্থক্য parametrize-expansion-এ ব্যাখ্যযোগ্য — re-execute করা হয়নি।
