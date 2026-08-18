# 🔐 SupremeAI 2.0 — সিকিউরিটি ও কমপ্লায়েন্স অডিট রিপোর্ট (Security & Compliance Audit)

> **নথি আইডি:** `docs/audit_reports/SECURITY_COMPLIANCE_AUDIT_2026-08-18.md`
> **অডিট তারিখ:** ১৮ আগস্ট ২০২৬
> **অডিটর:** Principal AI Engineer & System Architect
> **পদ্ধতি:** `C:\Users\N\Documents\audit` ফোল্ডারের রেফারেন্স অডিট ফাইলগুলোর (৩টি) সাথে বর্তমান কোডবেসের **READ-ONLY কোড-লেভেল তুলনা**। প্রতিটি ফাইন্ডিং ফাইল:লাইন প্রমাণ-ভিত্তিক। Document দাবির চেয়ে actual কোডকে প্রাধান্য দেওয়া হয়েছে।
> **রেফারেন্স ব্যবহৃত:**
> 1. `FEATURE_FEASIBILITY_ANALYSIS.md`
> 2. `FEATURE_FEASIBILITY_AND_VIABILITY_AUDIT.md`
> 3. `FEATURE_FEASIBILITY_AND_VIABILITY_AUDIT (2).md`

---

## 📌 নির্বাহী সারসংক্ষেপ (Executive Summary)

রেফারেন্স অডিট ফাইলগুলোর সাথে বর্তমান কোডবেস (main tree) তুলনা করে নিম্নোক্ত চিত্র পাওয়া গেছে:

- ✅ **কয়েকটি P0/P1 ইস্যু আসলে ফিক্সড হয়ে গেছে** যা রেফারেন্স ফাইলে এখনও "Open" লেখা আছে — এগুলো **Code-vs-Document ড্রিফট (discrepancy)**:
  - **SEC-001 (RBAC bypass)** — `rbac.py`-তে আর bypass flag নেই; `is_bypass_allowed`-এ হার্ড প্রোডাকশন গার্ড আছে।
  - **SEC-002 (WebSocket token URL-এ)** — `apps/mobile/lib/main.dart`-এ token আর URL query-তে নেই (auth payload-এ যায়)।
  - **AUDIT-018** — skills/voice/files রাউটার এখন register হয়েছে; টেস্টও আছে।
- ❌ **কিছু সিকিউরিটি-সংবেদনশীল সমস্যা এখনও খোলা / নতুন**: live secret অন-ডিস্ক, হার্ডকোডেড Render API key, সাসপেন্ডেড URL রেফারেন্স, stub `/agents/execute`, broken specialized-agents catalog, WebSocket path/auth contract mismatch, mobile brand-rule violation, health-check placeholder, unpinned GitHub Action, `enforce_anti_hacking=false`।
- ⚠️ **সব live সিক্রেট git-tracked নয়** (`.env`, `.secrets`, Render-key scripts gitignore-এ আছে) — ভালো; কিন্তু plaintext-এ ডিস্কে থাকা নিজেই ঝুঁকি।

---

## 🧩 রেফারেন্স অডিট বনাম বর্তমান কোড — ডিসক্রিপেন্সি টেবিল

| ID | রেফারেন্স অডিটের দাবি | বর্তমান কোডে অবস্থা | মূল্যায়ন |
|---|---|---|---|
| **SEC-001** | `rbac.py:172-174`-এ RBAC bypass flag active (Open) | bypass flag নেই; `RoleBasedAccessControl.require()` + `is_bypass_allowed` (production-gated) | ✅ **FIXED** (অডিট আউটডেটেড) |
| **SEC-002** | mobile `main.dart:72-73`-এ token URL-এ (Open) | token আর URL-এ নেই; auth-message-এ যায় | ✅ **PARTIAL-FIX** (মোবাইল সাইড) |
| **AUDIT-003** | mobile main.dart-এ hardcoded localhost+token | localhost নেই; `String.fromEnvironment` derive | ✅ **FIXED** |
| **AUDIT-018** | `/skills/catalog`, `/voice/voices`, `/files/{path}` broken (Open) | routers.py-এ voice/skills/files register হয়েছে; TODO.md বলছে 11/11 test pass | ✅ **FIXED** (অডিট আউটডেটেড) |
| **AUDIT-015** | CostGuard `validate_budget()` test-only (Open) | `check_budget()` llm_gateway-এ wired; `validate_budget()`/`record_spend()` এখনও tier-router-এ wire নয় | ⚠️ **PARTIAL** |
| **AUDIT-006** | ১৫১টি `@vX` unpinned (Open) | প্রায় সব action SHA-pinned; `google-github-actions/auth@v2` (২ টি) এখনো unpinned | ⚠️ **PARTIAL** |
| **SEC-004** | ৪টি test ফাইলে `os.system('rm -rf /')` (Open) | `backend/tests/`-এর ৪টি ফাইল ফিক্সড (`echo test`); টপ-লেভেল `tests/`-এ এখনো test-payload | ⚠️ **PARTIAL** |

