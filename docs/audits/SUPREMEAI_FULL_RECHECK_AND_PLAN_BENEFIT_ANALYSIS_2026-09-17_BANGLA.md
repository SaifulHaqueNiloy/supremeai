# SupremeAI — Main Branch সম্পূর্ণ পুনঃযাচাই (Root থেকে Fresh Clone) + docs/plans প্ল্যান বেনিফিট বিশ্লেষণ

**Document ID:** `FULL-RECHECK-PLAN-BENEFIT-2026-09-17`
**ভাষা:** বাংলা (Bangla)
**তারিখ:** 2026-09-17 (Asia/Dhaka)
**পদ্ধতি:** main branch root থেকে সম্পূর্ণ fresh clone (`git clone`, HEAD = `83084ee8`) → সম্পূর্ণ কোডবেস পুনঃস্ক্যান
**পরিসর:** backend/ (১,৮৩২ Python ফাইল), frontend/ (৪২৫ production TS/TSX ফাইল), infrastructure/mcp-control-plane/ (৮৮ MCP tools), packages/, CI (২৮ workflow), docs/plans/ (১৬৩ প্ল্যান ডকুমেন্ট)
**পূর্ববর্তী রিপোর্ট:** `docs/audits/SUPREMEAI_IMPROVEMENT_AND_FIX_REPORT_2026-09-17_BANGLA.md` — এই ডকুমেন্ট সেটির হালনাগাদ পুনঃযাচাই + নতুন প্ল্যান-বিশ্লেষণ

---

## 📑 সূচিপত্র

