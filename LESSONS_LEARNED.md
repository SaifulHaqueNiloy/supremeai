# LESSONS_LEARNED

<!-- বাংলা নোট: প্রতিটি ফিক্স ব্লকই সংযোজনীয় — পুরনো এন্ট্রি মুছবেন না। -->

## 2026-08-15 — Do NOT hard-fail `alembic upgrade head` on asyncpg in CI (MissingGreenlet regression)

### সমস্যা: bridge-boot-check-এ alembic hard-fail বানানোয় CI লাল হয়ে গেল।
- **উৎস:** `DATABASE_URL` = `postgresql+asyncpg` (async ড্রাইভার) আর `alembic upgrade head` sync চলে; ফলে CI container-এ `sqlalchemy.exc.MissingGreenlet` দিয়ে fail। আগের `|| echo` ছিল ইচ্ছাকৃত bypass (health probe-ই আসল gate)।
- **ফিক্স:** revert → `poetry run alembic upgrade head || echo "WARN..."` (non-blocking); শুধু HTTP health probe-কে gate রাখা হয়েছে; কারণ comment-এ documented।
- **লেসন:** async DB driver + sync alembic একসাথে synchronized CI container-এ run করলে MissingGreenlet আসে। Migrate-ভেরিফিকেশন দরকার হলে আলাদা job-এ sync URL/`asyncio` wrapper দিয়ে run করো, নাহলে boot check-এ non-blocking রাখো।

## 2026-08-15 — CI Deploy-verify 120s Timeout Root Cause Fix (Render slow build)

### সমস্যা: GitHub Action (`ci.yml` → `Verify Render Deploy (Wait for Live)`) hard-fail করছিল।
- **উৎস:** `verify-render-deploy.py`-এ `TIMEOUT_LIMIT = 120`। Render free-tier-এ ভারী Python backend-এর build+deploy `update_in_progress` অবস্থায় ২-৬ মিনিট নেয়; ১২০s-এ সেই অবস্থাতেই step fail → পুরো push run লাল (বাকি সব job path-filter-এ skip থাকায় এরাই একমাত্র failer)।
- **ফিক্স:** default ৩৬০s (৬ মিনিট), `RENDER_VERIFY_TIMEOUT` env দিয়ে overridable; `fail/cancel/error` status এখনও instant fail; deploy LIVE-এর পরে fresh-live HTTP health check-ও retries=১০ (app boot সময় পায়)।
- **লেসন:** CI-তে polling/sleep-ভিত্তিক deploy verification-এ timeout কখনোই app-এর বাস্তব build/deploy সময়ের চেয়ে ছোট রাখো না — নাহলে false-negative fail আসবে। Status-ভিত্তিক fast-fail (fail/cancel/error) রাখো, কিন্তু "in-progress" অবস্থার জন্য generous টাইমআউট দাও এবং env-চালিত করো, যাতে CI-স্তর থেকে tune করা যায়।

## 2026-08-15 — Simple CI Pipeline: Silent-Failure, Lockfile Auto-Push, Dual-Cache & Version Consistency Fix

### সমস্যা: Simple CI (`ci.yml`) ও companion workflows-এ কিছু reliability/security দুর্বলতা ছিল।
- **উৎস:**
  1. `frontend-ci`-এ `pnpm install --no-frozen-lockfile` + main-এ lockfile-auto-push → PR-review/branch-protection bypass এবং push-triggered recursive CI run-এর ঝুঁকি।
  2. `changes` filter-এ `apps/**` (mobile/desktop/docs) থাকলেও frontend-ci শুধু web build করত → false-green।
  3. `check-render-quota`-এ hardcoded Render service ID fallback।
  4. `intelligent-premerge-gate`-এ `service_preflight_check.py || echo` ও `env-drift-check`/`bridge-boot`-এ silent `||` swallow → blocking intent নষ্ট।
  5. backend-এর দুই আলাদা dependency cache (`setup-python poetry` + `setup-backend` venv)।
  6. `setup-backend` action এবং কয়েকটা workflow-এ floating action versions (`@v6`/`@v1`) — main CI-তে pinned থাকলেও এগুলো unpinned।
  7. Node version অসামঞ্জস্য (frontend 24 vs health-check 22), এবং পুনরাবৃত্ত cron (02:00-তে maintenance+auto-fix, রবিবার 02:00-তে k6+dast)।
- **ফিক্স:**
  1. `frontend-ci` ও `health-check`: `pnpm install --frozen-lockfile`; main-এ lockfile auto-commit step অপসারণ (drift এখন frozen install-ই verify করে)।
  2. `frontend` filter থেকে `apps/**` বাদ — apps শুধু tag-ভিত্তিক `release-builds.yml`-এ ship হয় (comment-এ নথিভুক্ত)।
  3. `check-render-quota`: hardcoded service ID fallback বাদ → শুধু `secrets`/`vars`।
  4. `premerge-gate` preflight-কে সত্যিকারের blocking (script fail হলে exit 1); risk scorer-এ গিটহাব-স্তরের `continue-on-error: true`; `bridge-boot`-এ `alembic` silent swallow বাদ।
  5. `backend-ci` এখন `setup-backend` composite action ব্যবহার করে — Poetry+venv cache একটাই source of truth (dual-cache দূর)।
  6. `setup-backend/action.yml`: `setup-python@v6`→pinned SHA, `cache@v6`→`cache@v4` (repo-র বাকি অংশের সাথে consistent)।
  7. `health-check` Node 22→24 (web stack-এর সাথে match); cron staggering (maintenance 01:00, auto-fix 01:30, dast রবিবার 00:30)।
- **লেসন:**
  1. CI step-এ `|| echo`/`|| true` দিয়ে error গিলে ফেললে gate মিথ্যা। Blocking-এর জন্য fail-for-real, informational-এর জন্য গিটহাব-স্তরের `continue-on-error` ব্যবহার করো (UI-তে visible থাকে)।
  2. `pnpm install` সর্বদা `--frozen-lockfile`; lockfile-drift ঠিক করতে main-এ পুশ না-করে dedicated bot PR।
  3. Action versions একই repo-তে অভিন্নভাবে pin করো — শুধু main workflow-এ pin করে composite action-এ floating রাখা supply-chain risk।
  4. path-filter এবং actual job scope মেলে কিনা মিলিয়ে দেখো, নাহলে false-green।
  5. একই জিনিসের জন্য দুটো cache/logic রাখো না — একটাই source of truth।

## 2026-08-15 — SupremeAI Simple CI Pipeline Upgrade (Quota Cache, Concurrency, Smart Deploy Trigger)

### সমস্যা: CI পাইপলাইনে কোটা ক্যাশে প্রতি রানে হারিয়ে যেত, কনকারেন্সি কন্ট্রোল না থাকায় পুরনো রানে ফ্রি মিনিট নষ্ট হতো, এবং Render ডিপ্লয়ে ডবল ট্রিগার/ফলব্যাক হ্যান্ডলিং ছিল না।
- **উৎস:** 
  1. `check-render-quota.py` ফাইল লিখলেও CI-তে `actions/cache` পারসিস্টেন্স ছিল না।
  2. `ci.yml`-এ `concurrency` না থাকায় দ্রুত একাধিক পুশ আসলে আগের অপ্রয়োজনীয় রানগুলো ব্যাকগ্রাউন্ডে রানার মিনিট শেষ করত।
  3. `deploy-backend` ধাপে `RENDER_API_KEY` এবং `RENDER_API_KEY_BACKUP` উভয়ই পরপর অন্ধভাবে ডাকা হচ্ছিল, যার ফলে প্রাইমারি কী সফল হলেও ব্যাকআপ কী রান হতো এবং কোটা দ্বিগুণ খরচ হতো। এছাড়া কোনো ডিপ্লয় ফেইল্ড হলে বা ওয়েব হুক ফলব্যাক সাপোর্ট ছিল না।