> **বিঃদ্রঃ** `.kilo/worktrees/` ও `archive/` হলো পুরোনো snapshot/worker — এগুলোর রেফারেন্স এড়িয়ে main tree-তে জোর দেওয়া হয়েছে।

---

# 🔴 ১. ক্রিটিকাল ও উচ্চ-অগ্রাধিকার ফাইন্ডিং (P0 / P1)

## FIND-001 — P0 | Specialized-Agents ক্যাটালগ এখনো Broken (500)
- **প্রমাণ:** `backend/api/routes/agents.py:73,85,97,109,120,131,142,153,170,181` — `agents.legal_agent` / `agents.medical_agent` / `agents.trading_agent` / `agents.research_assistant` import করে।
- **দেখা:** `backend/agents/` ফোল্ডারে **এই মডিউলগুলো কোনোটি নেই** (এখানে আছে autonomous/ephemeral/headless_terminal/insight_mage/skill_* প্রভৃতি, কিন্তু legal/medical/trading/research নেই)।
- **প্রভাব:** `/api/agents/legal/analyze`, `/medical/*`, `/trading/*`, `/research/*` কল করলে `ModuleNotFoundError` → HTTP 500। Status endpoint-গুলো hardcoded "active" return করে।
- রেফারেন্স অডিটের সাথে **মিলেছে** (দাবি সঠিক, এখনও খোলা)।

## FIND-002 — P0 | `/api/v1/agents/execute` — Stub Live, Real Not Mounted
- **প্রমাণ:** `backend/api/routes/agent.py` (stub) `@router.post("/execute")` → hardcoded `response_text = f"Task {...} executed successfully. Prompt processed: ..."`। এটা `api/routers.py:40`-এ register (`api.routes.agent`, prefix `""`)।
- **সমস্যা:** বাস্তব ইমপ্লিমেন্টেশন `backend/api/routes/agent_tasks.py:57` (`@agent_router.post("/execute")`, prefix `/api/v1/agents`) **routers.py-তে register করা হয়নি**।
- **অতিরিক্ত:** Stub-এর Pydantic স্কিমা `{task_id, prompt}`; কিন্তু frontend `frontend/src/services/agentService.ts:16` পাঠায় `{instruction}` → schema mismatch → 422 বা misleading "success"।
- **প্রভাব:** Frontend agent execution thinks work happened কিন্তু আসলে ফেক (fake) output। **Trust/নিরাপত্তার জন্য বিপজ্জনক।**
- রেফারেন্স অডিটের সাথে সামঞ্জস্যপূর্ণ (collision → এখন আরও খারাপ: real-unmounted)।

## FIND-003 — P0/HIGH | Plaintext Live Secrets অন-ডিস্ক (ডিস্ক হাইজিন)
- **প্রমাণ:**
  - `.env:123` — **LIVE `SUPABASE_SERVICE_ROLE_KEY`** (JWT, `role: service_role`) + `.env:120` comment-এ আরেকটি key (`sb_secret_...`)।
  - `.env` — **LIVE `JWT_SECRET`** (মোটামুটি strong)।
  - `scripts/check_deploys.py:5`, `scripts/sync_secrets_to_frontend.py:5`, `scripts/test_render_api.py:3`, `scripts/trigger_deploys.py:4` — **`RENDER_API_KEY = "rnd_S0H7uYcNWmqX3jcepMTBL9WXghGP"`** (hardcoded, plus hardcoded `SERVICE_ID`s)।
  - `backend/core/config_validation.py:85` — **hardcoded docs fallback password `"supreme-admin-2026-prod"`**।
- **ভালো দিক:** `git check-ignore` নিশ্চিত — `.env`, `.env.backup`, `.secrets/jwt_secret.key`, `frontend/.env`, Render-key scripts **সব gitignored**; `git log -S`-এ Render key commit ইতিহাসে পাওয়া যায়নি। `secrets_registry.yaml` tracked কিন্তু কেবল মেটাডেটা (নাম), value নেই।
- **ঝুঁকি:** চুরি/backup/force-add/কনফিগ লিক হলে service-role DB access + infra API। **সুপারিশ:** কীগুলো vault/Infisical + render dashboard-এ, লোকাল থেকে মুছে দিন; Render key rotate করুন।

