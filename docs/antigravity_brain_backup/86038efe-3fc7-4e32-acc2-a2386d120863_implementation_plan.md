# SupremeAI 2.0 — ফাইল পরিষ্কার, একত্রীকরণ ও পুনর্গঠন পরিকল্পনা

> **লক্ষ্য**: অপ্রয়োজনীয় ফাইল মুছে ফেলা, ডুপ্লিকেট মার্জ করা এবং প্রজেক্ট স্ট্রাকচার এমনভাবে সাজানো যেন কোনো কিছু ভাঙে না।

---

## পটভূমি (Background)

বর্তমান প্রজেক্টে নিম্নলিখিত সমস্যা চিহ্নিত হয়েছে:
- **ডুপ্লিকেট ফাইল**: একই নামের ফাইল একাধিক ডিরেক্টরিতে রয়েছে (যেমন `swarm_orchestrator.py` ৩টি জায়গায়)
- **অব্যবহৃত ফাইল**: রুট-লেভেলে বিচ্ছিন্ন স্ক্রিপ্ট যেগুলো কোনো মডিউলের অংশ নয়
- **অসংগঠিত স্ট্রাকচার**: `backend/core/` তে ১০০+ ফাইল যা বিভিন্ন দায়িত্বে মিশ্রিত
- **টেস্ট ফাইল ভুল জায়গায়**: `backend/adaptive_engine/` ও `backend/tools/` এ test ফাইল আছে
- **বাইনারি ফাইল**: `render.exe` (24MB), `render_cli.zip` (8MB) রুটে থাকা উচিত নয়

---

## ⚠️ ব্যবহারকারীর মনোযোগ প্রয়োজন

> [!CAUTION]
> এই পরিকল্পনাটি বাস্তবায়নের আগে অবশ্যই একটি **git branch** তৈরি করুন এবং সব পরিবর্তন সেখানে করুন। Production-এ merge করার আগে সম্পূর্ণ CI পাস হতে হবে।

> [!WARNING]
> `backend/core/` ডিরেক্টরি পুনর্গঠনের ফলে অনেক import path পরিবর্তিত হবে। প্রতিটি মার্জের পর `pytest` রান করতে হবে।

> [!IMPORTANT]
> **ওপেন প্রশ্ন**: `render.exe` ও `render_cli.zip` কি সত্যিই দরকার? এগুলো `.gitignore`-এ নেই, তাই git ট্র্যাক করছে। এগুলো মুছে দেওয়া যাবে কি?

---

## খোলা প্রশ্ন (Open Questions)

1. **`evolution/` রুট ডিরেক্টরি** — এটি কি `backend/evolution/` এর সাথে মার্জ করা যাবে? নাকি ইচ্ছাকৃতভাবে আলাদা?
2. **`apps/web-chat/`** — এটি কি `apps/studio-client/` থেকে আলাদা প্রোজেক্ট? নাকি অপ্রচলিত?
3. **`tools/` রুট ডিরেক্টরি** — এটি কোন উদ্দেশ্যে? `backend/tools/` থেকে আলাদা কেন?
4. **`interfaces/` রুট ডিরেক্টরি** — এর ব্যবহার কী?
5. **`data/` রুট ডিরেক্টরি** — `backend/data/` থেকে আলাদা কেন?

---

## চিহ্নিত সমস্যা ও সমাধান

### ১. ডুপ্লিকেট ফাইল (DUPLICATE FILES)

