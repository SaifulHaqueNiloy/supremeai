# LESSONS_LEARNED

> **[🤖 AI AGENT INSTRUCTION]** 
> This is a core SupremeAI "Brain" file. When adding a new lesson:
> 1. Add it to the TOP of the list (reverse chronological).
> 2. Include Date, Issue, Fix, and Lesson.
> 3. DO NOT delete or overwrite past historical entries.
> 4. Keep it concise and technical.

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