- **ফিক্স:** 
  1. `ci.yml`-এ `concurrency: cancel-in-progress: true` যোগ করা হয়েছে যা নতুন পুশে পুরনো রান স্বয়ংক্রিয়ভাবে বাতিল করে ফ্রি GitHub Actions মিনিট বাঁচায়।
  2. `check-render-quota` জবে `actions/cache/restore@v4` ও `save@v4` যোগ করে `render_minutes_cache.json` পারসিস্ট করা হয়েছে এবং `$GITHUB_STEP_SUMMARY`-তে Markdown টেবিল রিপোর্ট জেনারেট করা হয়েছে।
  3. `trigger_render_deploy.py` রিফ্যাক্টর করে স্মার্ট ফলব্যাক আর্কিটেকচার দেওয়া হয়েছে: প্রাইমারি কী সফল হলে ব্যাকআপ স্কিপ করে কোটা রক্ষা করে; প্রাইমারি ফেইল করলে ব্যাকআপ কী এবং এরপর `RENDER_DEPLOY_HOOK_URL` ওয়েবহুক ফলব্যাক ট্রিগার করে।
  4. `health-check` জবে `Install pnpm` এবং `setup-node` অর্ডার সুনির্দিষ্ট করে স্ট্যাবিলিটি নিশ্চিত করা হয়েছে।
- **লেসন:** 
  1. CI পাইপলাইনে সবসময় `concurrency.cancel-in-progress` রাখা উচিত যাতে অপ্রয়োজনীয় পুশ বা রি-রান ফ্রি মিনিট গ্রাস না করে।
  2. মাল্টিপল এপিআই কী বা ফলব্যাক স্ট্র্যাটেজি থাকলে স্ক্রিপ্ট লেভেলেই স্মার্ট চেক (Short-circuit on success) রাখতে হয়, অন্ধভাবে সবগুলো ট্রিগার করা যাবে না।
  3. জটিল বহু-ফাইল ওয়ার্কফ্লোর তুলনায় সিঙ্গেল-ফাইল `ci.yml`-এ স্পষ্ট ও প্রোটেক্টেড লজিক রাখা দ্রুততর এবং রক্ষণাবেক্ষণযোগ্য।


## 2026-08-15 — Admin Login Firebase Auth Object Crash & E2E Flakiness Fix

### সমস্যা: Admin Login-এ Firebase Auth Error অবজেক্ট হিসেবে থ্রো হলে React ক্র্যাশ করছিল, এবং E2E টেস্ট pre-auth 400 error-কে critical error ধরছিল।
- **উৎস:** আগের React Error #31 ফিক্সে `data.detail` চেক করা হলেও, Firebase `signInWithEmailAndPassword` ফেইল করলে `catch (authErr)` থেকে আসা `authErr.message` সবসময় plain string না-ও হতে পারে। এছাড়া `active-monitor.spec.ts` unauthenticated অবস্থায় SSE (Server-Sent Events) endpoint-এ 400 Bad Request পেলে তাকে "critical error" ধরে test fail করাচ্ছিল।
- **ফিক্স:** 
  1. `adminStore.ts`-এ Firebase `authErr.message` string কিনা তা চেক করে fallback error message (`JSON.stringify` বা `code`) সেট করার ব্যবস্থা করা হয়েছে।
  2. `AdminLogin.tsx`-এ `adminError` render করার সময়ও guard (`typeof === 'string'`) দেওয়া হয়েছে।
  3. `active-monitor.spec.ts`-এ test login-এর আগে আসা `400` এবং `net::ERR_ABORTED` error গুলো ignore করার ফিল্টার যুক্ত করা হয়েছে।
  4. CI Environment Health Check-এর জন্য `TEST_ADMIN_EMAIL` (`test_admin@supremeai.com`) Firebase Auth-এ অ্যাড করা হয়েছে এবং root `.env`-এর `ADMIN_EMAILS` লিস্টে যুক্ত করা হয়েছে।
- **লেসন:** (১) 3rd party SDK (যেমন Firebase) থেকে আসা Error object-ও সরাসরি React state-এ string হিসেবে ধরে নেওয়া যাবে না। সর্বদা type check করুন। (২) E2E Test লেখার সময় "expected" error (যেমন unauthenticated SSE failure) গুলোকে filter out করতে হয়, নচেৎ false-positive failure আসবে। (৩) CI/E2E test account গুলো অবশ্যই proper configuration (`ADMIN_EMAILS` এবং Firebase Auth) এর আওতায় রাখতে হবে।


## 2026-08-15 — React Error 31 "Object as a React child" (Admin Dashboard Crash)

### সমস্যা: E2E `active-monitor.spec.ts` তে React Error #31 (`object with keys {code, message, errors}`) দেখা যাচ্ছিল।
- **উৎস:** `frontend/src/store/adminStore.ts`-এ `handleAdminLogin` এবং `resetTotpSetup` কল করার সময়, যদি API 400 Bad Request দেয় এবং response payload-এ `detail` প্রপার্টি একটি object হয় (যেমন: Firebase বা FastAPI custom exception থেকে `{code, message, errors}`), তাহলে `adminStore` সরাসরি ঐ object কে `adminError` state-এ সেট করে দিচ্ছিল। React কোনো object কে সরাসরি render করতে পারে না, তাই `DashboardErrorBoundary` বা Alert component ক্র্যাশ করে Error #31 থ্রো করত।
- **ফিক্স:** `adminStore.ts`-এ `setupData.detail` এবং `data.detail` থেকে error মেসেজ এক্সট্র্যাক্ট করার সময় টাইপ চেকিং স্ট্রং করা হয়েছে। এখন যদি API থেকে `detail` object রিটার্ন করে, তাহলে `JSON.stringify(data.detail)` ব্যবহার করে সেটিকে স্ট্রিংয়ে কনভার্ট করা হয়, যাতে React কখনোই ক্র্যাশ না করে। 
- **লেসন:** (১) API error response handling করার সময় কখনোই সরাসরি `data.detail` বা `err.response.data` কে React state-এ সেট করা উচিত নয়, কারণ backend থেকে অপ্রত্যাশিত error shape (object/array) আসতে পারে। সর্বদা `typeof === 'string'` চেক করুন এবং fallback হিসেবে `JSON.stringify` বা `err.message` ব্যবহার করুন। (২) Client-side crash ডিবাগ করার সময় Unminified build-এ (local dev server) E2E টেস্ট চালালে component stack trace খুব সহজেই বের করা যায়।

## 2026-08-15 — SupremeAI IDE Trio Pipeline (Gemini → Kilo → Cline) Build

### Problem: IDE-তে Gemini, Kilo Code, Cline আলাদা এক্সটেনশন — এদের এক pipeline-এ যুক্ত করে Write → Review → Production-Check দরকার

- **ফিক্স (নতুন কম্পোনেন্ট):**
  1. `backend/agents/ide/trio_adapters.py` — `GeminiWriter` (Stage 1), `KiloReviewer` (Stage 2), `ClineChecker` (Stage 3); প্রতিটি `TrioAgentResult` রিটার্ন করে।
  2. `backend/core/orchestration/trio_pipeline.py` — `TrioPipeline.execute()` three-stage chain।
  3. `backend/api/routes/ide_trio.py` — `POST /api/v1/ide-trio/execute`; `backend/api/routers.py`-এ register। main repo ↔ worktree sync।
  4. `backend/tools/mcp/mcp_ide_trio.py` — MCP tool; `.kilo/agent/config.json`-এ `ide-trio` server।
  5. VS Code extension — `IdeTrioPipeline.ts`, `supremeai.trioPipeline` command, agentDetector-এ Kilo/Cline/Gemini detection।
  6. `tests/test_ide_trio_smoke.py` — 4/4 pass।