| ফাইল নাম | অবস্থান ১ | অবস্থান ২ | অবস্থান ৩ | সিদ্ধান্ত |
|---|---|---|---|---|
| `swarm_orchestrator.py` | `backend/brain/` (1.8KB - stub) | `backend/core/` (11.7KB - সম্পূর্ণ) | `backend/engine/` (6.2KB - আংশিক) | `core/` রাখো, বাকি ২টি মুছো |
| `evolution_engine.py` | `backend/core/` (17.6KB - সম্পূর্ণ) | `evolution/` (541B - stub) | — | `core/` রাখো, রুটেরটি মুছো |
| `cost_auditor.py` | `backend/monitoring/` (833B - stub) | `backend/tools/` (2.8KB - সম্পূর্ণ) | — | `tools/` রাখো, `monitoring/` মুছো |
| `github_agent.py` | `backend/services/` (5.4KB) | `backend/tools/` (4.9KB) | — | মার্জ করে `tools/` রাখো |
| `code_smell_detector.py` | `backend/tools/` (23KB - সম্পূর্ণ) | `scripts/` (13KB - পুরনো) | — | `tools/` রাখো, `scripts/` মুছো |
| `fuzz_sandbox.py` | `backend/tools/` (7.9KB) | `scripts/` (7.4KB) | — | `tools/` রাখো, `scripts/` মুছো |
| `generate_push_summary.py` | রুট (10KB) | `scripts/` (3.6KB) | — | `scripts/` রাখো, রুটেরটি মুছো |
| `update_render.py` | রুট (951B) | `scripts/` (824B) | — | `scripts/` রাখো, রুটেরটি মুছো |
| `cloud_sandbox_orchestrator.py` | `backend/core/` (11.2KB) | `backend/tools/` (5.9KB - stub) | — | `core/` রাখো, `tools/` মুছো |
| `task_router.py` | `backend/core/` (3.8KB) | `backend/tools/` (2.7KB) | — | `core/` রাখো, `tools/` মুছো |
| `tenant_rate_limiter.py` | `backend/tools/` (8.6KB - সম্পূর্ণ) | `backend/middleware/` (1.6KB - wrapper) | — | `tools/` রাখো, `middleware/` wrapper ঠিক রাখো |
| `docker-compose.yml` | রুট | `backend/core/` | — | রুটেরটি রাখো, `core/`-এরটি মুছো |
| `dummy_registry.json` | রুট | `backend/` | — | `backend/` রাখো, রুটেরটি মুছো |
| `pytest.ini` | রুট | `backend/` | — | `backend/` রাখো, রুটেরটি মুছো |
| `.coveragerc` | রুট | `backend/` | — | `backend/` রাখো, রুটেরটি মুছো |
| `.dockerignore` | রুট | `backend/` | — | উভয় রাখো (আলাদা scope) |
| `.gcloudignore` | রুট | `backend/` | — | উভয় রাখো (আলাদা scope) |

---

### ২. অপ্রয়োজনীয় ফাইল (UNNECESSARY FILES)

#### রুট ডিরেক্টরিতে অপ্রয়োজনীয়:

| ফাইল | কারণ | সিদ্ধান্ত |
|---|---|---|
| `render.exe` (24MB) | বাইনারি, git-এ থাকা উচিত নয় | **মুছো** + `.gitignore`-এ যোগ করো |
| `render_cli.zip` (8.5MB) | বাইনারি আর্কাইভ | **মুছো** + `.gitignore`-এ যোগ করো |
| `render_temp/` | অস্থায়ী ফোল্ডার | **মুছো** |
| `coverage.json` (81KB) | জেনারেটেড ফাইল | `.gitignore`-এ যোগ করো |
| `firebase-debug.log` (114KB) | লগ ফাইল | **মুছো** + `.gitignore`-এ যোগ করো |
| `job_log.txt` (59KB) | লগ ফাইল | **মুছো** + `.gitignore`-এ যোগ করো |
| `test_db_path` (রুট) | SQLite ফাইল | **মুছো** + `.gitignore`-এ যোগ করো |
| `create_python_service.py` | একবার ব্যবহারের স্ক্রিপ্ট | `scripts/` এ সরাও |
| `create_render_service.py` | একবার ব্যবহারের স্ক্রিপ্ট | `scripts/` এ সরাও |
| `patch_render.py` | একবার ব্যবহারের স্ক্রিপ্ট | `scripts/` এ সরাও |
| `update_render_env.py` | একবার ব্যবহারের স্ক্রিপ্ট | `scripts/` এ সরাও |
| `setup_kms.sh` | একবার ব্যবহারের স্ক্রিপ্ট | `scripts/` এ সরাও |
| `security-scan.yml` | CI file রুটে থাকা উচিত নয় | `.github/workflows/` এ সরাও |
| `ADR-001-firestore-for-tenancy.md` | docs-এ থাকা উচিত | `docs/03-architecture/` এ সরাও |
| `DFD-001-new-user-signup.md` | docs-এ থাকা উচিত | `docs/03-architecture/` এ সরাও |
| `SEQ-001-canary-deployment.md` | docs-এ থাকা উচিত | `docs/03-architecture/` এ সরাও |
| `THREAT-MODEL-001-authentication.md` | docs-এ থাকা উচিত | `docs/09-security/` এ সরাও |
| `CI_PIPELINE.md` | docs-এ থাকা উচিত | `docs/05-operations/` এ সরাও |
| `IMPLEMENTATION_STATUS.md` | docs-এ থাকা উচিত | `docs/01-project/` এ সরাও |
| `PRODUCTION_READINESS_GUIDE.md` | docs-এ থাকা উচিত | `docs/05-operations/` এ সরাও |
| `agent_rules.json` | `config/` এ থাকা উচিত | `config/` এ সরাও |
| `scratch/` | অস্থায়ী ডিরেক্টরি | `.gitignore`-এ যোগ করো |
| `playwright-report/` | জেনারেটেড | `.gitignore`-এ যোগ করো |
| `test-results/` | জেনারেটেড | `.gitignore`-এ যোগ করো |
| `docs/codebase_dump.md` (4.5MB!) | জেনারেটেড, বিশাল ফাইল | `.gitignore`-এ যোগ করো |
| `backend/requirements.txt` (350KB!) | poetry.lock আছে, redundant | মুছো বা আপডেট করো |

