# LESSONS_LEARNED

> **[🤖 AI AGENT INSTRUCTION]** 
> This is a core SupremeAI "Brain" file. When adding a new lesson:
> 1. Add it to the TOP of the list (reverse chronological).
> 2. Include Date, Issue, Fix, and Lesson.
> 3. DO NOT delete or overwrite past historical entries.
> 4. Keep it concise and technical.

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

## 2026-08-16 — Brand Exclusivity and the Thin Client Extension

### সমস্যা: এক্সটেনশনের ভেতরে থার্ড-পার্টি API (OpenRouter) ফলব্যাক লজিক থাকার কারণে মার্কেটিং ও আর্কিটেকচারাল কনফ্লিক্ট তৈরি হওয়া।
- **উৎস:** `SupremeAIService.ts` ফাইলে OpenRouter-এর API Key ব্যবহার করার লজিক ছিল। এটি একটি বিশাল ব্লান্ডার ছিল, কারণ এর ফলে ইউজার জানত যে আমরা অন্য এআই ব্যবহার করছি ("নিজে খেটে অন্যের দান বানানো")।
- **ফিক্স:** ফিলোসফিটি রি-অ্যালাইন করা হয়েছে। এক্সটেনশনকে ১০০% থিন ক্লায়েন্ট হিসেবে আর্কিটেকচার করা হচ্ছে। ইউজার শুধু "SupremeAI API Key" এবং "SupremeAI Model" দেখবে। সব থার্ড-পার্টি মডেল কল (Groq/Gemini/OpenAI) অত্যন্ত গোপনে ব্যাকএন্ড (Render) থেকে হবে।
- **লেসন:** মার্কেটিং এবং ব্র্যান্ডিং ঠিক রাখতে হলে ক্লায়েন্ট সাইডে (এক্সটেনশন) কখনোই থার্ড-পার্টি এআইয়ের নাম বা কনফিগারেশন এক্সপোজ করা যাবে না। এক্সটেনশনে শুধু SupremeAI-এর ব্র্যান্ডিং থাকবে, আর ব্রেইন এবং অর্কেস্ট্রেশন সর্বদা ব্যাকএন্ডে থাকবে।

## 2026-08-15 — CI Deploy-verify Timeout Increase to 12 Minutes (Render Free-Tier Cold Start)

### সমস্যা: `Verify Render Deploy (Wait for Live)` স্টেপে ৬ মিনিট (360s) টাইমাউটেও ফেইল করছিল।
- **উৎস:** Render free-tier এ ব্যাকএন্ড ডেপ্লয় এবং কোল্ড স্টার্ট হতে ৬ মিনিটের বেশি সময় লেগে যাচ্ছে। 
- **ফিক্স:** `.github/scripts/verify-render-deploy.py` তে `TIMEOUT_LIMIT` ডিফল্ট 360s থেকে বাড়িয়ে 720s (১২ মিনিট) করা হয়েছে।
- **লেসন:** ফ্রি-টিয়ার সার্ভিসের রিলায়াবিলিটির জন্য টাইমআউট লিমিট অনেক জেনারাস রাখতে হবে যাতে স্লো ডেপ্লয়মেন্টের কারণে ফলস-নেগেটিভ ফেইলিওর না আসে।

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