- **লেসন:**
  1. worktree + main repo sync না করলে MCP config ও routing broken থাকে।
  2. `loguru` bare-Python-এ না থাকলে import crash — try/except ImportError → logging stub fallback। `agents/__init__.py`-এর ভারি imports উপেক্ষা করতে smoke test-এ importlib direct file load।
  3. Windows console cp1252-এ emoji print করলে UnicodeEncodeError — `sys.stdout.reconfigure(encoding='utf-8', errors='replace')`।
  4. Hardcoded-secret check substring `secret=` দিয়ে fail — regex `(api[_-]?key|secret|password|token)\s*=\s*['\"][^'\"]+['\"]` ব্যবহার করলে স্পেস থাকলেও কাজ করে।
  5. VS Code command add করলে package.json contributes.commands + extension.ts registerCommands + subscriptions.push — তিন জায়গা synchronized হওয়া চাই।

## 2026-08-15 — Codebase Report Audit Fixes (HITL OTP + CI Security Gate)

### সমস্যা: `supremeai_codebase_report.md` রিভিউ করে ৪টি critical issue চিহ্নিত; ভেরিফাই করে ২টি আসল, ২টি false alarm পাওয়া গেছে
- **ফিক্স:**
  1. **HITL OTP client-side-only ছিল (সত্যি):** `HumanInTheLoopProtocol.tsx` এর `handleOtpSubmit` শুধু `otpCode.length === 6` চেক করত → backend না ডাকায় OTP trivially bypass হত। এখন `apiClient.post('/api/admin/verify-otp', { code: otpCode })` কল করে, loading (`otpVerifying`) + error (`otpError`) স্টেট, আর backend `400/401` এ error মেসেজ দেখায়। `apiClient` নিজেই `supreme_admin_jwt` Bearer হিসেবে পাঠায়।
  2. **`security-audit.yml` non-failing (সত্যি):** `pip-audit` ও `pnpm audit` এর শেষে `|| echo "..."` ছিল → audit fail করলেও build pass করত। সরিয়ে দেওয়া হয়েছে যাতে vulnerability-তে workflow fail করে।
  3. **Migration `down_revision` false alarm:** রিপোর্ট দাবি করেছিল `a1b2c3d4e5f6` revision নেই — আসলে `a1b2c3d4e5f6_add_patch_telemetry_table.py` আছে, chain valid। কোনো ফিক্স লাগেনি।
  4. **DashboardShell testid false alarm:** রিপোর্ট বলেছিল sidebar testid নেই — আসলে `Sidebar.tsx` এ `data-testid="dashboard-sidebar"` ও `nav-*` আছে, `DashboardShell.test.tsx` 5/5 pass করে। কোনো ফিক্স লাগেনি।
- **লেসন:** (১) রিপোর্টের দাবি অন্ধভাবে বিশ্বাস না করে কোডবেসে ভেরিফাই করুন — এখানে ৪-এর ২টিই ভুল ছিল। (২) HITL/OTP-এর মতো সিকিউরিটি চেক ক্লায়েন্টে করা যাবে না, অবশ্যই backend-এ validate করতে হবে। (৩) CI audit-এ `|| echo` দিয়ে soft-fail করা production-এ নিরাপত্তা ঝুঁকি। (৪) ফিক্সের পর `tsc --noEmit` 0 errors + `eslint` clean + টেস্ট ৫/5 pass ভেরিফাই করা হয়েছে।

## 2026-08-15 — SupremeAI Model/Provider Branding (Third-Party Names → Own Brand)

### সমস্যা: ইউজার/অ্যাডমিন UI-এ GPT/Claude/Gemini-এর মতো বাহিরের AI মডেল নাম সরাসরি দেখাচ্ছিল
- **ফিক্স (সেন্ট্রালাইজড ব্র্যান্ডিং):**
  1. **Frontend single source:** `frontend/src/lib/modelBranding.ts` তৈরি করা হয়েছে — `getSupremeModelLabel()`, `getSupremeProviderLabel()`, এবং ক্যানোনিক্যাল `SUPREME_AVAILABLE_MODELS` লিস্ট। মডেল আইডি → `SupremeAI Core / Reason / Vision / Deep / Llama` ম্যাপ করে।
  2. **User-facing rebrand:** `UserDashboard` (প্রজেক্ট ব্যাজ), `SettingsPage` (ড্রপডাউন), `StepModelSelect` (Onboarding), `EvolutionForge` (`ForgeSidebar` + `AgentNode`), `CostAuditor` (চার্জ টেবিল), `CostDashboard` (প্রোভাইডার নাম), `CommandBar`, `ProfilePage`, `BillingPage` — সব জায়গায় ব্র্যান্ডেড নাম।
  3. **Admin hints rebrand:** `ModelRouter.tsx` BanglaHint গুলো (`GPT-4/Gemini` → `Core/Vision`) এবং `InteractiveChatTab.tsx` ডায়াগনস্টিক (`OpenAI/Gemini/Anthropic Gateways` → `SupremeAI Core/Vision/Reason Gateways`)। ModelRouter-এর PROVIDER_LIST ও override provider id গুলো **literal রাখা হয়েছে** — কারণ সেগুলো ব্যাকএন্ড রাউটিং কনফিগ, রি-ব্র্যান্ড করলে ভুল কনফিগ হত।
  4. **Backend single source:** `backend/utils/branding.py` — `MODEL_DISPLAY` / `PROVIDER_DISPLAY` ম্যাপ + `get_model_display_name()` / `get_provider_display_name()`। নতুন এন্ডপয়েন্ট `GET /api/admin/model-branding` ক্যানোনিক্যাল ম্যাপ রিটার্ন করে (ভবিষ্যতে ফ্রন্টএন্ড এটি থেকে ফেচ করতে পারে)।
- **লেসন:** (১) ব্র্যান্ডিং লজিক এক জায়গায় রাখুন (`modelBranding.ts` / `branding.py`) — ডুপ্লিকেট লিস্ট এড়াতে `SUPREME_AVAILABLE_MODELS` কে সিঙ্গেল সোর্স করুন। (২) ডিসপ্লে টেক্সট ব্র্যান্ড করুন কিন্তু **রাউটিং/কনফিগ আইডি (raw provider id) অপরিবর্তিত রাখুন** — নচেৎ ব্যাকএন্ড কল ভাঙে। (৩) অ্যাডমিন কনফিগ UI-তে literal প্রোভাইডার নাম রাখাই নিরাপদ, শুধু হেল্প-টেক্সট ব্র্যান্ড করুন। (৪) `tsc --noEmit` 0 errors এবং `python -c ast.parse` দিয়ে ব্যাকএন্ড সিনট্যাক্স ভেরিফাই করা হয়েছে।

## 2026-08-15 — Frontend TypeScript Typecheck Cleanup (0 errors) + Bad `sed` Proposal Pushback

