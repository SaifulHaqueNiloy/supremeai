# LESSONS_LEARNED

> **[🤖 AI AGENT INSTRUCTION]** 
> This is a core SupremeAI "Brain" file. When adding a new lesson:
> 1. Add it to the TOP of the list (reverse chronological).
> 2. Include Date, Issue, Fix, and Lesson.
> 3. DO NOT delete or overwrite past historical entries.
> 4. Keep it concise and technical.

## 2026-08-17 — 🐛 Pre-existing YAML Indentation Bug in maintenance_pipeline.yml (cost-guard-defcon job)

- **সমস্যা:** `maintenance_pipeline.yml`-এর `cost-guard-defcon` job-এর `env:` block-এ সঠিক আছিল 6-space indent, কিন্তু `SUPABASE_DATABASE_URL`/`SUPABASE_DATABASE_URL_POOLER`/`SUPREMEAI_JWT_SECRET` লাইনগুলো 11-space indentation-এ লেখা ছিল → YAML parser error (`expected <block end>, but found '<block mapping start>'`)। GitHub Actions-ও এটি catch করত না কারণ job scheduling-এ ফেইল হয়েছিল।
- **ফিক্স:** 11-space → 6-space indentation ঠিক করা। `yaml.safe_load()` দিয়ে verify করা — VALID।
- **লেসন:** YAML-এর block mapping-এর indentation strict — editor স্বয়ংক্রিয়ভাবে indent করলে even-width সাপোর্ট দেয় না। CI YAML-এর syntax সর্বদা `yaml.safe_load()` দিয়ে pre-validate করতে হবে, বিশেষ করে যখন একটি বড় pre-existing file-এর মিধ্যে edit করা হয়।

## 2026-08-17 — 🔄 CI Workflow Consolidation (11 → 6 workflows)

- **সমস্যা:** ১টি মূল `ci.yml` + ৪টি ডুপ্লিকেট/অভিরুপ workflow ছিল: (1) `auto-fix.yml` — daily 01:30 UTC স্কিডুল + PR trigger, `maintenance_pipeline.yml`-এর `auto-lint-fix` + `ci-failure-smart-summary` জবগুলোর সম্পূর্ণ ডুপ্লিকেট; (2) `cache-janitor.yml` + `workflow-janitor.yml` — আলাদা workflow-এর জায়গে maintenance task হিসেবে maintenance_pipeline-এ যুক্ত করা যায়; (3) `security-audit.yml` + `security-dast.yml` — দুটোটি weekly security scan, একত্র করা যায়।
- **ফিক্স:** এই 5টি workflow ডিলিট করে `maintenance_pipeline.yml`-এ তাদের জবগুলো যুক্ত করা (8টি নতুন জব + 6টি নতুন `workflow_dispatch` input)। `pull_request` trigger যোগ করা — gatekeeper ২৪ঘণ্টার সীমা PR trigger-এ bypass করে (`github.event_name != 'schedule'`)। `promotion/staging` PR-এর জন্য `!startsWith(github.head_ref, 'promotion/staging')` গার্ড যোগ করা।
- **লেসন:** Multiple scheduled workflows একসাথে চালু হলে GitHub Actions free tier minutes ডুপ্লিকেট হয়। Consolidated workflow-এর `if` conditions-এ `github.event_name` check অপরিহার্য — gatekeeper `needs:` dependency only makes sense on `schedule` triggers, PR trigger-এ সরাসরি run করতে হয়।

## 2026-08-17 — 🚨 Dead URL: supremeai-admin.onrender.com is SUSPENDED