1. [এক্সিকিউটিভ সামারি](#-এক্সিকিউটিভ-সামারি)
2. [পার্ট ১ — যা আগে ঠিক হয়েছে (যাচাইকৃত)](#পার্ট-১---যা-আগে-ঠিক-হয়েছে-যাচাইকৃত)
3. [পার্ট ২ — Backend-এ এখনো খোলা সমস্যার সম্পূর্ণ তালিকা](#পার্ট-২---backend-এ-এখনো-খোলা-সমস্যার-সম্পূর্ণ-তালিকা)
4. [পার্ট ৩ — Frontend / Infra / CI-তে এখনো খোলা সমস্যার সম্পূর্ণ তালিকা](#পার্ট-৩---frontend--infra--ci-তে-এখনো-খোলা-সমস্যার-সম্পূর্ণ-তালিকা)
5. [পার্ট ৪ — docs/plans প্ল্যান রেজিস্ট্রির বাস্তব চিত্র](#পার্ট-৪---docsplans-প্ল্যান-রেজিস্ট্রির-বাস্তব-চিত্র)
6. [পার্ট ৫ — PLAN_001–004 গভীর বিশ্লেষণ](#পার্ট-৫---plan_001004-গভীর-বিশ্লেষণ)
7. [পার্ট ৬ — কোন প্ল্যান আমাদের সত্যিকারের লাভ দেবে (Top 10 র‍্যাংকিং)](#পার্ট-৬---কোন-প্ল্যান-আমাদের-সত্যিকারের-লাভ-দেবে-top-10-র‍্যাংকিং)
8. [পার্ট ৭ — যেসব প্ল্যান আর্কাইভ/বাতিল করা উচিত](#পার্ট-৭---যেসব-প্ল্যান-আর্কাইভবাতিল-করা-উচিত)
9. [পার্ট ৮ — প্ল্যানগুলোর মধ্যে দ্বন্দ্ব (Conflicts)](#পার্ট-৮---প্ল্যানগুলোর-মধ্যে-দ্বন্দ্ব-conflicts)
10. [পার্ট ৯ — চূড়ান্ত প্রস্তাবিত এক্সিকিউশন অর্ডার](#পার্ট-৯---চূড়ান্ত-প্রস্তাবিত-এক্সিকিউশন-অর্ডার)

---

## 🎯 এক্সিকিউটিভ সামারি

Root থেকে fresh clone করে সম্পূর্ণ main branch পুনঃযাচাই করা হয়েছে। **সুখবর:** আগের রাউন্ডের বেশিরভাগ ক্রিটিক্যাল ফিক্স (merge-conflict markers, react-router v7 আপগ্রেড, M2 Context Engine, runs observer wiring, orphan কম্পোনেন্টের ~৯০%) কোডে লাইভ যাচাই হয়েছে। **খারাপ খবর:** সবচেয়ে বিপজ্জনক ক্যাটাগরি — **"নীরব ভুয়া fallback"** — এখনো production path-এ জীবিত। সিস্টেম ব্যর্থ হলে ভুল বলে চিৎকার করে না; বরং **ভুয়া সফলতা মুখোশ পরে হাজির হয়** (ভুয়া ফাইল আপলোড, ভুয়া DB রেজাল্ট, ভুয়া ব্রাউজার স্টেপ, ভুয়া QA pass)। এটা আমাদের নিজেদের সব মেট্রিককেই অবিশ্বাস্য করে তোলে।

**docs/plans-এর বাস্তবতা:** ১৬৩টি প্ল্যান ডকুমেন্টের মধ্যে মাত্র ৪৪টিতে status আছে; ১১৯টি সম্পূর্ণ status-হীন (প্ল্যান-স্ফীতি)। সত্যিকারের মূল্য কেন্দ্রীভূত হয়েছে **PLAN_001–004 + Strategic Leverage memo-র ৭টি লিভারে** — কিন্তু চারটি numbered plan-এর **কোনোটাই এখনো কোডে নামেনি** (কোড-স্তরে grep-যাচাইকৃত)। সবচেয়ে বড় ঝুঁকি কোড নয় — **পরিকল্পনা-স্ফীতি**। এই ডকুমেন্টের পার্ট ৬-এ কোন প্ল্যান কী করে দেবে তার চূড়ান্ত Top 10 র‍্যাংকিং দেওয়া হলো, এবং পার্ট ৭-এ কোনগুলো আর্কাইভ করা উচিত।

**মূল সংখ্যা:**

| মেট্রিক | মান |
|---|---|
| Merge-conflict marker | **0** (সব পরিষ্কার ✅) |
| Backend-এ ভুয়া/mock fallback (production path) | **১০+ সাইট** (P1) |
| Backend-এ log ছাড়া except ব্লক | **৬৫৭** |
| Backend-এ সাইলেন্ট `except: pass` | **৩৪** (৩১ single-line + 3 multiline) |
| Unbounded in-memory store | **৫টি নিশ্চিত** (৫১২MB Render টায়ারে leak-vector) |
| Duplicate route registration (একই ফাইলে) | **৭ জায়গায়** |
| Frontend-এ ভুয়া UI/ডেটা | **২টি লাইভ রুটে** (P1) |
| Orphan/dead কম্পোনেন্ট | **~১১টি এখনো unwired** |
| Dual lockfile (bun.lock + pnpm-lock.yaml) | **হ্যাঁ — এখনো আছে** (P1) |
| MCP Control Tower | **৮৮ tools, ০ stub** (কোড পরিষ্কার, টেস্ট কভারেজ দুর্বল) |
| docs/plans ডকুমেন্ট | **১৬৩** (৩৩ active, ৭ proposed, **১১৯ status-হীন**) |
| PLAN_001–004 কোডে বাস্তবায়ন | **০/৪** (সব pending) |

---

## পার্ট ১ — যা আগে ঠিক হয়েছে (যাচাইকৃত)

Fresh main (HEAD `83084ee8`) থেকে কোড-স্তরে পুনঃযাচাইকৃত ফিক্সগুলো:

| # | আগের সমস্যা | এখনকার অবস্থা |
|---|---|---|
| 1 | `api-client` conflict markers | ✅ ঠিক — repo-wide conflict marker scan = **0 hit** |
| 2 | LeftRail truncation | ✅ merged (`9678bfeb`) |
| 3 | Skills install/uninstall/deploy | ✅ merged (`fix/skills-install-uninstall-deploy` branch) |
| 4 | Runs observer dispatch path (ERR-F01) | ✅ `observe_automation_run` লাইভ dispatch path-এ wired (`ee60fdb4`) |
| 5 | M2 Context Engine (ERR-F03) | ✅ `backend/context_engine/` লাইভ — budgeted smallest-sufficient-context assembly + test (`e48daaf0`) |
| 6 | react-router v7 + মৃত i18next deps (ERR-F04/ERR-P02) | ✅ আপগ্রেড ল্যান্ডেড (`dfb80110`) |
| 7 | Storybook v8/v10 intra-package conflict (ERR-P01) | ✅ ঠিক (`56058467`) |
| 8 | Stub scanner (ERR-M01) + CI stub gate (ERR-M02) | ✅ ব্রাঞ্চগুলো merge হয়েছে |
| 9 | Orphan কম্পোনেন্ট (~৪১টির ক্যাটালগ) | ✅ ~৯০% wired/deleted — CostDashboard, DeepResearchPanel, ScheduledTasksPanel, MemoryPanel, MCPConnector ইত্যাদির importer যাচাইকৃত |
| 10 | production_deploy.py ভুয়া deploy (`time.sleep(2)→return True`) | ✅ এখন fail-loud `NotImplementedError` (ERR-G02) |
| 11 | Crown-jewel ভুয়া স্টেপ এক্সিকিউটর | ✅ সরিয়ে honest 501 (ERR-G05) |
| 12 | Email agent ভুয়া OAuth `True` | ✅ এখন `NotImplementedError` + honest 501 |
| 13 | Hardcoded GitHub token (dock_integrations) | ✅ এখন Vault/DB থেকে encrypted token |
| 14 | Simulator in-memory state | ✅ Upstash Redis + TTL-এ মুভড |
| 15 | MCP Control Tower টুল | ✅ ৮৮টি tool রেজিস্টার্ড, **০টি stub** — adapters সব রিয়েল HTTP integration |
| 16 | CI actions pinning | ✅ ২৮টি workflow-এ ১০০% commit-SHA pinned |

---

## পার্ট ২ — Backend-এ এখনো খোলা সমস্যার সম্পূর্ণ তালিকা

### 🔴 P1 — নীরব ভুয়া fallback (সবচেয়ে বিপজ্জনক ক্যাটাগরি)

এগুলো ব্যর্থ হলে ভুল বলে না — **ভুয়া সফলতা রিটার্ন করে**। ডেটা নীরবে হারিয়ে যায় বা ভুয়া ডেটা ঢুকে যায়।

| # | ফাইল:লাইন | সমস্যা |
|---|---|---|
| B-01 | `backend/storage/r2_storage_client.py:23,41-63` (wired: `api/routes/media.py:12`) | R2 credential না থাকলে "dry-run/mock mode"-এ ঢুকে **ভুয়া presigned URL** (`https://mock-r2-upload.local/...`) রিটার্ন করে — মিডিয়া আপলোড "সফল" দেখায় কিন্তু কোথাও যায় না |
| B-02 | `backend/database/supabase_client.py:157-166` | Supabase init ব্যর্থ হলে `create_client("https://mock.supabase.co","mock-key")` fallback — DB অপারেশন নীরবে no-op হয়ে যায় |
| B-03 | `backend/database/supabase_client.py:82-122` | ৪৯+ public DB মেথডকে retry-wrapper মুড়ে রাখে; সব Exception ধরে `None`/`False` রিটার্ন করে — আসল DB error খালি রেজাল্ট সাজছে। এছাড়া "ফিক্সকৃত" retry sleep আসলে `future.result()` দিয়ে **event-loop ব্লক করায়** |
| B-04 | `backend/byoc/container_orchestrator.py:24-33,103-127` (wired: `api/routes/byoc_api.py`) | `async def deploy()`-এর ভেতরে blocking `subprocess.run(terraform apply)` (মিনিটব্যাপি event-loop ব্লক); terraform absent হলে **ভুয়া URL** (`https://byoc-skill-...-mock-url.a.run.app`) সহ `status:"deployed"` ফেরায়; rollback ব্যর্থ হলেও `"rolled_back"` বলে |
| B-05 | `backend/tools/browser/web_fallback_agent.py:116-144` | Playwright না থাকলে "simulated headless runner" থেকে **ভুয়া `steps_executed`** রেজাল্ট বানিয়ে দেয় — ব্রাউজার অটোমেশন সফলতা মিথ্যা |
| B-06 | `backend/core/testing/qa_suite.py:322-471,714-725` (registry: `core/__init__.py:295`) | QA suite DB কানেকশন **simulate** করে (সবসময় `True`), SQL-injection/XSS/auth-bypass চেক **simulate** করে, mock unit test বানায় — যেকোনো verification consumer ভুয়া pass/fail পায় |
| B-07 | `backend/core/orchestration/cloud_sandbox_orchestrator.py:67-141` | API key ছাড়া `run_command` রিটার্ন করে `status:"COMPLETED", exitCode:0, stdout:"Mock output..."` — mock flag আছে, কিন্তু flag উপেক্ষা করা caller সফল এক্সিকিউশন দেখে |

### 🟠 P2 — Mock leakage, unbounded memory, duplicate routes

| # | ফাইল:লাইন | সমস্যা |
|---|---|---|
| B-08 | `backend/core/llm/token_deductor.py:20,93-114` | Production **billing** মডিউলে `MagicMock` import + legacy branch-এ `session.add(MagicMock())` — টোকেন-ডিডাকশন পাথে test-shim |
| B-09 | `backend/core/embeddings.py:26,116-124` | Module-level `_embedding_cache` — **কোনো TTL/eviction নেই**; ৫১২MB free-tier-এ OOM leak-vector |
| B-10 | `backend/api/routes/chat_upload.py:40,200,421` | `_uploads` registry — শুধু explicit DELETE-এ remove; TTL নেই, প্রসেস-জীবনে unbounded |
| B-11 | `backend/api/routes/pr_review_api.py:27,87` + `ci_dashboard_api.py:183` | `_review_status`, `_ci_summaries_store` — কখনো prune হয় না |
| B-12 | `backend/api/routes/browser/_tasks.py:125-199` | একই ফাইলে **duplicate route** (DELETE /tasks/{id} ×২, POST complete ×২, POST fail ×২); legacy handler-গুলো dead কিন্তু mounted; :159-161-এ `return`-এর পরে **unreachable code**; legacy `TASKS` list unbounded |
| B-13 | `backend/core/competitive_kit.py:1340-1359` | `_call_llm` placeholder — `"[Response from {provider}/{model}]..."` ফেরায়; hardcoded model (o1-preview, gpt-4o-mini...); ভুয়া cost math (dormant, কিন্তু trap) |
| B-14 | `backend/core/deployment/production_deploy.py:366-469` | সব deploy/rollback backend এখন honest `NotImplementedError` (ভালো) — কিন্তু মানে **কার্যকর deploy পথ নেই**; `run_health_checks`-এ hardcoded `http://localhost:8000` (:429) |

### 🟡 P3 — Hardcode, blocking, hygiene

| # | ফাইল:লাইন | সমস্যা |
|---|---|---|
| B-15 | `backend/api/routes/chat.py:30`, `mobile_bff.py:12`, `onboarding.py:33`, `preferences.py:82,97`, `skills/core_knowledge_qa.py:169`, `skills/core_doc_summarizer.py:80`, `services/llm/providers.py:614` | রাউট স্কিমায় pinned model name (`gemini-2.5-pro`, `gpt-4o-mini`, `gpt-4o`, `llama-3.3-70b-versatile`) — নিজেদের zero-hardcode doctrine-এর লঙ্ঘন |
| B-16 | `backend/middleware/rate_limiter.py:17-24` | `InMemoryFallbackLimiter._hits` — চলমান key-ই prune হয়; অদৃশ্য client-দের key চিরকাল থাকে (Redis outage-এ slow growth) |
| B-17 | `backend/api/routes/session_stream.py:75-97` | সেশন-কী unbounded (বাফার ৫০ msg-এ ক্যাপড, কিন্তু key জমে) |
| B-18 | `backend/core/security/secret_vault.py:202-219` | Infisical retry-তে sync `time.sleep(2**attempt)` — async startup-এ ডাকলে event-loop স্টল |
| B-19 | `backend/tools/mcp/mcp_workspace.py:117-136` | Cross-process dir-lock `time.sleep(0.05)×50` (~২.৫সে) sync context-এ, async caller থেকে ডাকা হয় |
| B-20 | `backend/audit_check.py:60-78` | `POST /rules`, `POST /actions/{action_type}` — প্রতিটি দুইবার registered |
| B-21 | `backend/database/supabase_client.py:185-189` | Service-role client init ব্যর্থ হলে নীরবে `service_client = client` alias — config error লুকায় |
| B-22 | `backend/hardcoded_llm.json` | পুরোনো audit artifact, Windows path (`f:/supremeai/...`) সহ repo-তে committed — মুছে ফেলা উচিত |
| B-23 | `backend/tools/devops/docker_sandbox.py:126-141,240-250` | Docker absent হলে `"simulated": True` success envelope — flag সৎ, কিন্তু caller বিপদ |

### 📊 Backend স্ট্যাটিসটিক্স (grep-যাচাইকৃত)

| ক্যাটাগরি | সংখ্যা |
|---|---|
| Production `except Exception` ব্লক | ২,২০১ |
| এদের মধ্যে body-তে **কোনো log/raise নেই** | **৬৫৭** (top: `tools/self_planner.py`, `tools/agent_tools.py`, `tools/code/code_smell_detector.py`, `worker_service.py` ×5) |
| Single-line silent `except: pass/continue` | ৩১; multiline `except Exception: pass` → 3 (`memory/mcp_server.py:1218`, `core/orchestration/cloud_sandbox_orchestrator.py:391`, `services/integration_discovery.py:193`) |
| Duplicate route path string | 124 duplicate / 878 route decorator-এর মধ্যে; **৫টি true same-file conflict** |
| Merge-conflict marker | **0** |
| `time.sleep` in production | 10 সাইট (কোনোটা সরাসরি async def-এ নেই, কিন্তু ২টি event-loop-blocking পথ B-03/B-04) |

---

## পার্ট ৩ — Frontend / Infra / CI-তে এখনো খোলা সমস্যার সম্পূর্ণ তালিকা

### 🔴 P1

| # | ফাইল:লাইন | সমস্যা |
|---|---|---|
| F-01 | `frontend/src/components/dashboard/AgentExecutionTelemetryCockpit.tsx:75-116` (লাইভ রুট `/telemetry`) | "Mock file tree data" useEffect hardcoded ভুয়া repo-tree সেট করে; `handleExecuteCommand` `setTimeout` দিয়ে **ভুয়া টার্মিনাল এক্সিকিউশন** simulate করে ("Operation completed successfully.") — লাইভ রুটে ভুয়া টার্মিনাল |
| F-02 | `frontend/src/components/dashboard/AutomationQueuePage.tsx:45-58` | রিয়েল `/api/browser/tasks` ডেটার সাথে **fabricated `failure_payload`** মেশানো হয় (ভুয়া root-cause "DOM Element Timeout", ভুয়া stack trace, ভুয়া `reset_eta_sec: 240`) — ইউজার বানানো diagnostics দেখে |
| F-03 | রুট: `bun.lock` (303KB) **এবং** `pnpm-lock.yaml` (359KB) দুটোই committed, অথচ `package.json`-এ `packageManager: pnpm@10.15.0` | **Dual lockfile = গ্যারান্টেড dependency-tree drift**; কোনটা authoritative তা কিছুই pin করে না |
| F-04 | `pnpm-workspace.yaml` vs `apps/docs`, `apps/mission-control` | `apps/*` workspace member না, অথচ `turbo.json:119-123` `supremeai-docs#build` define করে (কখনো রান হতে পারে না); `apps/mission-control` (Next.js+Prisma) সম্পূর্ণ pnpm/turbo/CI-র **বাইরে** |

### 🟠 P2

| # | ফাইল:লাইন | সমস্যা |
|---|---|---|
| F-05 | `frontend/src/lib/cache.manager.ts:17,94-97` | Browser bundle-এ `@upstash/redis` + module-scope `new Redis({...})`; env var `UPSTASH_REDIS_REST_URL` `envPrefix`-এ নেই → সবসময় undefined; server-side Redis client browser-এ shipped |
| F-06 | `frontend/src/components/admin/InteractiveChatTab.tsx:232-233` | Admin "Interactive Chat" আসলে self-labeled "Secure Read-Only Mock Shell" |
| F-07 | `packages/core-infrastructure` (`frontend/package.json:33`, `tools/vscode-extension:429` ডিক্লেয়ার করে) | **০টি source import** — dead dependency; `@supremeai/shared-types`-ও frontend কখনো import করে না |
| F-08 | `packages/ui-components/src/utils/api.ts:16-35` vs `frontend/src/utils/api.ts:237` | **দুটি ভিন্ন `getApiBaseUrl()`** ভিন্ন semantics-এ — latent contract trap |
| F-09 | রুট `package.json` overrides (`vite 7.3.5`, `firebase ^12.15.0`) vs `frontend/package.json` (`vite ^7.3.6`, `firebase ^12.18.0`) | Root override নীরবে frontend-এর declared range downgrade করে |
| F-10 | রুট `package.json:30-31` (`desktop:dev/build`) | `supremeai-studio-client`-এ electron script/dep নেই — দুটো scriptই সাথে সাথে fail |
| F-11 | Orphan ফাইল (importer শূন্য — যাচাইকৃত): `OperatorStudio.tsx`, `LiveSujonBackground.tsx`, `SujonCoreCockpit.tsx`, `FixPreviewModal.tsx`, `SwarmHealthDashboard.tsx`, `HealthBanner.tsx`, `SkillForgeWidget.tsx`, `LoginScreen.tsx`, `RegisterScreen.tsx` + dead barrel `components/admin/index.ts`, `components/sujon/index.tsx` + transitively `TelemetryDashboardWidget.tsx` | **~১১-১২টি dead ফাইল** — ক্যাটালগ ৯৫% resolved বললেও এগুলো বাকি |
| F-12 | `frontend/src/store/adminStore.ts` (6), `hooks/useAdminApi.ts` (5), `hooks/useAuth.ts` (4) | Production-এ ৫৭টি `: any` + ৭টি `as any` কেন্দ্রীভূত |
| F-13 | MCP CI: `.github/workflows/ci-mcp-build.yml:63-65` | ১২টি MCP test script-এর **মাত্র ১টি** CI-তে চলে (`test:health-history`); `test:unit`, `test:smoke`, `test:access`, `test:client-registry`, `test:service-circles`, `test:timestamps` সব manual-only |
| F-14 | `infrastructure/mcp-control-plane/package.json` | Workspace-এর বাইরে (নিজস্ব npm lockfile) — **major-version drift unmanaged**: TS 7 vs 5, zod 4 vs 3, ioredis 6 vs 5 |

### 🟡 P3

| # | ফাইল:লাইন | সমস্যা |
|---|---|---|
| F-15 | `.github/workflows/maintenance.yml:733,754` | দুটি no-op echo step: "scripts/cost_guard_monitor.py does not exist — skipping" — যে script কখনো লেখাই হয়নি তার জন্য green-check |
| F-16 | `frontend/knip.json` | dead-code rule `warn`/`off` (`files: off`) — তাই knip gate F-11-এর dead code ধরতে পারে না; রুট `.knip.json` ভুল পথ point করে (`src/main.tsx` frontend-এর ভেতরে আছে রুটে না) |
| F-17 | `frontend/src/lib/supabase.client.ts:47-48` | Silent fallback `https://placeholder-supabase.internal` — কখনো connect করতে পারবে না এমন client |
| F-18 | `frontend/src/services/api/microserviceMonitor.ts:14-15`, `lib/secureSse.ts:34` | পুরোনো "mock implementation" কমেন্ট — কোড এখন রিয়েল API ডাকে, কমেন্ট মিথ্যা বলে |
| F-19 | `frontend/package.json:26-72` | Build tooling (typescript, vite, tailwindcss, cross-env...) `dependencies`-এ; unused: `jspdf`, `file-saver`, `@types/file-saver`, `dexie-react-hooks`; `workspace:*` vs `workspace:^` মিশ্রণ |
| F-20 | CI Infisical imports | `continue-on-error` ×14 (বেশিরভাগ justified) — কিন্তু Infisical secret import fail করলে নীরবে missing-env build হতে পারে (alert নেই) |
| F-21 | `06-e2e-customer.yml` | QA creds unprovisioned হলে scheduled run skip — customer E2E সম্ভবত সম্প্রতি একবারও চলেনি |

### ✅ Frontend-এ যা পরিষ্কার

- `console.log` production code-এ: **0** (একটি JSDoc উদাহরণে); prod build console drop করে (`vite.config.ts:116`)
- Hardcoded URL/localhost: **1** (`services/apiClient.ts:279` SSR fallback — গ্রহণযোগ্য)
- `alt=""` empty: **0**; icon-button-গুলো spot-check-এ aria-label আছে
- মোট ২৮ workflow-এ `if: false` disabled job: **0**

---

## পার্ট ৪ — docs/plans প্ল্যান রেজিস্ট্রির বাস্তব চিত্র

`docs/plans/plan_registry.json` (১৬৩ ডকুমেন্ট, generator: `scripts/governance/lint_plans.py`):

| Status | সংখ্যা | মানে |
|---|---|---|
| active | ৩৩ | approved/executable |
| proposed | ৭ | অনুমোদনের অপেক্ষায় (single-plan discipline-এ PLAN_001 active থাকায় ০০২-০০৪ অপেক্ষমাণ) |
| historical | ৩ | পুরোনো |
| blocked | ১ | `PLATFORM_OSS_INTEGRATION_PLAN` — বিষয়বস্তু roadmap M2/M4/M5/M8-এ শুষে গেছে |
| **status নেই** | **১১৯** | **প্ল্যান-স্ফীতির প্রধান প্রমাণ** — ফ্যামিলি: control-tower-mcp (32), execution-phases (30), unclassified (28), free-tier-federation (21), frontend-product-ux (15)... |

**গুরুত্বপূর্ণ পর্যবেক্ষণ:** সংখ্যাগরিষ্ঠ প্ল্যান কোডে রূপান্তরিত হয়নি, আর রূপান্তরিত হওয়া প্ল্যানগুলোর মধ্যে সবচেয়ে সফল (PR Guardian v1 — ৪৪/৪৪ টেস্ট) ছিল ছোট, সুনির্দিষ্ট, evidence-gated। এটাই আমাদের শেখা: **বড় blueprint নয়, ছোট falsifiable plan-ই কাজ করে।**

Traceability matrix (`PLAN_TO_CODE_TRACEABILITY_MATRIX.md`, ৯ canonical row):

| Canonical Area | অবস্থা | Gap |
|---|---|---|
| Architecture governance | active | unified static/runtime graph |
| QA governance | active | ৬টি fixme honestly blocked |
| Memory & context | active | M2 Context Engine (`e48daaf0`) ল্যান্ডেড — **matrix এখনো আপডেট হয়নি** |
| Execution (Run fabric) | active | dispatch instrumentation আংশিক (`ee60fdb4` এক bridge wired) |
| Browser / Control Tower / Production / Cost | active | staging evidence, boundary doc বাকি |
| Self-evolution | **proposed** | governed promotion path — কিছুই নেই |

---

## পার্ট ৫ — PLAN_001–004 গভীর বিশ্লেষণ

> চারটি numbered plan-ই **০টি নতুন dependency, ০টি নতুন infra, Render 512MB-সামঞ্জস্য**। কোড-স্তরে grep-যাচাই: চারটির কোনোটাই এখনো বাস্তবায়িত নয়।

### PLAN_001 — Anthropic Prompt Caching (`docs/plans/PLAN_001_ANTHROPIC_PROMPT_CACHING_2026-09-16.md`)
- **প্রস্তাব:** Claude-family provider-এ system prompt + MCP tool-catalog prefix-এ `cache_control: {"type":"ephemeral"}` marker — বিদ্যমান `CloudProviderAdapter`-এ ~৩০ লাইনের helper (LiteLLM নেটিভ passthrough)। usage-তে `cache_read_input_tokens` সারফেস + Langfuse-এ ফরওয়ার্ড; ১,০২৪-token minimum-prefix guard; ১টি mocked regression test।
- **Status:** `active` (একমাত্র active execution plan)। ⚠️ বাস্তবতা: `cache_control` backend-এ **zero hit** — মানে active = approved-executable, **done নয়**।
- **লাভ:** cached অংশে ~৯০% টোকেন-সাশ্রয় (vendor pricing), ৫০-৮০% latency কমে। **বাস্তব নোট:** zero-cost chain (Groq/free credits/Ollama) বলে ডলার-সাশ্রয় ≈ $0 — আসল লাভ **free-quota সংরক্ষণ** (প্রতি টার্নে কম টোকেন পোড়ে) + first-token latency।
- **জটিলতা/ঝুঁকি:** সব প্ল্যানের মধ্যে সবচেয়ে ছোট diff (<৮০ লাইন যোগ, ১ ফাইল + ১ setting + ১ test)। Worst case = আজকের আচরণ (regression শূন্য)।

### PLAN_002 — Claude-Style Context Compaction (`docs/plans/PLAN_002_CLAUDE_STYLE_CONTEXT_COMPACTION_2026-09-16.md`)
- **প্রস্তাব:** WS chat loop নীরবে ৫০ মেসেজের বেশি history ফেলে দেয় (`deque(maxlen=50)` — আজকেও লাইভ, `websocket_agent.py:474` যাচাইকৃত) → ~turn-25 অ্যামনেসিয়া (Constitution #13 লঙ্ঘন, লাইভ)। ফিক্স: full হলে পুরোনো অর্ধেক evict → বিদ্যমান zero-cost gateway chain দিয়ে summarize → labeled `compacted_context` ব্লক prepend; summarizer fail-এ আজকের dumb eviction-এ honest fallback।
- **Status:** `proposed` — ৩ বার re-verified (c812985 → 1f570558 → b37f3f10), touched ফাইলে 0-diff।
- **লাভ:** দীর্ঘ সেশন কার্যত unlimited memory, প্রতি ~২৫ exchange-এ ১টি extra LLM call (<1% free quota); per-turn খরচ অপরিবর্তিত (naive maxlen বাড়ালে ১০× হতো); demoable ("turn-1 তথ্য turn-60-এ স্মরণ")।
- **জটিলতা:** ছোট — ২ বিদ্যমান ফাইলে ~৮০ লাইন + ১ test। ঝুঁকি: compaction turn-এ ১-৩সে latency; খারাপ summary মেমোরি দূষণ (৩৫০-token cap দিয়ে mitigated); MEMLEAK-004 bounded-deque ফিক্স অক্ষত থাকে।

### PLAN_003 — Aider-Style Repo Map (`docs/plans/PLAN_003_AIDER_STYLE_REPO_MAP_2026-09-17.md`)
- **প্রস্তাব:** DynamicPlanningEngine-এর "Epistemic State Probe" (`backend/services/dynamic_planner.py:117-124`) দাবি করে "relevant files" দেখে কিন্তু **কোডবেস-দৃষ্টি শূন্য** (grep-যাচাই: `probe_system_state` executor নেই, `code_indexer.py` নেই)। ফিক্স: stdlib-`ast` symbol graph + pure-Python PageRank + ৪,০০০-চর budgeted render (`backend/core/code_indexer.py`, বিদ্যমান `markdown_indexer.py` singleton pattern অনুসরণ করে), শুধু CODER-domain intent-এ probe-এ inject।
- **Status:** `proposed`, evidence ২ বার শক্তিশালী (backend এখন ১,৮২৭ py-file; embedding fallback blake2b-এ deterministic)।
- **লাভ:** Dev-domain agent পায় whole-repo awareness ~১,০০০ টোকেনে — Aider/Cursor/Claude Code-এর table-stakes সমতা; `implementation_plan.md` §1-এর "discover_reusable_implementation"-এর প্রথম বাস্তব ভিত্তি; পরে PR Guardian/MCP tools-ও ব্যবহার করতে পারবে।
- **ঝুঁকি:** ৫১২MB Render container-এ প্রথম index (~১,৮০০ ফাইল) CPU-spike করতে পারে — mitigation: hard cap (২,০০০ ফাইল / ১০০KB) + ≤৫সে success threshold, নাহলে plan blocked (Gate 5)।

### PLAN_004 — Letta-Style Memory Distillation (`docs/plans/PLAN_004_LETTA_STYLE_MEMORY_DISTILLATION_2026-09-17.md`)
- **প্রস্তাব:** "Eternal Brain"-এর write path আক্ষরিক placeholder: `summary = content[:200] # Placeholder`, `structure = "{}"` (`backend/core/unified_memory.py:57-58` — **আজকেও লাইভ, যাচাইকৃত**), retrieval embedding সেই খারাপ summary থেকেই হিসাব হয় (`memory_service.py:306`)। ফিক্স: opt-in write-time distillation — dense ≤১৮০-token summary + JSON facts, **বিদ্যমান metadata JSON column-এ** (০ schema change); env kill-switch `SUPREMEAI_MEMORY_DIST=false`; honest fallback।
- **Status:** `proposed`, code evidence b37f3f10 পর্যন্ত re-verified।
- **লাভ:** Memory flywheel (Constitution #11) প্রথমবার সত্যিকারে compound শুরু করবে; SyncGuard-এর full JSON audit report ২০০ চরে কাটা পড়া বন্ধ। **অস্বাভাবিক সৎ threshold:** distilled entry-গুলোকে legacy truncation-কে top-3 hit-rate-এ **+১৫pp হরত হতে হবে, নাহলে plan declared failed** — falsifiable।
- **জটিলতা:** কম — ৩ ফাইল edit + ১ test; ০ dep/infra/schema। ঝুঁকি: খারাপ distillation-এ মেমোরি দূষণ (provenance flag `metadata["distilled"]`); PLAN_002-এর সাথে complementary ঘোষিত।

---

## পার্ট ৬ — কোন প্ল্যান আমাদের সত্যিকারের লাভ দেবে (Top 10 র‍্যাংকিং)

> র‍্যাংকিংয়ের ভিত্তি: ঘোষিত ROI vs প্রচেষ্টা, Render free-tier (৫১২MB, zero-cost provider) বাস্তবতার সাথে সামঞ্জস্য, এবং কোড-স্তরে যাচাইকৃত gap।

| র‍্যাংক | প্ল্যান | কেন সত্যিকারের লাভ (১-২ বাক্য) |
|---|---|---|
| **1** | **PLAN_002 Context Compaction** | সবচেয়ে user-visible quality win — মূল chat loop-এর turn-25 অ্যামনেসিয়া মেরে ফেলে, মাত্র ~৮০ লাইনে ২ ফাইলে; 512MB-safe; measurable; লাইভ Constitution #13 লঙ্ঘন বন্ধ করে |
| **2** | **PLAN_001 Prompt Caching** | সবচেয়ে ছোট diff, প্রতিটি Anthropic turn-এ সাথে সাথে latency + free-quota লাভ; একমাত্র caveat: zero-cost chain-এ "৯০% সাশ্রয়" ডলার নয়, quota-extension হিসেবে প্রকাশ পায় |
| **3** | **L1 Reliability Moat Gate** (leverage memo) | Mission suite 5→20 + nightly pass^3 ≥0.8 — বিদ্যমান harness-এ শুধু authoring-প্রচেষ্টা; প্রতিটি Phase-3 investment-এর stated prerequisite (B1/B2/B4 unlock) |
| **4** | **PLAN_004 Memory Distillation** | Eternal Brain write path-এর আক্ষরিক `# Placeholder` সরায়; +১৫pp falsifiable threshold; ~১০০ লাইন; মেমোরি (B4) প্রথমবার measurable করে |
| **5** | **L3 False-Assurance Purge** (Class G) | ভুয়া Stripe checkout, fake deploy, `score:100` scan — integrity দায়; এটা না করলে অন্য সব মেট্রিক অবিশ্বাস্য। (এই ডকুমেন্টের পার্ট ২-এর B-01…B-07 এরই আপডেটেড তালিকা) |
| **6** | **CI Pipeline Consolidation** (`CI_PIPELINE_CONSOLIDATION_PLAN_2026-09-15.md`) | প্রতি commit-এ ~৪× GitHub Actions runner-minute সাশ্রয় — যে free CI tier-এর উপর বাকি সব দাঁড়িয়ে তা রক্ষা করে; contained ও well-specified |
| **7** | **L2 Orphan Spine wiring** (ধাপে ধাপে) | ৫৭টি dead route family = সবচেয়ে বড় "বানানো কিন্তু অদৃশ্য" সম্পদ; missions-engine UI আগে (M1-এর Run fabric দৃশ্যমান করে); মোট effort বড় তাই staged। শুরু হয়েছে (`ee60fdb4`) |
| **8** | **M3/L4.1 Memory decision table** | ১৫+ প্রতিযোগী memory store = সবচেয়ে বড় architectural debt; প্রথম deliverable শুধু keep/merge/archive টেবিল — সস্তা, flywheel unblock করে, PLAN_004-কে doomed store-এ লেখা থেকে বাঁচায় |
| **9** | **PLAN_003 Repo Map** | Dev-task-এ সত্যিকারের capability unlock ০ খরচে, তবে লাভ CODER-domain-এ সীমাবদ্ধ + 512MB first-index ঝুঁকি — তাই 1-8-এর নিচে |
| **10** | **L7 Transparency Scoreboard** | বিদ্যমান artifact-এর উপর পাতলা React page (`reports/mission_passk.json`, cost analyzer, admin stats) — one-person project-এর জন্য সস্তা monitoring/marketing; কিন্তু L1/L5 সংখ্যা না বানালে মূল্যহীন |

**ইতিমধ্যে হয়ে গেছে (আবার plan করবেন না):** PR Guardian v1 (implemented, ৪৪/৪৪ — `PR_GUARDIAN_ANALYSIS_PLAN.md` §13), M2 Context Engine (`e48daaf0` — বাকি শুধু measurement harness + matrix row আপডেট)।

---

## পার্ট ৭ — যেসব প্ল্যান আর্কাইভ/বাতিল করা উচিত

### A. প্রতিযোগী master plan (একটা রাখুন, বাকি দুটো historical করুন)
- `UNIFIED_ECOSYSTEM_ARCHITECTURE_PLAN.md` vs `architecture/SUPREMEAI_MASTER_PLAN_CANONICAL.md` — দুটোই master-architecture দাবি করে (প্রথমটার নিজের frontmatter-ই flag করেছে); তার উপর `ROADMAP_ECOSYSTEM_ARCHITECTURE_BN.md` তৃতীয় Bangla master roadmap (`evidence_state: unverified`)। Reconciliation register নিজেই স্বীকার করে "several master blueprint documents overlap" — এটা নিজেদের নিয়ম ৯-এর লঙ্ঘন।

### B. Constitution-বিরোধী / ফ্যান্টাসি infrastructure (আর্কাইভ)
- `features/cloudflare_7node_global_edge_mesh_plan.md` — ৭টি combined account = standing prohibition #4 ("no free-tier quota tricks or account multiplication") সরাসরি লঙ্ঘন
- `features/kaggle_6node_cluster_compute_plan.md` — ৬ account / 180 GPU-h/week; leverage memo এক account-এ ~৩০h/week-ই চায় (L6.4)
- `infrastructure/render_4accounts_deployment_status_record.md` — ইতিমধ্যে `historical`

### C. Free-tier পরিবারের duplication (এক ops plan-এ consolidate)
- `features/free_tier_production_upgrade_plan_v2.md` vs `features/free_tier_512mb_memory_pressure_remediation_plan.md` — competing set
- `infrastructure/free_tier_federation_master_plan_v4.md` + `features/..._v4.1_missing_services_analysis.md` — banned versioned filename, unverified; `free_tier_scaling_constitution_and_compliance_policy.md`-ই declared canonical policy — এটাই absorb করুক

### D. Legacy / স্টেল / status-হীন (historical মার্ক করুন)
- `features/Plan_01…Plan_24` সিরিজ — pre-pivot lineage; ধারণাগুলো unified roadmap-এ বেঁচে আছে (Plan_02 key-rotation → provider router; Plan_03 learning → learning_events)
- `phases/file_disposition_and_retention_list.md` — **Java/Spring-Boot যুগের** artifact (`src/main/java` নিয়ে); বর্তমান Python/React repo-র সাথে অপ্রাসঙ্গিক, অথচ canonical governance plan এটাকে `depends_on`-এ রেখেছে (দ্বন্দ্ব #7)
- `phases/phase1_foundation…phase4_optimization`, `q1_2026_foundation_execution_plan.md`, `yearly_strategic_roadmap_2026.md` — historical planning lineage
- One-person project-এর জন্য ফ্যান্টাসি-স্টাফিং: `agent_roles_and_team_assignments.md`, `team_and_cloud_resource_allocation_plan.md`, `agent_and_engineer_skill_requirements.md`
- Audit-era one-shot: `comprehensive_172_files_reconciliation_master_plan.md`, `codebase_audit_and_remediation_roadmap_2026_08_25.md`, `evolution_patch_v3_implementation_plan.md`, `orphan_components_wiring_master_plan.md` (L2 superseded)
- Runtime evidence-হীন speculative self-evolution: `SUPREMEAI_REAL_INTELLIGENCE_EVOLUTION_PLAN.md`, `living_autonomous_intelligence_master_plan.md`, `crown_jewel_complete_system_integration_blueprint.md` (Crown Jewel নিজেই L3-এ mock-flagged), `self_assembling_need_supply_intelligence_plan.md` ইত্যাদি
- Status-হীন speculative integration: `n8n_workflow_automation_master_plan.md`, `messaging_bots_telegram_and_whatsapp_architecture.md`, `vscode_lm_multi_model_ide_support_plan.md`, `kilo_ai_*`, `superai_competitor_playbook.md`, `burj_khalifa_4pillar_evolution_roadmap.md`, `full_integration_master_blueprint_bn.md` ইত্যাদি

**সারমর্ম:** ১১৯টি status-হীন ডকের বাল্ক এখানেই। `CANONICAL_PLANNING_RECONCILIATION_AND_GUARDRAILS_PLAN`-এর Phase 3–6 (registry enforcement) শেষ না-করা পর্যন্ত এই স্ফীতি থাকবে।

---

## পার্ট ৮ — প্ল্যানগুলোর মধ্যে দ্বন্দ্ব (Conflicts)

| # | দ্বন্দ্ব | প্রভাব |
|---|---|---|
| 1 | PLAN_001 status "active" কিন্তু কোডে `cache_control` শূন্য | ভুল বোঝাবুঝির ঝুঁকি: active = approved-executable, **executed নয়**; single-plan discipline-এ এটি 002-004 block করে আছে |
| 2 | Candidate numbering drift: PLAN_001-এর "next plan" seeds ছিল Stagehand (#002), Letta (#003); বাস্তবে হয়েছে compaction (#002), repo-map (#003), distillation (#004) | ক্ষতিকর নয়, কিন্তু লিনিয়েজ নোট করা দরকার |
| 3 | **তিনটি প্রতিযোগী master doc** (UNIFIED_ECOSYSTEM vs MASTER_PLAN_CANONICAL vs ROADMAP_ECOSYSTEM_ARCHITECTURE_BN) | নিয়ম ৯ লঙ্ঘন — founder resolution দরকার |
| 4 | Run-vs-Context ordering দ্বন্দ্ব | UNIFIED_NEXT_ROADMAP-এ মীমাংসা হয়েছে, কিন্তু দুটি source plan-এ পুরোনো বিপরীত phase order রয়ে গেছে pointer metadata ছাড়া |
| 5 | Account-multiplication: Cloudflare 7-node + Kaggle 6-node প্ল্যান vs prohibition #4 | `.github/constitution/rules.yml`-এর সাথে সরাসরি সাংঘর্ষিক |
| 6 | Traceability matrix staleness | Matrix (verified 2026-09-15) বলে Context Engine contract gap — কিন্তু M2 (`e48daaf0`) ও M1 dispatch (`ee60fdb4`) পরে ল্যান্ড করেছে; matrix-এর নিজের "same PR" আপডেট নিয়মই ভাঙা |
| 7 | Governance plan Java-যুগের artifact-এর উপর নির্ভরশীল | `CANONICAL_PLANNING...`-এর `depends_on`-এ `phases/file_disposition_and_retention_list.md` — যা `src/main/java` নিয়ে |
| 8 | PLAN_004 vs M3/L4 sequencing | L4 চায় ১৫-store consolidation decision **আগে**; PLAN_004 বর্তমান landscape-এ লেখে (hedged: canonical `UnifiedMemoryInterface` path target)। 004 আগে চালালে M3 যে store archive করবে সেখানে distill হতে পারে |
| 9 | Registry vs inventory mismatch | `plan_inventory_2026-09-17.md` বলে 157 doc/126 missing-frontmatter; `plan_registry.json` বলে 163/1 — inventory lint snapshot, ক্যাটাগরাইজেশন আসলে `phases/plan_reconciliation_register.md`-এ |

---

## পার্ট ৯ — চূড়ান্ত প্রস্তাবিত এক্সিকিউশন অর্ডার

```
ধাপ ০ (এই সপ্তাহ — পরিষ্কারকরণ, সব Tier-1/Tier-2, কোনো approval লাগবে না):
  1. F-03: bun.lock মুছুন (pnpm-lock.yaml authoritative রাখুন)
  2. F-04: apps/* workspace-এ যোগ করুন অথবা exclusion doc করে dead turbo task মুছুন
  3. B-12/B-20: browser/_tasks.py + audit_check.py-এর shadowed duplicate handler মুছুন
  4. B-22: stale hardcoded_llm.json মুছুন
  5. F-15/F-16: maintenance.yml-এর দুটি no-op step মুছুন; frontend/knip.json-এ files rule on করুন
  6. F-17: supabase.client.ts-এর placeholder fallback সরিয়ে fail-fast করুন
  7. Matrix row আপডেট: M2 Context Engine (দ্বন্দ্ব #6 বন্ধ)

ধাপ ১ (পরের — PLAN_002 Context Compaction):
  2 ফাইলে ~৮০ লাইন + ১ test। সাফল্যের শর্ত: turn-60-এ turn-1 তথ্য recall; fallback <10%; RSS ±10%।

ধাপ ২ (PLAN_001 Prompt Caching — সবচেয়ে ছোট):
  ~৩০ লাইন helper + setting + test। Claude-family provider-এ cache_control।

ধাপ ৩ (L1 Reliability Moat):
  Mission suite 5→20 + nightly pass^k। পরের সব কিছুর prerequisite।

ধাপ ৪ (L3 False-Assurance Purge — এই ডকুমেন্টের P1 তালিকা দিয়ে):
  B-01…B-07 + F-01/F-02 — ভুয়া fallback → explicit 503/degraded বা সত্যি empty-state।
  সাথে F-05 (browser-এ Upstash client সরান)।

ধাপ ৫ (PLAN_004 Memory Distillation — M3/L4.1 decision table-এর সাথে সমন্বয়ে):
  আগে keep/merge/archive টেবিল, তারপর distillation — যেন doomed store-এ না লেখা হয়।

ধাপ ৬ (PLAN_003 Repo Map + CI Consolidation):
  512MB cap-guard সহ code_indexer; CI-তে matrix→monolith প্যাটার্ন।

ধাপ ৭ (L2 Orphan Spine, staged):
  missions-engine UI আগে, তারপর বাকি ৫৭ route family ধাপে ধাপে।

চলমান সংস্কৃতি-ফিক্স (ধাপে ধাপে):
  - ৬৫৭ log-হীন except ব্লক → structured logger (সবচেয়ে বেশি যাত্রী-পথ আগে)
  - ৫টি unbounded store → TTLCache
  - ৫৭টি `: any` → typed
  - বাকি ~১১ orphan ফাইল delete (knip gate on)
  - MCP-র বাকি ১১ test script ci-mcp-build.yml-এ wire
```

---

## পরিশিষ্ট — যাচাই পদ্ধতি ও প্রমাণ

- **Clone:** `git clone https://github.com/SaifulHaqueNiloy/supremeai.git` (fresh, root) — HEAD `83084ee8` ("Merge remote-tracking branch 'origin/main'"), working tree clean
- **Branch অবস্থা:** ১৬টি remote branch; সব feature/fix branch ইতিমধ্যে main-এ merge — কোনো pending merge নেই
- **স্ক্যান মেথড:** ripgrep pattern-স্ক্যান (stub/TODO/hardcode/silent-except/unbounded-store/conflict-marker), audit evidence cross-check (`docs/audits/evidence/2026-09-15/stubs_backend.txt` → বর্তমান HEAD-এ পুনঃযাচাই), import-graph tracing (orphan verification), plan-registry parsing + ১৫টি শীর্ষ প্ল্যান-ডক পূর্ণপাঠ
- **কোড-যাচাইকৃত গুরুত্বপূর্ণ দাবি:** `deque(maxlen=50)` @ `websocket_agent.py:474` (PLAN_002-এর ভিত্তি); `summary = content[:200] # Placeholder` @ `unified_memory.py:57-58` (PLAN_004-এর ভিত্তি); `cache_control` zero-hit (PLAN_001 অ-বাস্তবায়িত); `code_indexer.py` অনুপস্থিত (PLAN_003 অ-বাস্তবায়িত); ০ merge-conflict marker
- **সীমাবদ্ধতা:** Render/production runtime লগ এই পরিবেশ থেকে যাচাই নয়; backend test suite পূর্ণ রান করা হয়নি (স্ট্যাটিক + evidence-ভিত্তিক বিশ্লেষণ)

---

*এই ডকুমেন্টটি `SUPREMEAI_IMPROVEMENT_AND_FIX_REPORT_2026-09-17_BANGLA.md`-এর পরবর্তী সংস্করণ। পরবর্তী agent `CHECKPOINT.md` পড়ে ধাপ ০ (পরিষ্কারকরণ) থেকে শুরু করবে।*