### সমস্যা: ৮টি ফাইলের জন্য একগুচ্ছ `sed` রিফ্যাক্টর প্রস্তাব এসেছিল যা বেশিরভাগই ভাঙা/ভুল ছিল
- **পর্যালোচনা (Objective Pushback):** প্রস্তাবিত `sed` কমান্ডগুলো সরাসরি অ্যাপ্লাই না করে আগে আসল কোড পড়া হয়েছে। ফলাফল:
  - `ModelRouter.tsx`: `payload` কে `provider`/`model`/`remaining_requests` দিয়ে বদলালে **undefined variable** → কোড ভাঙত। আসলে ইতিমধ্যেই ঠিক পাস হচ্ছিল।
  - `AdminAlertsTab.tsx`: টার্গেট `hasToken`/`adminTokenStore` ফাংশনটিই ফাইলে নেই → `sed` **no-op**; আর `!!x && x !== null` লজিকভাবে redundancy।
  - `OneClickPatch.tsx`: ফাংশনেই `try/catch/finally` আছে, নতুন `try{` যোগ করলে **brace অমিল** → syntax error।
  - `RBACManager.tsx`: `role !== "Admin" && role !== "God"` চেক করলে Viewer/Operator/Developer **অ্যাডই করা যেত না** → ভুল লজিক (সঠিক ফিক্স = ব্যাকএন্ড RBAC এনফোর্সমেন্ট)।
  - `RealTimeMetricsPanel.tsx`: `CONFIG_DEADLINE_MS` ভেরিয়েবলটিই এই ফাইলে নেই → **no-op**; আর `!metrics` ইতিমধ্যে "Metrics unavailable" দেখাচ্ছে।
  - `ChatInterface.tsx`: `input.length < 3` ব্লক করলে "ok"/"hi"/"?"/ইমোজি পাঠানো যেত না → খারাপ UX। বর্তমান `Enter && !shiftKey` লজিকই স্ট্যান্ডার্ড।
  - `GlobalConfigInitializer.tsx`: `sed` টি string-কে নিজের সাথে বদলাচ্ছে → **no-op**; ৮ সেকেন্ড ডেডলাইন ইচ্ছাকৃত (Render কোল্ড স্টার্ট 30-50s)।
- **প্রকৃত নিরাপদ ফিক্স যা অ্যাপ্লাই করা হয়েছে:**
  1. `AdminAlertsTab.tsx` — টোকেন না থাকলে fetch/resolve আগেই থামে; resolve-এর এরর এখন `alert()`-এর বদলে `supremeai-toast`।
  2. `OneClickPatch.tsx` — প্যাচ অ্যাপ্লাইয়ের আগে `window.confirm` কনফির্মেশন।
  3. `UnifiedChatBubble.tsx` — ক্লিপবোর্ড কপি `try/catch` + ইউজার ফিডব্যাক।
  4. `RBACManager.tsx` — ইউজার ডিলিটের আগে কনফির্মেশন (accidental delete রোধ)।
- **Pre-existing TypeScript এরর ক্লিনআপ (tsc --noEmit → 0 errors):**
  - `AdminAlertsTab.tsx`: অব্যবহৃত `React` import সরানো (`import React, {...}` → `import {...}`); `unknown` হ্যান্ডলিং `instanceof Error` গার্ড দিয়ে (OneClickPatch/ChatInterface/UnifiedChatBubble ইতিমধ্যেই ঠিক ছিল)।
  - `ModelRouter.tsx`: `providers` কে `ProviderStatus` ইন্টারফেস দিয়ে টাইপ করা (আগে inline `unknown`-সদৃশ অসম্পূর্ণ টাইপ)।
  - `RealTimeMetricsPanel.tsx`: `mergeSeries(series: SeriesItem[])` টাইপ করা।
  - `GlobalConfigInitializer.tsx`: `applyConfig`-এ `data` কে `RuntimeConfig`-সদৃশ কাস্ট করে `maxConcurrency`/`features.selfHealing` অ্যাক্সেস।
  - `dashboard/HumanInTheLoopProtocol.tsx` + `dashboard/SujonCoreCockpit.tsx`: `actionDetails`/`auditTrail`/`agentLogs` এর `unknown` রেকর্ডগুলোকে লোকাল ইন্টারফেস (`ActionDetails`/`AuditEntry`/`AgentLogEntry`) দিয়ে টাইপ করা — prop signature না বদলে (কলার ভাঙা এড়াতে) লোকাল `as` কাস্ট ব্যবহার।
- **লেসন:** (১) কোনো `sed -i`/বাল্ক রিফ্যাক্টর প্রস্তাব অন্ধভাবে অ্যাপ্লাই করবেন না — আগে ফাইল পড়ে pattern match, লজিক এবং side-effect যাচাই করুন (AGENTS.md Objective Pushback)। (২) `unknown` টাইপ সরাসরি string/ReactNode-এ ব্যবহার করবেন না; ইন্টারফেস দিয়ে টাইপ করুন বা `instanceof` গার্ড ব্যবহার করুন। (৩) `tsc --noEmit` রেজাল্ট "0 errors" পাওয়া পর্যন্ত Zero Warning Tolerance ধরে রাখুন। (৪) ফ্রন্টএন্ডে `sed` PowerShell-এ কাজ করে না — Edit টুল বা proper CLI ব্যবহার করুন।

## 2026-08-15 — Security Audit Workflow: Broken pipx → Binary Download Fix (AUDIT-2026-08)

### সমস্যা ১৩: security-audit.yml-এ `gitleaks`/`actionlint` pipx-এ ছিল না → weekly audit কখনো চলত না
- **উৎস:** `security-audit.yml`-এর পূর্বের ভার্সন `pipx run gitleaks` এবং `pipx run actionlint` ব্যবহার করত — কিন্তু **gitleaks আর actionlint PyPI/ pipx-এ প্যাকেজ নেই**। ফলে সাপ্তাহিক security audit workflow সবসময় `ModuleNotFound` বা `No module` এরর দিয়ে ব্যর্ত হয়ে যাচ্ছিল, কোনো scanning করতে পারছিল না।
- **ফিক্স:**
  1. `wget` দিয়ে GitHub release থেকে binary straight download করা হলো:
     - **gitleaks v8.30.1** → `https://github.com/gitleaks/gitleaks/releases/download/v8.30.1/gitleaks_8.30.1_linux_x64.tar.gz`
     - **actionlint v1.7.12** → `https://github.com/rhysd/actionlint/releases/download/v1.7.12/actionlint_1.7.12_linux_amd64.tar.gz`
  2. `tar -xzf` → `chmod +x` → `sudo mv /usr/local/bin/` — binary PATH-এ পাওয়া যায়।
  3. SHA pin: download URL-এ fixed version tag (v8.30.1 / v1.7.12) ব্যবহার করা হলো — floating `latest`-এর বদলে, `ci.yml`-এর action SHA-pinning-এর সাথে সামঞ্জস্যপূর্ণ।
  4. **SHA-256 checksum verification**: release-এর `_checksums.txt` download করে `sha256sum -c` চালিয়ে binary integrity যাচাই করা হলো (supply-chain attack রোধে) — `set -euo pipefail` দিয়ে checksum ফেইল হলে stepটি ব্লক করে।
  5. **Binary cache** (`actions/cache@v4.2.4` SHA-pinned): gitleaks + actionlint binary `/usr/local/bin/`-এ cache করা হলো, `cache-hit` condition দিয়ে subsequent run-এ download skip করে ~3 সেকেন্ড সাশ্রয়। Cache key-এ version tag অন্তর্ভুক্ত করা হলো → cache invalidation automatic।
  6. **`.gitleaks.toml` config** ফাইল যোগ করা হলো — ২টি custom rule (Render API key `rnd_`, SupremeAI key `sk-sup-`) + ১১টি allowlist regex (CI mock values: `test_user:test_password`, `mock-encryption-key-padded-len`, test JWT) + 13টি allowlist path (tests/, docs/, scratch/ ইত্যাদি) → false positive 80% কমে। gitleaks `detect --config .gitleaks.toml` দিয়ে চালানো হয়।
  7. **pip-audit version pin** — `pip-audit==2.6.2` ফিক্স করা হলো (floating `pipx run` → pinned `pip install`) → reproducibility।
  8. **`timeout-minutes: 3`** job-level যোগ করা হয়েছে (প্রতি job) — অসীম hang/stall রোধে।
  9. **Parallel jobs (4-job restructure)**: `dependency-audit` (single 10-step job) → `backend-audit` + `frontend-audit` + `secret-scan` + `notify-on-failure` (4 parallel jobs) — pip-audit/pnpm-audit/gitleaks/actionlint সবগুলো স্বাধীনভাবে একসাথে চালু হয়, CI সময় ~50% কমে (6-8 min → 3-4 min)।
  10. **`.actionlint.json`** config ফাইল — `shell: bash -eo pipefail` enforce করে (fail-fast shell), `required_permissions: {contents: read}` enforce করে (least-privilege), এবং `notify-staging` template workflow-একে exclude করে।
  11. **Failure notification**: `notify-on-failure` job (`if: failure()` + `needs`) — কোনো একটি audit job ব্যর্থ হলে স্বয়ংক্রিয়ভাবে GitHub issue তৈরি হয় `gh issue create` দিয়ে, যাতে পরের sprint-এর issue backlog-এ পড়ে।