## FIND-004 — P1 | WebSocket Contract Mismatch (Mobile ↔ Backend)
- **প্রমাণ:**
  - Mobile `main.dart:69` → `wss://<API_BASE>/api/ws/chat`; API_BASE default `https://supremeai-a.web.app` (static Firebase shell, backend নয়)।
  - Backend `websocket_agent.py:11` prefix `/ws`, `:114` route `/chat` → **`/ws/chat`**; `:88` `_authenticate` **token `query_params["token"]`-এ চায়** (URL-এ)।
- **প্রভাব:** (ক) path mismatch (`/api/ws/chat` vs `/ws/chat`); (খ) auth transport mismatch — mobile token একটি auth JSON-message-এ পাঠায়, কিন্তু backend first-message-কে chat prompt ধরে (empty content → LLM)। ফলে mobile WebSocket chat **এন্ড-টু-এন্ড ভাঙা**।
- **সিকিউরিটি নোট:** backend এখনো query-param-এ token চাওয়ায় token-এর URL/log leak vector টিকে আছে। রেফারেন্সের SEC-002/AUDIT-003-এর "PARTIAL" অবস্থা।


## FIND-005 — P1 | Mobile ব্র্যান্ড-রুল ভায়োলেশন + Backend Bypass (Direct Gemini)
- **প্রমাণ:** `apps/mobile/pubspec.yaml:25` `google_generative_ai: ^0.4.0`; `apps/mobile/lib/providers/orchestration_provider.dart:7` import; `:287` `GenerativeModel(model: activeModel ?? 'gemini-1.5-flash', apiKey: geminiKey)`।
- **প্রভাব:** ক্লায়েন্টে সরাসরি ৩য়-পক্ষ LLM কল + **Gemini ব্র্যান্ড এক্সপোজ** — AGENTS.md-এর "কখনো ৩য়-পক্ষ AI নাম এক্সপোজ করবে না", model-agnostic ও thin-client দর্শন লঙ্ঘন। LLM key ক্লায়েন্টে চলে যায়।
- রেফারেন্স অডিটের সাথে মিলেছে (mobile brand violation)।

## FIND-006 — P1 | Hardcoded/Stale Endpoint URLs (Production Config Drift) — VERIFIED

**কোড-লেভেল প্রমাণ (main tree):**

| রেফারেন্স | ফাইন্ডিং (main tree-এ আছে) | প্রমাণ |
|---|---|---|
| `.env` | `SUPREMEAI_ADMIN_BACKEND_URL="https://supremeai-admin.onrender.com"` (SUSPENDED) | `.env:123` — live secret file, gitignored কিন্তু ডিস্কে plaintext |
| `.env` | `VITE_ADMIN_BACKEND` = suspended URL | `frontend/.env` — gitignored |
| `.env` | `VITE_USER_BACKEND="https://supremeai-worker.paykaribazaronline.workers.dev"` (probe→HTTP 401) | `.env` |
| `envs/render-backend.env` | suspended admin URL | `envs/render-backend.env:25` |
| `envs/render-studio-client.env` | suspended admin URL | `envs/render-studio-client.env:16` |
| `envs/vercel.env` | suspended admin URL | `envs/vercel.env:15` |
| `.github/workflows/supreme-core-ci.yml:1723` | default admin URL = suspended | `VITE_ADMIN_BACKEND: ${{ vars.SUPREMEAI_ADMIN_API_URL || 'https://supremeai-admin.onrender.com' }}` |
| `.github/workflows/supreme-core-ci.yml:1725` | `pnpm --dir apps/studio-client run build:admin` — **ডিরেক্টরি নেই** (`apps/studio-client` নেই; সঠিক `frontend/`) | CI-তে build step fail → deploy বন্ধ |

**স্ট্যাটাস:** ❌ **খোলা** (কোড-লেভেল প্রমাণ রয়েছে; `.kilo/worktrees/` snapshot শুধু পুরোনো অনুলিপি)।
- **প্রমাণ:**
  - `.env` `SUPREMEAI_ADMIN_BACKEND_URL="https://supremeai-admin.onrender.com"` (SUSPENDED), `VITE_ADMIN_BACKEND`-ও ওই URL, `VITE_USER_BACKEND="https://supremeai-worker.paykaribazaronline.workers.dev"` (live probe→ **HTTP 401**)।
  - `envs/render-backend.env:25`, `envs/render-studio-client.env:16`, `envs/vercel.env:15` — suspended URL।
  - `.github/workflows/supreme-core-ci.yml:1723` default admin URL = suspended; `:1725` `pnpm --dir apps/studio-client run build:admin` (ডিরেক্টরি নেই)।
  - `apps/mobile/lib/providers/orchestration_provider.dart:89` hardcoded `https://supremeai-api-lhlwyikwlq-uc.a.run.app/api/task/stream/` (GCP Cloud Run)।
