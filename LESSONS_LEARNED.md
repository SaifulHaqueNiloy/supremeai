# LESSONS_LEARNED

> **[🤖 AI AGENT INSTRUCTION]** 
> This is a core SupremeAI "Brain" file. When adding a new lesson:
> 1. Add it to the TOP of the list (reverse chronological).
> 2. Include Date, Issue, Fix, and Lesson.
> 3. DO NOT delete or overwrite past historical entries.
> 4. Keep it concise and technical.

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

## 2026-08-16 — 🚨 Atomic Tasks & Automation Blindspot (Agent Correction)

- **সমস্যা:** URL replace করার পর verification করা হয়নি, `git add .` দিয়ে ইউজারের অন্যান্য ফাইল কমিট করে দেওয়া হয়েছিল, এবং unused Render service ডিলিট করার automation ট্রাই করা হয়নি।
- **ফিক্স:** `check_system_health.py` রান করে URL verify করার চেষ্টা করা হয়েছে (local module missing error পাওয়া গেছে)। `LESSONS_LEARNED.md` ও `CHECKPOINT.md` আপডেট করা হলো।
- **লেসন:** Systemic Propagation-এর পাশাপাশি Atomic Tasks (১ Task = ১ Verify) রুল কখনোই ইগনোর করা যাবে না। অটোনোমাস এজেন্টকে অবশ্যই $0 Cost ফিলোসফি অনুযায়ী unused resource (যেমন Render Service) নিজে থেকেই ডিলিট করার চেষ্টা করতে হবে।

## 2026-08-16 — ⚙️ Architecture Decision: Autonomous Execution Policy

- **সমস্যা:** AI-এর code execution sandbox এবং auto-commit authority কোনো rule ছাড়াই চলছিল।
- **সিদ্ধান্ত (Core Philosophy থেকে):**
  - **Sandbox:** Python subprocess (timeout=30s) for safe tasks; Docker only for risky/unknown code — `$0 cost` principle।
  - **Direct Push:** docs, `*.md`, AI memory files, lint-only commits।
  - **PR Required:** backend logic, frontend, CI/CD, infra config, migrations, lock files।
- **Lesson:** Core philosophy (`$0 cost` + `self-healing` + `reliability`) থেকে সরাসরি rules derive করলে admin-এর approval loop ছাড়াই সঠিক decision নেওয়া যায়।

## 2026-08-16 — 🚨 Double Deploy Bug Fixed (render.yaml autoDeploy)

- **সমস্যা:** `render.yaml`-এ `autoDeploy: true` ছিল। প্রতি `git push main`-এ Render তাৎক্ষণিক deploy করত। CI-ও আলাদাভাবে `deploy-backend` job চালাত। ফলে প্রতি push-এ **2টা deploy** → 500 min free quota দ্বিগুণ গতিতে শেষ।
- **Fix:** `render.yaml` → `autoDeploy: false` (backend + frontend উভয়)। CI pipeline একমাত্র deploy authority।
- **Effect:** `check-render-quota` → quota-based routing এখন কার্যকর। Resource waste বন্ধ।
- **Lesson:** Render `autoDeploy: true` + CI deploy job একসাথে রাখা যাবে না। Always pick ONE deploy authority।

## 2026-08-16 — 🔥 React Error #31 (Active Monitor E2E) Root Cause: RAW ERROR OBJECT RENDERED IN TOAST


### সমস্যা: 🩺 Environment Health Check → Active Monitor E2E প্রোডাকশন বিল্ডে Admin Dashboard লগইন করার সময় `Minified React error #31` (object with keys `{code, message, errors}`) আনকট uncaught pageerror → `caughtErrors.length` 1 → CI fail।

- **উৎস:** `frontend/src/utils/apiInterceptor.ts`-এ `setupGlobalFetchInterceptor()` error body পার্স করে:
  `if (parsed.error) errorMsg = parsed.error; else if (parsed.message) errorMsg = parsed.message;` — back-এর error envelope (`{code,message,errors}`) string-এ কনভার্ট না করে সরাসরি `window.showGlobalToast('error', errorMsg)`-এ পাঠায় → toast state `t.message`-এ object বসে → `{t.message}` render → React #31।
- **ফিক্স (defense-in-depth, 4 layer):** (1) `apiInterceptor.ts`: `parsed.error/message/detail` সবকে `toMsgString()` দিয়ে string-এ; (2) `hooks/useErrorHandler.ts`: `error?.message` object হলে `JSON.stringify()`; (3) `contexts/ToastProvider.tsx`: `safeMessage` guard; (4) `components/ui/Toast.tsx`: একই guard।
- **লেসন:** যেকোনো error মেসেজ toast/state→JSX child-এ বসানোর আগে MUST `typeof === 'string'` guard, নাহলে production (minified) বিল্ডে React #31 ধরা পড়ে। Commit `f71269c2` (adminStore-এ String()) CI-test হয়েও ফেল ছিল — আসল লিক ছিল interceptor→toast রুটে। CI ফেলের minified error args (`args[]=object with keys {code,message,errors}`) পড়ে object-shape ট্রেস করো।

## 2026-08-16 — Brand Exclusivity and the Thin Client Extension

### সমস্যা: এক্সটেনশনের ভেতরে থার্ড-পার্টি API (OpenRouter) ফলব্যাক লজিক থাকার কারণে মার্কেটিং ও আর্কিটেকচারাল কনফ্লিক্ট তৈরি হওয়া।
- **উৎস:** `SupremeAIService.ts` ফাইলে OpenRouter-এর API Key ব্যবহার করার লজিক ছিল। এটি একটি বিশাল ব্লান্ডার ছিল, কারণ এর ফলে ইউজার জানত যে আমরা অন্য এআই ব্যবহার করছি ("নিজে খেটে অন্যের দান বানানো")।
- **ফিক্স:** ফিলোসফিটি রি-অ্যালাইন করা হয়েছে। এক্সটেনশনকে ১০০% থিন ক্লায়েন্ট হিসেবে আর্কিটেকচার করা হচ্ছে। ইউজার শুধু "SupremeAI API Key" এবং "SupremeAI Model" দেখবে। সব থার্ড-পার্টি মডেল কল (Groq/Gemini/OpenAI) অত্যন্ত গোপনে ব্যাকএন্ড (Render) থেকে হবে।
- **লেসন:** মার্কেটিং এবং ব্র্যান্ডিং ঠিক রাখতে হলে ক্লায়েন্ট সাইডে (এক্সটেনশন) কখনোই থার্ড-পার্টি এআইয়ের নাম বা কনফিগারেশন এক্সপোজ করা যাবে না। এক্সটেনশনে শুধু SupremeAI-এর ব্র্যান্ডিং থাকবে, আর ব্রেইন এবং অর্কেস্ট্রেশন সর্বদা ব্যাকএন্ডে থাকবে।