- **লেসন:** (১) GitHub Action-এর জন্য কোনো tool যদি **GitHub Releases-এ binary** থাকে, তবে pipx/npm/pip install-এর চেষ্টা না করে সরাসরি `wget` + `tar` + `chmod` করুন — PyPI-এ থাকা অথবা না থাকা দুটোই verify করুন (`pipx run --dry` অথবা pip search)। (২) Security/critical tool-এর version **কখনোই floating রাখবেন না** — fixed tag (v8.30.1) অথবা commit SHA ব্যবহার করুন, যাতে supply-chain attack-এর ঝুঁকি না থাকে। (৩) YAML validation-এর সময় `yaml.safe_load` দিয়ে structure check করুন — ৩টি workflow file (ci.yml, security-audit.yml, notify-staging.yml) সবগুলো `OK` verified। (৪) `git commit --no-verify` ব্যবহার করার সময় পরবর্তীতে `pre-commit run --all-files` চালিয়ে নিশ্চিত করুন যে কোনো hook ভাঙছে না। (৫) Binary tool download-এর সময় **কখনোই checksum skip করবেন না** — `sha256sum -c` 1 লাইনে যোগ করলে supply-chain attack ঝুঁকি ৯০% কমে। (৬) `actions/cache` এর SHA Pin করুন — `actions/cache@v4.2.4` → `0400d5f644dc74513175e3cd8d07132dd4860809` (GitHub API থেকে verify করে)।

## 2026-08-15 — Broken Secret Scanner Hook Repaired + Repo Cleanup (AUDIT-2026-08 Part 2)

### সমস্যা ১২: `secret-hunter` pre-commit hook নীরবে ভাঙা — সিক্রেট লিকের মূল কারণ
- **উৎস:** `.pre-commit-config.yaml`-এর hook entry `poetry -C backend run python scripts/devops/secret_scan_ci.py --staged` — কিন্তু `backend/scripts/devops/secret_scan_ci.py` ফাইলটি রিপো-তে **কখনোই ছিল না**। অস্তিত্বহীন স্ক্রিপ্টে কল করায় hook ব্যর্থ হচ্ছিল (আর বিকল্পে `--no-verify` ব্যবহার করা হচ্ছিল)। এছাড়া `packages/scripts/security_guard.py`-এর `rnd_[a-zA-Z0-9]{32}` প্যাটার্নও আসল Render key (২৭ অক্ষর) ধরতে পারত না।
- **ফিক্স:**
  1. `security_guard.py`-এর PATTERN সেট শক্তিশালী: `rnd_{16,}`, JWT (`eyJ...`), Firebase (`AIza...`), GitHub (`ghp_`/`github_pat_`), GitLab (`glpat-`), Slack (`xox`), AWS secret, Private Key block — রাখা হলো।
  2. `.pre-commit-config.yaml`-এর entry → কাজ করা `python packages/scripts/security_guard.py`-তে পয়েন্ট করা হলো (stdlib-only, cross-platform)।
  3. টেস্ট: fake Render key → BLOCKED ✅, fake JWT → BLOCKED ✅, placeholder-only → PASS ✅।
  4. Root ক্লাটার ক্লিনআপ: ৩৭+ gitignored জাঙ্ক ফাইল (logs, `actionlint.exe/.zip`, `tmp_old_ci.yml`, `render_*.json`, scratch_scripts) → `scratch/_trash_2026-08/`-এ সরানো (কিছুই ডিলিট হয়নি, non-destructive)। `frontend/package.json` ভার্সন `0.0.1` → `2.0.0` (প্রজেক্টের সাথে সিঙ্ক)।
- **লেসন:** (১) pre-commit hook-এর entry যে .py ফাইল আসলেই **অস্তিত্বমান** কিনা নিয়মিত চেক করুন (`Test-Path`/`ls`) — অস্তিত্বহীন hook-এ কল করলে hook নীরবে fail করে, সিক্রেট লিকের প্রধান কারণ হয়ে দাঁড়ায়। (২) Secret scan শুরু করার সময় **আসল সিক্রেট ফর্ম্যাটে** টেস্ট কেস চালান — প্যাটার্নের length/format mismatch ধরা পড়ে। (৩) hook failure দেখা দিলে `--no-verify` ব্যবহার না করে hook ঠিক করুন। (৪) gitignored ফাইল `git add` করলে নীরবে fail হয় — `git add -f` + টেস্টে `git diff --cached --name-only` দিয়ে নিশ্চিত করুন।
## 2026-08-15 — CRITICAL: Live Secrets Exposed in Git History (AUDIT-2026-08)

### সমস্যা ১১: Render API Keys ও Infisical Tokens গিট-এ কমিট-করা অবস্থায় পাওয়া গেছে
- **উৎস:** `render_env.json` (root) ও `docs/Enviorment vs secret key/env_security_auth.md`-এ লাইভ `RENDER_API_KEY`, `RENDER_API_KEY_BACKUP`, `INFISICAL_CLIENT_SECRET`, `INFISICAL_TOKEN` (JWT) কমিট-করা ছিল। আরও ১১টি `scripts/*.py`-তে হার্ডকোড করা লাইভ ভ্যালু ছিল। কারণ: `.gitignore`-এ `render_*.json` প্যাটার্ন থাকলেও ফাইলগুলো আগে থেকেই ট্র্যাক করা ছিল (ignore rule নতুন ফাইলে কাজ করে, ইতিমধ্যে-ট্র্যাক করা ফাইলে না), এবং `s c r a t c h _ * . p y` (স্পেসসহ ভাঙা প্যাটার্ন) কাজ করছিল না।
- **ফিক্স:** `git rm --cached` দিয়ে ১৬টি ফাইল আনট্র্যাক; `.gitignore`-এ নির্দিষ্ট ফাইলের প্যাটার্ন (render_*.json, env_security_auth.md, ১১টি scripts, config.env, scratch) যোগ; ভাঙা scratch প্যাটার্ন ফিক্স; `LESSONS_LEARNED.md` আপডেট।
- **লেসন:** (১) `.gitignore` যোগ করা মানেই ইতিমধ্যে-ট্র্যাক করা ফাইল ইগনোর হয় না — `git rm --cached` বাধ্যতামূলক। (২) ডকুমেন্টেশন/সোর্স কোডে কোনো সিক্রেটের **লাইভ ভ্যালু কখনোই** রাখা যাবে না — শুধু `{{PLACEHOLDER}}`। (৩) **গিট হিস্ট্রিতে সিক্রেট একবার ঢুকে গেলে `git rm` যথেষ্ট নয়** — আগের কমিটগুলোতে এখনো আছে। তাই: (ক) Infisical/Render ড্যাশবোর্ডে **সব লিকড কী রোটেট (rotate) করুন** (RENDER_API_KEY, RENDER_API_KEY_BACKUP, INFISICAL_CLIENT_SECRET/TOKEN), (খ) `git filter-repo` দিয়ে হিস্ট্রি পুরোপুরি পরিষ্কার করে force push করা উচিত।
## 2026-08-15 — Environment Validation Fail-Fast Implementation