- **ভালো দিক:** `frontend/src/utils/api.ts:8,15` সঠিক default `https://supremeai-backend-docker.onrender.com`; কিন্তু root `.env` এই default-কে override করতে পারে।
- **প্রভাব:** user-facing chat path সঠিক backend পায় না; admin console dead URL-এ যায়। LESSONS_LEARNED (2026-08-17)-এর দাবি ও actual `.env`-এর মধ্যে **ড্রিফট**।

## FIND-007 — P1 | Frontend CI/Deploy এখনো `apps/studio-client/`-কে নির্দেশ করে (মিস-পয়েন্টেড)
- **প্রমাণ:** `apps/`-এ শুধু `desktop`, `docs`, `mobile` — **`studio-client` নেই**; আসল frontend `frontend/`-এ। তবু:
  - `supreme-core-ci.yml:142-143` (filter), `:1725` (build), `maintenance_pipeline.yml:373,378,430-437` (artifact/preview), `.github/scripts/dependency_upgrader.py:94-96`, root `vercel.json`।
- **প্রভাব:** Frontend GitHub-এর মাধ্যমে ship হয় না (CI fail)। রেফারেন্স অডিটের blocker #4-এর সাথে মিলেছে, এখনও খোলা।

---

# 🟠 ২. মাঝারি-অগ্রাধিকার ফাইন্ডিং (P2)

## FIND-008 — P2 | Unpinned GitHub Action (Supply-chain)
- `supreme-core-ci.yml:949` (`if: false`) ও `:1970` (active, production env job) — `google-github-actions/auth@v2` **SHA-pinned নয়**।
- বাকি প্রায় সব action SHA-pinned (ভালো), তাই AUDIT-006 প্রায় মেটানো; এই ২টি বাকি।

## FIND-009 — P2 | `enforce_anti_hacking=false` (Destructive-Op Defense Disabled)
- `backend/core/config_fields.py:53` default `False`; `infrastructure/render.admin.yaml:42-43` explicit `ENFORCE_ANTI_HACKING: false` (alert-only)। অ্যান্টি-হ্যাকিং (JIT OTP/ধ্বংসাত্মক কমান্ড গেট) তাই enforce-মোডে নয়।

## FIND-010 — P2 | Health-Check DB Probe Placeholder (Misleading Monitoring)
- `backend/core/health_check.py:146-163` — `check_database()` আসলে DB-তে সংযোগ করে না; hardcoded `"connected": True` + `HEALTHY` return। সুতরাং `/api/v1/health` DB-ডাউন হলেও "healthy" দেখাবে → monitoring/compliance প্রতারণা।

## FIND-011 — P2 | Orphaned/Broken কোড
- `backend/api/routes/chat.py` — **`api/routers.py`-এ register নয়** (dead file; রেফারেন্স অডিটেও উল্লেখ)।
- `backend/services/data` — শুধু `gcp_firestore_queue.db`, কোড নেই (STUB)।
- `core/health/self_healer.py` — প্যাটার্ন স্ক্যান আছে কিন্তু auto-remediation `AUTO_REMEDIATION_DRY_RUN=true` (default dry-run)।
- `numpy` পোয়েট্রি লকে **দুটি সংস্করণ** (1.26.4 ও 2.5.2) — সম্ভাব্য কনফ্লিক্ট।

## FIND-012 — P2 | Test-File Dangerous-Payload রেসিডিউ
- `backend/tests/`-এ ৪টি ফাইলে `rm -rf /` → `echo test` (ফিক্সড), কিন্তু টপ-লেভেল `tests/test_agents_skill_ingestor.py:44`, `tests/test_e2e_chat.py:100`, `tests/test_skill_pipeline.py:23` — এখনো `os.system('rm -rf /')`-কে **input payload** হিসেবে ব্যবহার করে। এগুলো সাধারণত `echo test`-এ বদলানো উচিত (isolated container প্রোটোকল ছাড়া ঝুঁকি)।

