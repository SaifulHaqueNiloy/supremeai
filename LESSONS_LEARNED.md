# LESSONS_LEARNED

> **[🤖 AI AGENT INSTRUCTION]** 
> This is a core SupremeAI "Brain" file. When adding a new lesson:
> 1. Add it to the TOP of the list (reverse chronological).
> 2. Include Date, Issue, Fix, and Lesson.
> 3. DO NOT delete or overwrite past historical entries.
> 4. Keep it concise and technical.

## 2026-08-18 — 🐛 PyJWT Migration: `JWTError` → `PyJWTError` (Systemic Import Break)

- **সমস্যা:** python-jose → PyJWT মাইগ্রেশনের সময় `from jwt.exceptions import JWTError` লেখা
  হয়েছে, কিন্তু **PyJWT 2.13-এ `JWTError` alias নেই — base exception-এর নাম `PyJWTError`**
  (JWTError alias 2.10-এ রিমুভ)। ফলে `api.dependencies` import-ই ব্যর্থ — ওই মডিউল থেকে
  40+ route import করে, তাই পুরো রাউটার সাবসিস্টেম লোড হতো না। `auth.py`/`sso.py`/
  `sso_integrator.py`-তে `try/except ImportError: jwt = None` fallback থাকায় সাইলেন্টভাবে
  PyJWT নিষ্ক্রিয় হয়ে যাচ্ছিল (সবচেয়ে বিপজ্জনক — error না দেখিয়ে feature disable)।
- **ফিক্স:** ৬টি ফাইলে সব `JWTError` → `PyJWTError` (import + `except` clause +
  fallback assignment): `api/dependencies.py`, `api/routes/auth.py`, `api/routes/sso.py`,
  `core/security/auth_middleware.py`, `tools/sso_integrator.py`, `tests/test_auth_middleware.py`।
  `py_compile` + `TestApiDeps` + `test_invalid_jwt_token` (PyJWTError side-effect) pass।
- **লেসন:** (১) PyJWT-এ catch-all exception class-এর নাম **`PyJWTError`** — পুরোনো jose-র
  `JWTError` 2.10+ থেকে নেই। (২) `try/except ImportError` fallback import failure-কে
  সাইলেন্ট করে — ভুল import নাম থাকলে module নীরবে নিষ্ক্রিয় হয়; import failure সবসময়
  loud হওয়া উচিত (test বাধ্যতামূলক)। (৩) Shared working tree-তে একাধিক agent কাজ করলে
  `git status`/`git diff HEAD` দিয়ে কোন পরিবর্তন কার তা চেক করে এগোতে হবে।


- **সমস্যা:** `.github/workflows/supreme-core-ci.yml`-এ `dorny/paths-filter` action-এ `filters:` এর সাথে `|` (pipe multiline scalar) বাদ পড়ায় GitHub Actions parser `(Line: 100, Col: 13): A mapping was not expected` এরর দিয়ে সম্পূর্ণ workflow ব্লক করে দিচ্ছিল।
- **ফিক্স:** `with.filters: |` যোগ করে মাল্টিলাইন স্ট্রিং স্কেলার হিসেবে ডিফাইন করা হয়েছে। সমস্ত `.github/workflows/*.yml` ফাইলের `with:` ব্লক স্ক্যান করে কনফার্ম করা হয়েছে যাতে আর কোনো নেস্টেড ম্যাপিং অবজেক্ট না থাকে।
- **লেসন:** GitHub Actions action inputs শুধুমাত্র scalar (string/number/boolean) অ্যাকসেপ্ট করে; `paths-filter`-এর ফিল্টার স্পেসিফিকেশন অবশ্যই `filters: |` স্ট্রিং ফরম্যাটে পাস করতে হবে।

## 2026-08-18 — 📋 Feature Feasibility Audit: 16 Features Assessed

- **সমস্যা:** প্রজেক্টের প্রস্তাবিত সকল ফিচারের (plan docs + code + deploy config) পূর্ণ প্রজেক্টবিশ্বীয় ভেরিফাইকেশন ছিল না। কিছু ফিচার তত্ত্বাবদ্ধ কিন্তু $0 ফ্রি-টিয়ার ও সার্ভারলেস সীমাবদ্ধতায় টেকনিক্যালি অসম্ভব। কিছু "FIXED" দাবি আছে কিন্তু কোডে এখনও খুলে।
- **ফিক্স:** `docs/audit_reports/FEATURE_FEASIBILITY_AND_VIABILITY_AUDIT.md`-এ 16টি ফিচারের পূর্ণ অডিট — Viable (10), Non-Viable/Rejected (7), Conditionally Viable/Blocked (5)। কোড-লেভেল প্রমাণ, ডেপ্লয় অ্যার্কি (`render.yaml`), ও `codebase_issues_report.md`-এর ভেরিফাইড খোলা ইস্যুগুলোর ভিত্তিতে সিদ্ধান্ত নেওয়া হয়েছে।
- **লেসন:** (১) থিওরিটিক্যাল ML ট্রেনিং ফিচার (EWC, FGSM, P2P Federated Learning) সর্বদা $0 ফ্রি-টিয়ার পরিবেশে অসম্ভব — Vector Memory (pgvector/mem0/Graphiti) পিভর্ট করুন। (২) যেকোনো "FIXED"/"Done" দাবি কোড-লেভেল ভেরিফিকেশন ছাড়া বিশ্বস্ত করা যায় না। (৩) 6 সংযুক্ত রেপো তৈরি করলে CI path-filters, pnpm workspace, shared types ভাঙে — মনোরেখা মেনে থাকা (monorepo) ভাগ্য রাখুন। (৪) স্ক্র্যাপার সার্ভিসের জন্য HF Spaces (PRO-only) ও Koyeb (paid-only) ব্যবহার করা যায় না — Render `env: docker` হওয়াই সঠিক পথ।