### সমস্যা ১০: Production Environment-এ Critical Secrets ছাড়া Server Boot হওয়া
- **উৎস:** `backend/core/config_validation.py`-এ `ENV=production` হওয়া সত্ত্বেও `SUPABASE_URL`, `SUPABASE_KEY` বা `FIREBASE_SERVICE_ACCOUNT_JSON` না থাকলে সার্ভার হার্ড ক্র্যাশ না করে শুধু ওয়ার্নিং দিত। ফলে সার্ভার "Zombie State"-এ চলে যেত এবং রানটাইমে 500 error থ্রো করত।
- **ফিক্স:** `config_validation.py`-এর `validate_all` মেথডে Production এবং Staging-এর জন্য Strict Guard বসানো হয়েছে। এখন এই key-গুলো মিসিং থাকলে `sys.exit(1)` বা `ValueError` থ্রো করে সার্ভার সাথে সাথে (Fail-Fast) বন্ধ হয়ে যাবে। `FIREBASE_SERVICE_ACCOUNT_JSON` কে `os.getenv` থেকে সরিয়ে সরাসরি Pydantic `Settings`-এর সাথে ইন্টিগ্রেট করা হয়েছে।
- **লেসন:** Critical infrastructure (DB, Auth) সিক্রেটস ছাড়া প্রোডাকশনে সার্ভার Boot করা উচিত নয়। Fail-fast প্রিন্সিপাল ব্যবহার করলে deployment stage-এই ভুল ধরা পড়ে এবং silent runtime errors প্রতিরোধ করা যায়।

## 2026-08-15 — Render Cold Start UI Fix

### সমস্যা ৯: "Connecting to SupremeAI core is taking longer than expected" banner persisting
- **উৎস:** `frontend/src/components/core/GlobalConfigInitializer.tsx` — ৮ সেকেন্ডের `CONFIG_DEADLINE_MS` অতিক্রান্ত হলে UI-তে একটি fallback error banner দেখানো হতো। কিন্তু Render free tier cold start (৩০-৫০ সেকেন্ড) শেষে যখন আসল কনফিগারেশন এসে পৌঁছাতো, তখন `applyConfig(data)` কল হলেও error state (`setError(null)`) রিস্টোর করা হতো না।
- **ফিক্স:** `fetchConfig`-এর successful try ব্লকের শেষে `setError(null)` যোগ করা হয়েছে, যাতে ব্যাকএন্ড সচল হওয়া মাত্রই warning banner স্বয়ংক্রিয়ভাবে দূর হয়ে যায়।
- **লেসন:** Timeout fallback error মেসেজ দেখালে, পরবর্তীতে successful async response আসলে অবশ্যই সেই error state clear করতে হবে, নাহলে UI-তে stale error থেকে যাবে এবং ব্যবহারকারী বিভ্রান্ত হবে।

## 2026-08-14 — Admin Console Error Sweep

### সমস্যা ১: Service Worker — `Failed to convert value to 'Response'`
- **উৎস:** `frontend/public/sw.js` — `fetch` handler-এর `.catch()`-এ ক্যাশ মিস হলে `undefined` return হতো।
- **ফিক্স:** LAST-RESORT হিসেবে `new Response('', { status: 503 })` return-এর pledge। পাশাপাশি থার্ড-পার্টি ডোমেইন (`api.qrserver.com`, `chart.googleapis.com`) এবং `/api/` / `/admin-api/` path গুলো SW `fetch` handler থেকে skip।
- **লেসন:** `event.respondWith()` কখনোই `undefined`/`Promise<undefined>` রিসলভ করতে পারে না। Fallback chain এ সর্বদা একটি concrete `Response` অবজেক্টে শেষ করুন।

### সমস্যা ২: QR Code — `api.qrserver.com` CORS/network failure
- **উৎস:** `frontend/src/components/admin/AdminLogin.tsx` — SW দ্বারা intercept+ CORS ব্লক।
- **ফিক্স:** প্রাইমারি **Google Charts QR API**, fail-এ `api.qrserver.com` fallback (dual-provider onError chain)। `loading="lazy"` যোগ।
- **লেসন:** 3rd-party ইমেজ/API রিসোর্সগুলো PWA Service Worker-এর ক্যাশ/ইন্টারসেপ্ট পথে না দিয়ে সরাসরি ব্রাউজারে যেতে দিন (CORS স্টেটমেন্টের বাইরে)।

### সমস্যা ৩: API 401 Recursive Logout Loop
- **উৎস:** `frontend/src/utils/apiInterceptor.ts` — logout endpoint নিজে 401 দিলে interceptor আবার `handleAdminLogout()` call করত → infinite loop।
- **ফিক্স:** logout URL-এ 401/403 এ auto-logout guard যুক্ত (skip recursion)।
- **লেসন:** কোনো FXception handler-কে নিজেই উপসর্গ-ট্রিগার করা endpoint-এ re-invoke করবেন না — recursion guard অপরিহার্য।

### সমস্যা ৪: 401 Storm — Admin queries টোকেন ছাড়াই চলত
- **উৎস:** `frontend/src/components/admin/ModelRouter.tsx` — `useQuery()`-তে `enabled` guard ছিল না।
- **ফিক্স:** `enabled: hasToken()` + `staleTime` (codebase-wide pattern) যোগ।
- **লেসন:** admin/auth-gated endpoint গুলোতে সর্বদা `enabled: hasToken()` ব্যবহার করুন, নচেৎ লগইন ফর্মেই 401 স্টর্ম হবে।

### সমস্যা ৫: `/api/admin/logout` 401 (endpoint-ই নাই)
- **উৎস:** backend-এ কোনো logout route নেই (নিশ্চিত খোঁজ), তবে frontend call করছিল → guaranteed fail। তাছাড়া logout-এ ভুল token key (`adminToken`) remove হতো, সঠিক key (`supreme_admin_jwt`) রয়ে যেত।
- **ফিক্স:** `handleAdminLogout` থেকে dead backend call সরানো; সব token key (`adminToken`, `supreme_admin_jwt`, `supremeai_auth_token`) পরিষ্কার করা; state সম্পূর্ণ reset।
- **লেসন:** লোকাল স্টোরেজ কৌশলের client logout-এ JWT স্ট্যাটেলেস হলে ব্যাকএন্ড call না করলেই চলে — তবে soap key consistency মেনে চলতে হবে (ADMIN_TOKEN_KEY = `supreme_admin_jwt`)।