#### backend/ ডিরেক্টরিতে:

| ফাইল | কারণ | সিদ্ধান্ত |
|---|---|---|
| `backend/test_db_path` | SQLite artifact | **মুছো** |
| `backend/coverage.json` (109KB) | জেনারেটেড | `.gitignore`-এ |
| `backend/run_roundtrip_tests.py` | `scripts/` এ থাকা উচিত | `scripts/` এ সরাও |
| `backend/dummy_registry.json` | `config/` এ থাকা উচিত | `config/` এ সরাও |
| `backend/adaptive_engine/test_platform_learner.py` | ভুল জায়গায় test | `backend/tests/` এ সরাও |
| `backend/adaptive_engine/test_agent_department.py` | ভুল জায়গায় test | `backend/tests/` এ সরাও |
| `backend/brain/swarm_orchestrator.py` | stub, `core/` এর সম্পূর্ণ version আছে | **মুছো** |
| `backend/tools/backend_tests.yml` | CI file, ভুল জায়গায় | `.github/workflows/` এ সরাও |
| `backend/tools/test_*.py` (৫টি) | ভুল জায়গায় test | `backend/tests/` এ সরাও |
| `backend/core/docker-compose.yml` | রুটে আছে | **মুছো** |
| `backend/core/_write_auth_middleware.py` | `_` prefix = draft/unused | পর্যালোচনা করো, সম্ভবত মুছো |
| `evolution/evolution_engine.py` | stub, `backend/core/` এ সম্পূর্ণ version | **মুছো** |
| `scripts/observability_report.json` | জেনারেটেড | `.gitignore`-এ |

---

### ৩. backend/core/ পুনর্গঠন (REFACTORING)

বর্তমানে `backend/core/` তে **১০০টি** ফাইল আছে — এটি একটি "god module" সমস্যা। নিচে সাজানো কাঠামো:

```
backend/core/
├── config/               # [নতুন] কনফিগ ফাইল
│   ├── config.py         # (আগে core/config.py)
│   ├── config_cache.py
│   ├── config_proxy.py
│   └── constants.py
├── security/             # [নতুন] সিকিউরিটি ফাইল
│   ├── auth_middleware.py
│   ├── api_key_middleware.py
│   ├── honeypot_middleware.py
│   ├── prompt_firewall.py
│   ├── input_sanitizer.py
│   ├── rbac.py
│   ├── secret_vault.py
│   ├── security_vault.py (secret_vault-এ মার্জ)
│   ├── secure_credential_store.py
│   └── origin_validator.py
├── messaging/            # [নতুন] মেসেজিং
│   ├── event_bus.py
│   ├── events.py
│   ├── pubsub.py
│   ├── gcp_pubsub_queue.py
│   ├── nats_messaging.py
│   └── upstash_redis_queue.py
├── cache/                # [নতুন] ক্যাশিং
│   ├── multi_layer_cache.py
│   ├── semantic_cache.py
│   ├── autocache_proxy.py
│   └── redis_manager.py
├── orchestration/        # [নতুন] অর্কেস্ট্রেশন
│   ├── agent_orchestrator.py
│   ├── swarm_orchestrator.py
│   ├── cloud_sandbox_orchestrator.py
│   └── task_queue_enhanced.py
├── llm/                  # [নতুন] LLM গেটওয়ে
│   ├── llm_gateway.py
│   ├── token_budget.py
│   ├── token_deductor.py
│   └── free_tier_tracker.py
├── health/               # [নতুন] স্বাস্থ্য পর্যবেক্ষণ
│   ├── health_monitor.py
│   ├── health_probes.py
│   └── self_healer.py
└── (মূল ফাইল)
    ├── app.py
    ├── lifespan.py
    ├── logging_config.py
    └── telemetry.py
```