## 2026-08-18 — 🔴 Tier 0 Confidence Gate: Consolidation Over Duplication

- **সমস্যা:** Needle 2 প্ল্যানটি 4রা স্ট্যান্ডঅ্যালোন `CloudConfidenceGate` ক্লাস প্রস্তাব করে, যাকে `AdvancedModelRouter` + `LatencyAwareWeightedRouter` + `PerformanceOptimizer`-এর সাথে ডুপ্লিকেট। একই routing logic তিন জায়গায় — রক্ষণাবেক্ষণযোগ্য নয়। কাল্পনিক 0.85 threshold কোনো ক্যালিব্রেশন ছাড়া।
- **ফিক্স:** `route_with_confidence()` পদ্ধতিটি `AdvancedModelRouter`-এ যুক্ত করে `analyze_prompt_complexity()`-এর `overall` স্কোরকে কনফিডেন্স ইনপুট হিসেবে পুনরায় ব্যবহার করা হয়েছে। Tier0Dispatcher-এর 4টি প্যাটার্ন (pypi_search, list_files, regex_format, schema_lookup) pure-Python stdlib-এ ভিত্তি করে — কোনো LLM কল নেই। LLMGateway.acompletion()-এ semantic cache-check এবং cost-guard-এর মধ্যবর্তীতে hook সন্নিবেশ করে, litellm কল একদম বাদ যায়।
- **লেসন:** Needle 2-এর "confidence score" কনসেপ্টটি আগে থেকেই `analyze_prompt_complexity()`-এ আছে — নতুন ক্লাস না বানিয়ে বিদ্যমান স্কোরকে কালিয়ান্ট ব্যবহার করা উচিত। Hash-vectorize fallback (pure Python feature hashing) 384-ডাইমেনশনাল embedding দেয় কিন্তু sentence-transformers না থাকলে সিমিলারিটি স্কোর 0-0.22 পর্যন্ত খুব কম হয় — মাল্টি-নিডেল cross-score-এর থ্রেশহোল্ড আপেক্ষিক (needle_avg * 0.3) হওয়া দরকার। স্কিমা validation-এর জন্য BaseSkill দুই রকম import path আছে (`core.skills.base` এবং `core.base`) — দুটোতেরাই `parameters` আর `validate_args()` যোগ করা প্রয়োগ। SQLite `ON CONFLICT(file_path)`-এ একই `file_path` দিয়ে store করলে overwrite হয় — টেস্টে আলাদা `file_path` ব্যবহার করতে হবে।

## 2026-08-18 — 🐛 Pre-existing YAML Indentation Bug in maintenance_pipeline.yml (cost-guard-defcon job)

- **সমস্যা:** main-এ merge-এর পর GitHub Actions RED — Core CI-র ৩টি job (Frontend pnpm install, Render backend env check, Infisical vault check) + Monorepo Type Sync fail করছিল। Root causes: (১) `pnpm-lock.yaml` root importer-এ ৭টি stale dependency (`cross-env`, `ioredis`, `@types/ioredis`, `@types/node`, `@webcontainer/api`, `dotenv`, `rollup`) package.json-এ না থাকলেও lockfile-এ আটকে ছিল → `ERR_PNPM_OUTDATED_LOCKFILE`। (২) আসল Render backend (`supremeai-backend-docker` = `srv-da07ogmgekts739amqa0`) এ মাত্র 26/99 tracked keys — critical `SUPREMEAI_ADMIN_PASSWORD_HASH` ও `INFISICAL_TOKEN` missing; workflow-র hardcoded fallback ID (`srv-d9d3n58js32c738n79k0`) 404। (৩) Infisical Universal Auth 401 — rotated CLIENT_ID/SECRET Infisical-এ create হয়নি + vault-এ `INFISICAL_CLIENT_SECRET` key-ই ছিল না। (৪) `generate_types.py`-তে `filename.relative_to(Path.cwd())` — CI-র `working-directory: backend`-এ output path `cwd`-র subpath না → ValueError; আর generated ফাইলের header-এ `// Generated: <timestamp>` ছিল → checksum সবসময় drift দেখাত।
- **ফিক্স:** (১) `pnpm install --lockfile-only` → lockfile resync। (২) Render API (PUT /services/{id}/env-vars/{key}) দিয়ে ২টি critical key যোগ + workflow-র ৮টি dead fallback ID-কে সঠিক ID (`srv-da07ogmgekts739amqa0`) দিয়ে replace। (৩) Infisical API (POST /v3/secrets/raw) দিয়ে vault-এ `INFISICAL_CLIENT_SECRET` যোগ + `verify_infisical_env.py`-এ Universal Auth fail হলে `INFISICAL_TOKEN` fallback। (৪) `relative_to(_REPO_ROOT)` + ৪ জায়গায় timestamp লাইন রিমুভ (deterministic) + UTF-8 reconfigure।
- **লেসন:** (১) Render/env drift check-এ GitHub secret-এর উপর blind ভরসা না — live API দিয়ে service ID/env var key verify করতে হবে; fallback-এ dead ID রেখে দিলে misleading error পাই। (২) PowerShell দিয়ে YAML/UTF-8 file replace নিষিদ্ধ (BOM + CRLF + mojibake) — Python `pathlib` দিয়ে replace। (৩) Generated ফাইলে কখনো timestamp header রাখা যাবে না — determinism ভাঙে। (৪) Secrets rotation শুধু value generate করলে হয় না — Infisical-এ machine identity আসলেই create/register করতে হয়, নাহলে 401।