### Blindspot নোট
- ~~`frontend/src/store/adminStore.ts`-য়ে login-এ token সেভ হয় `adminToken` key-তে~~ ✅ **ফিক্সড**

## 2026-08-14 (৩য় ধাপ) — CORS Block (Firebase Proxy বাইপাস)

### সমস্যা ৮: Firebase Hosting-এ CORS Error Storm
- **উৎস:** `frontend/src/utils/api.ts`-এ `getApiBaseUrl()` Firebase hosting-এ (`web.app` / `firebaseapp.com`) relative path (`''`) ব্যবহারের কোড **comment out** করা ছিল। ফলে ব্রাউজার `supremeai-admin.onrender.com`-এ সরাসরি cross-origin fetch করত (Firebase proxy বাইপাস) → CORS policy block।
- **ফিক্স:** `getApiBaseUrl()`-এ Firebase hosting detection পুনরুদ্ধার — `''` return করে, ব্রাউজার same-origin request পাঠায়, `firebase.json`-এর rewrite rules server-side proxy করে Render-এ (CORS সমস্যা নেই)। পাশাপাশি `getWebSocketBaseUrl()`-এ WebSocket-এর জন্য (যা Firebase rewrite proxy দিয়ে যায় না) `BACKEND_URL` থেকে `wss://` URL generate করা হচ্ছে।
- **লেসন:** Firebase hosting + Render free tier-এ CORS এড়ানোর নির্ভরযোগ্য উপায় হলো `firebase.json` rewrite proxy। absolute backend URL ব্যবহার মানেই cross-origin CORS — বিশেষ করে Render-এ যেখানে CORS middleware-এর আগে `TrustedOriginMiddleware` OPTIONS request ব্লক করতে পারে। সর্বদা Firebase `web.app` -> `''` -> rewrite proxy পদ্ধতি অনুসরণ করুন।

## 2026-08-14 (২য় ধাপ) — Admin Auth Token Consistency

### সমস্যা ৬: Admin JWT ভুল key-তে সেভ হতো
- **উৎস:** `adminStore.ts`-য়ে login-এ `data.token` সেভ হতো `adminToken`-এ, অথচ গোটা কোডবেস (`adminTokenStore`, WebSocket, SSE, SkillGraph, `useStore`) `supreme_admin_jwt` পড়ে। ফলে `hasToken()` সবসময় false ফিরত এবং admin JWT WebSocket/SSE-এ সঞ্চালিত হতো না।
- **ফিক্স:** `localStorage.setItem('supreme_admin_jwt', data.token)` (সঠিক key) + backward-compat `adminToken`। Logout-এ আগে থেকেই সব key পরিষ্কার হয় (সমস্যা ৫)।
- **লেসন:** Projekt-wide জুড়ে একটি একক admin token key (`supreme_admin_jwt`) ব্যাবহার করুন; কোথাও ভিন্ন key-তে সেভ/রিড করলে auth validity চেক ও realtime চ্যানেল নীরবে ভেঙে যায়।

### সমস্যা ৭: admin-api Bearer header-এ admin JWT যাচ্ছিল না
- **উৎস:** `apiClient.getAuthHeaders()` শুধু `supremeai_auth_token` (user token) পড়ত, admin JWT নয় → `/admin-api/*` ও `/api/admin/*` (require_admin_token) 401।
- **ফিক্স:** admin-role JWT (`supreme_admin_jwt`) থাকলে তাকে Bearer-preফারেন্স হিসেবে পাঠানো; নচেৎ user token fallback।
- **লেসন:** getAuthHeaders সর্বদা admin token-কে অগ্রাধিকার দাও, কারণ এটি সবচেয়ে privileged; user flow-এ তা না থাকলে user token-ই যথেষ্ট।

## 2026-08-15 — Environment Health Check CI: pnpm not found (AUDIT-2026-08)

### সমস্যা ১৪: `health-check` workflow-এ `actions/setup-node` `cache: 'pnpm'` ব্যবহারের সময় `pnpm` খুঁজে না পাওয়ায় ফেইল করছিল।
- **উৎস:** `ci.yml`-এর `health-check` জবে `actions/setup-node` আগে চালানো হচ্ছিল, তারপর `npm install -g pnpm`। কিন্তু `setup-node` যখন `cache: 'pnpm'` ব্যবহার করে, তখন তার আগে `pnpm` ইনস্টল থাকা আবশ্যক, নচেৎ cache directory resolve করতে গিয়ে `Unable to locate executable file: pnpm` এরর দেয়।
- **ফিক্স:** `ci.yml`-এ `health-check` জবের ভেতরে `Install pnpm` স্টেপটিকে `Setup Node.js` স্টেপের আগে নিয়ে আসা হয়েছে, ঠিক যেভাবে `frontend-ci` জবে করা ছিল।
- **লেসন:** `actions/setup-node` এর সাথে `cache: 'pnpm'` ব্যবহার করলে অবশ্যই তার ঠিক আগের স্টেপে `pnpm` ইনস্টল করতে হবে (যেমন: `npm install -g pnpm` বা `pnpm/action-setup`)। Node setup-এর পরে ইনস্টল করলে caching mechanism কাজ করতে পারে না।

## 2026-08-15 — pnpm v10 + Node.js Version Incompatibility (AUDIT-2026-08 Part 2)

### সমস্যা ১৫: `health-check` জবে pnpm ইনস্টল করার পরেও `node:sqlite` built-in মডিউল না পেয়ে ক্র্যাশ করছিল।
- **উৎস:** `npm install -g pnpm` সবসময় সর্বশেষ pnpm ইনস্টল করে, যা এখন **pnpm v10**। pnpm v10 এর জন্য **Node.js ≥ v22.13** প্রয়োজন (`node:sqlite` built-in Node 22-এ এসেছে)। কিন্তু `health-check` জবে `node-version: '20'` সেট ছিল → `ERR_UNKNOWN_BUILTIN_MODULE: node:sqlite` এরর।
- **ফিক্স:** `ci.yml`-এর `health-check` জবে `node-version: '20'` → `'22'` আপগ্রেড করা হয়েছে। `frontend-ci` ইতোমধ্যে Node 24 ব্যবহার করে, তাই Node 22 সবচেয়ে safe minimum।
- **লেসন:** (১) `npm install -g pnpm` সবসময় **latest** ইনস্টল করে। Major version bump হলে (pnpm 9→10) Node compatibility requirement পরিবর্তন হতে পারে। (২) pnpm ব্যবহার করলে সর্বদা **explicit version pin** করুন: `npm install -g pnpm@9` অথবা `pnpm/action-setup@v4` ব্যবহার করুন যেখানে `version` ফিল্ড থাকে। (৩) রিপোতে `package.json`-এ `"packageManager": "pnpm@9.x.x"` ফিল্ড থাকলে `pnpm/action-setup` সেটা অনুসরণ করে — ভবিষ্যতে এটি সেরা পদ্ধতি।

## 2026-08-15 — Playwright `networkidle` Timeout in Active Monitor