- **সমস্যা:** `supremeai-admin.onrender.com` (Admin Backend Render সার্ভিস) স্বামী কর্তৃ SUSPENDED — CORS headers রিটার্ন করে না, কোনো API কল 403 দেয়। 8টি অ্যাক্টিভ ফাইলে 36টি রেফারেন্স ছিল: vite.config.ts, api.test.ts, origin_validator.py, Cloudflare worker, render.admin.yaml, service_preflight_check.py, .env.example, DEPLOYMENT_CHECKLIST.md, scripts/check_admin_console.js। `api.ts` আগেই `supremeai-backend-docker.onrender.com`-এ আপডেট করে ছিল (অথরাইজ্ড), কিন্তু vite.config.ts ও test assertions পুরনো URL ব্যবহার করছিল → test failure + dev proxy 403।
- **ফিক্স:** সব অ্যাক্টিভ ফাইলে `supremeai-admin.onrender.com` → `supremeai-backend-docker.onrender.com` রিপ্লেস। `_archive/` ও `docs/`-এর রেফারেন্সগুলো ডকুমেন্টেশন-ওয়েজি রাখা (historical reference)।
- **লেসন:** Production URL পরিবর্তন/সাস্পেনশন হলে সক্রিয় কোড-এ সব রেফারেন্স আপডেট করতে হবে — environment variable, CORS allowlist, health check URLs, test assertions, deployment configs. `api.ts`-এর default আগেই আপডেট করা থাকায় সেটি source of truth হিসেবে ব্যবহার করা যায়।

## 2026-08-17 — ⚠️ Initial Assumption Error: Storybook and Electron are NOT dead code

- **সমস্যা:** প্রাথমিক বিশ্লেষণে `frontend/package.json`-এর Storybook এবং Electron depsকে "dead" বলে ধরা হয়েছিল — কিন্তু `.storybook/` config directory, 3টি `.stories.tsx` ফাইল, `eslint-plugin-storybook` eslint config, এবং Electron `main.js` + `preload.cjs` সবই ফাইলে বিদ্যমান ছিল। CI workflow থেকে রেফারেন্স না থাকাটা মানে হয়নি যে ডেভটা ডেড।
- **ফিক্স:** স্ক্রিপ্টগুলো রান করতে ব্যবহার করা হয় না, কিন্তু রিমুভ করা হয়নি — ভবিষ্যৎতে রিঅনডার আর্টিফ্যাক্টের জন্য বা লোকালি dev হিসেবে দরকারী হতে পারে। শুধুমাত্র স্পষ্টভাবে মার্কি আর্কাইভড রিপোজিটরিতে রেফারেন্স থাকলে রিমুভ করা উচিত।
- **লেসন:** কোনো ডিপেন্ডেন্সি/টুল রিমুভ করার সিদ্ধান্ত নেওয়ার আগে সর্বদা কোডবেসে তার কনফিগারেশন ফাইল, স্ক্রিপ্ট, এবং রেফারেন্সগুলো স্ক্যান করতে হবে। `grep` + `glob` ব্যবহার করে সঠিকভাবে যাচাই করুন।

## 2026-08-17 — 🧠 Scalable Agent Orchestration: LiteLLM, PydanticAI & MCP

- **সমস্যা:** SupremeAI-তে একাধিক LLM প্রোভাইডার, রেট-লিমিটিং, ফলব্যাক, এবং রিয়েল-ওয়ার্ল্ড টুলের (MCP) জন্য কোনো স্কেলেবল বা ইউনিফাইড অর্কেস্ট্রেশন আর্কিটেকচার ছিল না। ডিপেন্ডেন্সি কনফ্লিক্টের কারণে `langfuse` ইন্সটলেশন ফেইল হচ্ছিল।
- **ফিক্স:** `LiteLLMGateway`-এ LiteLLM-এর built-in Redis cache এবং Langfuse observability যুক্ত করা হয়েছে। `BasePydanticAgent` তৈরি করে PydanticAI-এর মাধ্যমে স্ট্রাকচারড আউটপুট এবং `MCPRegistryClient`-এর মাধ্যমে ডাইনামিক টুল ইন্টিগ্রেশন সম্পন্ন করা হয়েছে। `poetry` দিয়ে `langfuse`, `pydantic-ai`, `opentelemetry` এর ভার্সন কনফ্লিক্ট ঠিক করে ইন্সটল করা হয়েছে।
- **লেসন:** একাধিক LLM এবং টুল ইন্টিগ্রেট করতে LiteLLM এবং PydanticAI-এর কম্বিনেশন ব্যবহার করলে প্রচুর কাস্টম কোড এবং মেইনটেইনেন্স কমানো যায়। Langfuse-এর মতো observability টুল দিয়ে পুরো সিস্টেমের cost এবং latency ট্র্যাক করাটা প্রোডাকশন-লেভেলের এজেন্টদের জন্য অত্যন্ত জরুরি।