## FIND-013 — P2/LOW | Dependency CVE-অডিট (AUDIT-014)
- বর্তমান lock-এ বড় প্যাকেজ সংস্করণ বেশ সাম্প্রতিক (fastapi 0.136.3, starlette 1.3.1, cryptography 48.0.1, urllib3 2.7.0) — আপগ্রেড/রিমিডিয়েশন হচ্ছিল। তবে `passlib 1.7.4` EOL (শেষ রিলিজ ২০২০)। রানটাইমে `pip-audit`/`safety` চালিয়ে **বর্তমান CVE-ভিত্তিক রিপোর্ট নিশ্চিত করুন** (এখানে scanner চালানো যায়নি)।


---

# 🟢 ৩. ইতিবাচক / কমপ্লায়েন্স-ঠিক (নিশ্চিত GOOD PRACTICES)

- `.env`, `.env.backup`, `.secrets/*`, Render-key scripts, `frontend/.env` — সব **gitignored**; tracked-history-তে Render key পাওয়া যায়নি। ✅
- `render.yaml` — সব সার্ভিসে `autoDeploy: false` (CI = একমাত্র deploy authority)। ✅
- `.env.example` — সব placeholder, কোনো live key নেই; tracked `secrets_registry.yaml`-এ কেবল মেটাডেটা (নাম+criticality), value নেই। ✅
- `allow_test_auth_bypass`/`allow_test_origin_bypass` — default `False` + `is_bypass_allowed`-এ `ENV=production` হলে hardcoded `False`। ✅
- SHA-pinning — প্রায় 100% action-এ প্রয়োগ (AUDIT-006 প্রায় মেট)। ✅
- `tools_ops` এখন `_admin_paths`-এ (route-leakage ঠেকানো)। ✅
- AUDIT-018 (skills/voice/files) — fix + test। ✅
- Scraper microservice-এ SSRF fix (`is_safe_url`) — রিপোর্ট/টেস্টে উল্লেখ। ✅

---

# 🎯 রিকমেন্ডেশন (অগ্রাধিকারক্রম)

1. **[P0]** `scripts/*.py`-এর hardcoded `RENDER_API_KEY` + `SERVICE_ID` মুছে env-var/Infisical-এ নিন; **Render key rotate করুন**। `.env`-এর service-role key ও JWT secret vault-এ সরান; লোকাল plaintext মুছুন।
2. **[P0]** `/api/v1/agents/execute` — `agent_tasks.py` (real) register করুন; `agent.py` stub-এর schema `{task_id,prompt}` frontend `{instruction}`-এর সাথে মেলান বা remove করুন।
3. **[P0]** Specialized-agents ক্যাটালগ — `backend/tools/ai_agents/*`-এ implement বা রেফারেন্স সংশোধন; অন্যথায় 400/501 দিয়ে remove করুন।
4. **[P1]** WebSocket — একই path (`/ws/chat`) ব্যবহার; token-কে প্রথম auth-message-এ (URL-এ নয়) ভেরিফাই করুন; mobile `API_BASE_URL` আসল backend-এ (default fixed) করুন।
5. **[P1]** mobile-এ direct Gemini প্রত্যাহার → backend `model_router` হাব; `.env`-এর suspended/dead URL (`supremeai-admin.onrender.com`, `supremeai-worker...`) টার্গেটে বদলান এবং `envs/*`/CI/WF সিঙ্ক করুন।
6. **[P1]** Frontend CI `apps/studio-client` → `frontend/` (workflows, vercel.json, dependency_upgrader)।
7. **[P1]** `config_validation.py:85` hardcoded `supreme-admin-2026-prod` fallback বাদ দিন; production-এ missing docs password → fail-fast boot করুন।
8. **[P2]** `google-github-actions/auth@v2` → SHA-pin; `.gitleaks`-কে pre-commit/config hook-এ সক্রিয় করুন।
9. **[P2]** health-check DB probe বাস্তব সংযোগ/query-ভিত্তিক করুন; `enforce_anti_hacking`-এ production-এ `true` বিবেচনা করুন।
10. **[P2]** টপ-লেভেল `tests/`-এর `rm -rf /` payload → `echo test`; `pip-audit`/`safety` চালিয়ে CVE-ভিত্তিক remediate করুন; duplicate numpy ঠিক করুন।

---

*এই রিপোর্টটি READ-ONLY অডিট — কোনো কোড পরিবর্তন করা হয়নি। প্রতিটি ফাইন্ডিং কোড/লাইভ-প্রোব প্রমাণ-ভিত্তিক। রেফারেন্স অডিটের সাথে কোডের মধ্যে যে ড্রিফট পাওয়া গেছে তা উপরিউক্ত টেবিলে দেখানো হয়েছে।*