> [!IMPORTANT]
> এই পুনর্গঠনে **প্রতিটি ফাইলে** import path আপডেট করতে হবে। এটি সবচেয়ে ঝুঁকিপূর্ণ ধাপ।

---

### ৪. রুট ডিরেক্টরি পরিষ্কার (FINAL ROOT STRUCTURE)

**লক্ষ্য কাঠামো:**
```
supremeai_2.0/
├── .github/              # CI/CD workflows
├── apps/
│   ├── studio-client/    # React/Vite frontend
│   ├── mobile/           # Flutter
│   └── web-chat/         # Web chat (যদি প্রয়োজন হয়)
├── backend/              # FastAPI backend
├── config/               # Global config JSONs
├── docs/                 # সব documentation
├── infrastructure/       # Terraform, Cloudflare
├── packages/             # Shared packages
├── scripts/              # সব helper scripts
├── skills/               # Dynamic skills
├── tools/                # VS Code extension (যদি থাকে)
├── .env.example          # শুধু example
├── docker-compose.yml    # Dev docker setup
├── firebase.json
├── package.json
├── pnpm-workspace.yaml
├── turbo.json
└── README.md
```

---

## প্রস্তাবিত পরিবর্তন (Proposed Changes)

### ধাপ ১: বড় বাইনারি ও লগ ফাইল মুছো (নিরাপদ, ১ম)

#### [DELETE] রুটের অপ্রয়োজনীয় ফাইল
- `render.exe` — 24MB বাইনারি
- `render_cli.zip` — 8.5MB আর্কাইভ
- `render_temp/` — অস্থায়ী ডিরেক্টরি
- `firebase-debug.log` — লগ
- `job_log.txt` — লগ
- `test_db_path` — SQLite artifact
- `coverage.json` — জেনারেটেড
- `playwright-report/` — জেনারেটেড
- `test-results/` — জেনারেটেড
- `backend/test_db_path` — SQLite artifact
- `backend/coverage.json` — জেনারেটেড

#### [MODIFY] [.gitignore](file:///c:/Users/n/supremeai/supremeai_2.0/.gitignore)
এই প্যাটার্নগুলো যোগ করো:
```
render.exe
render_cli.zip
render_temp/
*.log
coverage.json
playwright-report/
test-results/
scratch/
docs/codebase_dump.md
```

---

### ধাপ ২: ডুপ্লিকেট ফাইল মুছো ও মার্জ করো (মাঝারি ঝুঁকি)

#### [DELETE] ডুপ্লিকেট স্টাব ফাইল
- `backend/brain/swarm_orchestrator.py` → `backend/core/swarm_orchestrator.py` রাখো
- `evolution/evolution_engine.py` → `backend/core/evolution_engine.py` রাখো
- `backend/monitoring/cost_auditor.py` → `backend/tools/cost_auditor.py` রাখো
- `backend/tools/cloud_sandbox_orchestrator.py` → `backend/core/cloud_sandbox_orchestrator.py` রাখো
- `backend/tools/task_router.py` → `backend/core/task_router.py` রাখো
- `backend/core/docker-compose.yml` → রুটেরটি রাখো
- `scripts/code_smell_detector.py` → `backend/tools/code_smell_detector.py` রাখো
- `scripts/fuzz_sandbox.py` → `backend/tools/fuzz_sandbox.py` রাখো