## 2026-08-17 — ✅ Thin Client + Brand Exclusivity: VS Code Extension থেকে সরাসরি থার্ড-পার্টি LLM কল সম্পূর্ণ রিমুভ

- **সমস্যা:** `SupremeAIService.tryFreeModelFallback`-এ সরাসরি OpenRouter কল (`openrouter.ai`) + user-supplied API key ছিল; লিগ্যাসি `AIService.ts` সরাসরি `openai` SDK + `aiApiKey`/`aiModel` user-config পড়ছিল → Thin Client ও Brand Exclusivity নীতি লঙ্ঘন + `TS2307` compile error।
- **ফিক্স:**
  - `tryFreeModelFallback`: OpenRouter/ইউজার key বাদ; অফলাইন ফলব্যাক = শুধু লোকাল Ollama। বহিরাগত provider কনফিগ হলে স্পষ্ট error throw।
  - `AIService.ts`: `openai` import + ইউজার key বাদ; সব LLM এখন `getSupremeAIService().sendChatMessage()`-এর মাধ্যমে ব্যাকএন্ডে রাউট (offline static fallback সহ)। `CodeGenerationService` / `CodeReviewService` / `EnhancedAIService` (extends AIService) অক্ষত।
  - `TelemetryTracker.ts`: মিসিং `fast-levenshtein` → inline Levenshtein; dep প্যাকেজ থেকে `openai`/`fast-levenshtein` বাদ।
- **লেসন:** thin-client এক্সটেনশন কখনোই সরাসরি LLM provider-এ কল করবে না; key মানেই ব্যাকএন্ড (Render) এনভায়রনমেন্টে। ক্লায়েন্ট-সাইডে শুধু SupremeAI ব্র্যান্ড + ব্যাকএন্ড রাউটিং, আর লোকাল Ollama-ই একমাত্র অফলাইন ফলব্যাক।

## 2026-08-17 — 🚨 .gitignore *.txt Rule Masked requirements.txt in Scraper Microservice

- **সমস্যা:** GitHub Actions CI-তে `🕷️ Scraper Service Build` ফেইল করছিল: `ERROR: Could not open requirements file: [Errno 2] No such file or directory: 'requirements.txt'`.
- **উৎস:** `.gitignore`-এ `*.txt` গ্লোবাল প্যাটার্ন থাকায় `backend/services/scraper/requirements.txt` গিট ট্র্যাক করছিল না (ignored ছিল), ফলে রিমোট রিপোজিটরিতে ফাইলটি পুশ হয়নি।
- **ফিক্স:** `.gitignore`-এ `!requirements.txt`, `!**/requirements.txt`, `!**/requirements*.txt` এক্সক্লুশন রুল যোগ করা হয়েছে এবং Scraper সার্ভিসের জন্য `Dockerfile` তৈরি করে গিটহাবে পুশ করা হয়েছে।
- **লেসন:** `.gitignore`-এ ব্রড প্যাটার্ন যেমন `*.txt` ব্যবহারের সময় অবশ্যই প্রয়োজনীয় কনফিগারেশন ও ডিপেন্ডেন্সি ফাইলগুলোর জন্য এক্সপ্লিসিট হোয়াইটলিস্ট/নেগেশন (`!requirements.txt`) নিশ্চিত করতে হবে।