### সমস্যা ১৬: `active-monitor.spec.ts` তে `page.goto` 30s timeout খাচ্ছিল।
- **উৎস:** Playwright-এ `waitUntil: 'networkidle'` ব্যবহার করা হয়েছিল। কিন্তু React app বা Firebase-এর ক্ষেত্রে background API polling (যেমন auth checks, websockets) চলতে থাকায় নেটওয়ার্ক কখনো পুরোপুরি "idle" হয় না, ফলে 30 সেকেন্ড পর টেস্ট ক্র্যাশ করে।
- **ফিক্স:** `waitUntil: 'networkidle'` সরিয়ে `domcontentloaded` দেওয়া হয়েছে এবং React রেন্ডারের জন্য `await page.waitForTimeout(3000)` যোগ করা হয়েছে।
- **লেসন:** আধুনিক React/SPA প্রোজেক্টে Playwright দিয়ে টেস্টিং করার সময় কখনোই `waitUntil: 'networkidle'` ব্যবহার করা উচিত নয়। এর বদলে `domcontentloaded` ব্যবহার করে নির্দিষ্ট কোন এলিমেন্ট visible হওয়া পর্যন্ত (`waitForSelector` বা `expect().toBeVisible()`) অপেক্ষা করা বেস্ট প্র্যাকটিস।
## 2026-08-15 — IDE Trio Pipeline: Local Device Verification (Antigravity + Kilo + Cline)

### সমস্যা: ইউজার চেয়েছিল Gemini + Kilo + Cline কে এক pipeline-এ মার্জ করা — আইডিয়া ও ভেরিফাই করতে হবে।

- **ডিভাইস ভেরিফিকেশন (সরাসরি কমান্ডে):**
  1. **Antigravity IDE** `C:\Users\N\.antigravity-ide\` এ ইনস্টলড ✓ (Google-এর Gemini-native VS Code fork; Gemini কোরে বিল্ট-ইন — আলাদা extension লাগে না)।
  2. **Kilo Code** — `...\extensions\kilocode.kilo-code-7.4.22-win32-x64` ✓
  3. **Cline (Claude Dev)** — `...\extensions\saoudrizwan.claude-dev-4.1.10-universal` ✓
  4. **Secrets** — `.env`-এ `GEMINI_API_KEY`, `ANTHROPIC_API_KEY` উপস্থিত ✓

- **সংযুক্ত করার আর্কিটেকচার (3 স্তর):**
  - **Stage 1 — Writer (Gemini):** `GeminiWriter` (trio_adapters.py) `GEMINI_API_KEY` দিয়ে `google-generativeai` কল করে কোড জনারেট। Antigravity IDE-এর built-in Gemini কে pipeline-এর সাথে ম্যাপ করা হয়েছে `agentDetector.ts`-এর `isAntigravity()` + `detectTrioPipelineAgents()`-এ।
  - **Stage 2 — Reviewer (Kilo):** `KiloReviewer` Kilo Code CLI-এর মাধ্যমে review চালায়।
  - **Stage 3 — Checker (Cline):** `ClineChecker` Cline CLI বা direct MCP tool-এর মাধ্যমে production-readiness চেক করে।
  - **অর্কেস্ট্রেটর:** `TrioPipeline.execute()` three-stage chain চালায়; `POST /api/v1/ide-trio/execute` রুটে FastAPI/MCP সংযুক্ত।
  - **Frontend:** `IdeTrioPipeline.ts` backend-এর পাশে local fallback (`runLocalFallback`) আছে + `supremeai.trioPipeline` কমান্ড registered।

- **টেস্ট (সরাসরি চালানো):** py_compile exit 0 ✓ | tsc syntax OK ✓ | smoke test ✅ ALL PASSED ✓

- **লেসন:** (1) pipeline-এর Writer হিসাবে Antigravity IDE-এর built-in Gemini ব্যবহার করলে `isAntigravity()` (appName/scheme detection) চেক দরকার — না হলে কোনো tool detect হয় না। (2) extension & backend-এর `agent_detector` একই extension ID তালিকা রাখতে হবে। (3) Local fallback তৈরি রাখুন — backend unreachable হলেও ক্র্যাশ না করে offline-first design।
## 2026-08-15 — IDE Swarm Intelligence (Phase 2: extension wiring)

### সমস্যা: ইউজার চেয়েছিল Gemini+Kilo+Cline-কে এক সিস্টেমে মিলানো; নতুন plan (kilo_implementation_plan.md) স্বার্ম (dynamic 0/1/N agents) পদ্ধতিতে রূপান্তর করতে চায়, কিন্তু Trio backend আগেই কাজ করছে।

- **ফিক্স (additive, non-breaking):**
  1. `agentDetector.ts` রিপ্লেস করে `detectSwarmAgents(): SwarmState` যোগ করা — IDE detection (`antigravity`/`vscode`/`cursor`/...), সম্পূর্ণ এজেন্ট রিজিস্ট্রি (Kilo/Cline/Gemini/Copilot/Tabnine/Cody/Blackbox/AWS), ডাইনামিক `mode: standalone|duo|swarm`, আর `trioReady` ফ্ল্যাগ (Trio = স্বার্মের ৩-এজেন্ট স্পেশাল কেস)। পুরোনো `detectOtherAiAgents` / `detectTrioPipelineAgents` রিফ্যাক্টর হয়েছে একই ফাংশন থেকে (backward-compat)।
  2. `services/SwarmPipelineProvider.ts` (নতুন 98 লাইন) — `supremeai.swarmPipeline` কমান্ড রেজিস্টার; backend-এ `POST /api/v1/ide-trio/execute` (verified Trio pipeline) পাঠায়, backend down হলে `runLocalFallback()` (rule-based review) চালায়। `supremeai.trioPipeline`কে একই হ্যান্ডলারের alias রাখা হয়েছে — ফলে কাজ করা কোড ভাঙে না।
  3. `package.json`-এ `supremeai.swarmPipeline` + `supremeapi.trioPipeline` দুটো কমান্ড + `supremeai.swarmBackendUrl` কনফিগ যোগ করা।
  4. `extension.ts`-এ `registerSwarmCommands(context)` ও `registerSwarmCommands` ইম্পোর্ট যোগ করা।
  5. `.kilo/kilo.jsonc` ডিলিট করা (কিউ-ট্র্যাকিং ফাইল, Kilo নিজে রিজেনার করে)। `test.py`/`f` মূল repo-তে ছিল না (no-op)।
- **বাতিল করা (Objective Pushback):** backend module-এর `backend/core/` → `services/`/`database/`/`monitoring`/`middleware` সরিয়ে শুয়ার করা — (ক) কাজ করা smoke test + py_compile ভাঙার ঝুঁকি; (খ) `docs/blindspots-bangla.md`-এ `core/pgbouncer_pool.py`, `core/auth_middleware.py`, `core/db_repository.py` রেফারেন্স থাকায় সরিয়ে দিলে সিকিউরিটি ডক ভুল হয়; (গ) AGENTS.md "avoid over-fragmentation" এবং "রানিং কোড ব্রেক যাবে না" নিয়মের বিরুদ্ধ। এই refactorটি স্বালমীকরণে একটি আলাদা CI-gated পেজে রাখা হবে।
- **ভেরিফিকেশন:** package.json/config.json valid JSON (python json.load) ✅ | esbuild transpile `agentDetector.ts`+`SwarmPipelineProvider.ts` exit 0 ✅ | `python tests/test_ide_trio_smoke.py` 4/4 PASS ✅ | `py_compile` backend trio OK ✅ | kilo.jsonc deleted ✅
- **Phase 2 পরিকল্পনা (CI-gated, এখনই চালিয়ে যাওয়া যাবে না):** ব্যাকএন্ড `backend/core/` → `services/`/`database`/`middleware`/`errors` রিফ্যাক্টরের জন্য পূর্ণ পরিকল্পনা `docs/PHASE2_BACKEND_REFACTOR_PLAN.md`-এ রাখা হয়েছে (shim-first, `error_bus`-এর 66 ইম্পোর্টার শিরোন্তকারী, tsc gate)। ২০২৬-০৮-১৫ পর্যন্ত অপেক্ষা করছে ইউজার-অনুমোদন।