#### [MERGE] github_agent.py
`backend/services/github_agent.py` ও `backend/tools/github_agent.py` — উভয়ের সেরা অংশ একত্র করে `backend/tools/github_agent.py` রাখো।

---

### ধাপ ৩: ফাইল সঠিক জায়গায় সরাও (মাঝারি ঝুঁকি)

#### রুট থেকে সরাও:
- `create_python_service.py` → `scripts/`
- `create_render_service.py` → `scripts/`
- `patch_render.py` → `scripts/`
- `update_render_env.py` → `scripts/`
- `setup_kms.sh` → `scripts/`
- `security-scan.yml` → `.github/workflows/`
- `generate_push_summary.py` (রুট) → মুছো (scripts/-এ আছে)
- `update_render.py` (রুট) → মুছো (scripts/-এ আছে)
- `agent_rules.json` → `config/`
- সব ADR/DFD/SEQ/THREAT markdown → `docs/` উপযুক্ত ফোল্ডারে

#### Backend থেকে সরাও:
- `backend/adaptive_engine/test_platform_learner.py` → `backend/tests/adaptive_engine/`
- `backend/tools/backend_tests.yml` → `.github/workflows/`
- `backend/tools/test_3d_model_generator.py` → `backend/tests/tools/`
- `backend/tools/test_browser_agent.py` → `backend/tests/tools/`
- `backend/tools/test_cloud_sandbox_orchestrator.py` → `backend/tests/tools/`
- `backend/tools/test_freebuff_client.py` → `backend/tests/tools/`
- `backend/tools/test_local_code_executor.py` → `backend/tests/tools/`
- `backend/run_roundtrip_tests.py` → `scripts/`

---

### ধাপ ৪: backend/core/ পুনর্গঠন (উচ্চ ঝুঁকি, পরে করো)

> [!WARNING]
> এই ধাপ সবার শেষে করো। প্রতিটি সাব-ধাপে pytest রান করো।

#### [NEW] উপ-ডিরেক্টরি তৈরি:
- `backend/core/security/`
- `backend/core/messaging/`
- `backend/core/cache/`
- `backend/core/health/`

#### ফাইল গ্রুপিং (import redirect রেখে):
প্রতিটি সরানো ফাইলের পুরনো জায়গায় একটি thin wrapper রাখো:
```python
# backend/core/auth_middleware.py (পুরনো জায়গা)
# এটি backward compatibility এর জন্য redirect করে
from core.security.auth_middleware import *  # noqa: F401, F403
```

---

## যাচাইকরণ পরিকল্পনা (Verification Plan)

### স্বয়ংক্রিয় টেস্ট:
```bash
# প্রতিটি ধাপের পর রান করো:
cd backend && poetry run pytest tests/ -x --tb=short -q
poetry run ruff check .
poetry run mypy . --ignore-missing-imports
```

### ম্যানুয়াল যাচাই:
1. Backend সার্ভার স্টার্ট হয়: `pnpm backend:dev`
2. `/health` endpoint কাজ করে
3. Frontend connect করতে পারে
4. CI workflow পাস হয়

---

## অগ্রাধিকার ক্রম (Priority Order)

| অগ্রাধিকার | কাজ | ঝুঁকি | প্রভাব |
|---|---|---|---|
| 🔴 ১ম | বাইনারি ও লগ ফাইল মুছো | শূন্য | রিপো সাইজ কমবে ~35MB |
| 🟠 ২য় | `.gitignore` আপডেট | শূন্য | ভবিষ্যৎ পরিষ্কার রাখবে |
| 🟡 ৩য় | স্পষ্ট ডুপ্লিকেট স্টাব মুছো | কম | কোড পরিষ্কার |
| 🟢 ৪র্থ | রুট স্ক্রিপ্ট সরাও | কম | সংগঠন উন্নত |
| 🔵 ৫ম | Test ফাইল সঠিক জায়গায় সরাও | মাঝারি | টেস্ট কাঠামো পরিষ্কার |
| ⚪ ৬ষ্ঠ | `backend/core/` পুনর্গঠন | উচ্চ | দীর্ঘমেয়াদী রক্ষণাবেক্ষণ |
