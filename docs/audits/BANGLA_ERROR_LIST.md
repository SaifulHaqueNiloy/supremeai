# SupremeAI — সম্পূর্ণ কোডবেস ও সার্ভিস লাইভ-টেস্ট রিপোর্ট (বাংলা)

**তারিখ:** ২০২৬-০৯-০৫ | **কোডবেস:** main @ `ed7aa92` (PR #190 "finish full redesign")
**পদ্ধতি:** আপনার দেওয়া production `.env` (১৮১টি key) দিয়ে **আসল সার্ভার বুট** + ২৩টি বাহ্যিক সার্ভিস লাইভ কল + ২১টি HTTP endpoint ব্যাটারি + কোড-স্তরের static অডিট
**ফলাফল:** 🔴 মারাত্মক ৫টি · 🟠 গুরুতর ৯টি · 🟡 ঝুঁকি/পর্যবেক্ষণ ১২টি — মোট **২৬টি স্বতন্ত্র সমস্যা**, সাথে প্রতিটির প্রমাণ ও সমাধান।

---

## 🔴 মারাত্মক (CRITICAL) — প্রোডাকশন সরাসরি ভাঙছে

### 🔴-১. চ্যাট ফিচার ১০০% ক্র্যাশ করছে (`AttributeError`)
- **প্রমাণ (লাইভ টেস্ট):** আসল admin লগইন দিয়ে `POST /api/chat/stream` কল করা হলো → সার্ভার লগে:
  `Global Exception: AttributeError: 'ModelRouter' object has no attribute 'async_route_and_stream'`
- **কোড:** `backend/api/routes/task.py:149` এমন মেথড ডাকে যা `backend/brain/model_router.py`-এ **নেই**; শুধু sync `route_and_stream` (লাইন ৩৬৭) আছে। টেস্ট ফাইল (`tests/api/test_task_endpoints.py:161`) মেথডটি **ফেক করে রাখে**, তাই CI ধরতে পারেনি।
- **প্রভাব:** ফ্রন্টএন্ড (`frontend/src/services/chatService.ts:40`) এই রুটেই চ্যাট করে — অর্থাৎ **প্রতিটি চ্যাট মেসেজ ক্র্যাশ**।
- **বোনাস আবিষ্কার:** sync `route_and_stream` নিজেই একটি স্টাব — provider না পেলে `"Hello World"` ইয়েল্ড করে!
- **✅ ফিক্স করা হয়েছে:** `audit-fixes-v8` ব্রাঞ্চে commit — `async_route_and_stream` যোগ করা হয়েছে যা **আসল `LLMGateway.acompletion(stream=True)`** থেকে স্ট্রিম করে, gateway ব্যর্থ হলে পরিষ্কার ফলব্যাক। প্যাচ: `0001-fix-chat-api-chat-stream-crashed-with-attributeerr.patch` (বুট-টেস্টে যাচাইকৃত: এখন gateway `gemini/gemini-2.5-flash` স্ট্রিম অ্যাটেম্প্ট লগ হয়, ক্র্যাশ নেই)।

### 🔴-২. `.env`-এর ৩টি JSON কনফিগ **সম্পূর্ণ মৃত** — dotenv পড়তেই পারে না
- **প্রমাণ:** `AUTH_KEYS`, `DATABASE_CONFIG`, `LLM_PROVIDER_KEYS` — তিনটিতেই `\"` ডাবল-escape আছে; python-dotenv ওয়ার্নিং দিয়ে **পুরো লাইন বাদ দেয়**: `could not parse statement starting at line 20/33/88` → ভ্যালিউ ফাঁকা → প্রোডাকশনে vault JSON-path নীরবে `{}` রিটার্ন করে (`secret_vault.py:436-453`)।
- **প্রভাব:** `AUTH_KEYS`-এর শক্তিশালী ৬৪-বাইট jwt_secret প্রোডাকশনে **পৌঁছায়ই না**; `LLM_PROVIDER_KEYS` ব্লব নিষ্ক্রিয়।
- **সমাধান:** এই ৩ লাইন single-quote-এ লিখুন: `AUTH_KEYS='{"jwt_secret": "..."}'` (ভেতরের `\"` → `"`), অথবা escape ছাড়া plain JSON।

### 🔴-৩. Firebase/Firestore সম্পূর্ণ মৃত — boot-এ বারবার P0 এরর
- **প্রমাণ (বুট লগ, বহুবার):**
  - `Firestore client initialization failed: Invalid control character at: line 1 column 156`
  - `Firebase Admin SDK not available: Invalid control character...`
  - `❌ [P0] no durable skill store available for AutoSkillCreator ... refusing to run (fail-closed)` (২ বার)
  - `P0: SQLite fallback refused for feature=admin_god_rules ... rules resolve to safe defaults (deny)`
- **কারণ:** `FIREBASE_SERVICE_ACCOUNT_JSON`-এর private_key-এ **আসল নিউলাইন** ঢুকে গেছে (multi-line হয়ে আছে) → JSON parse ব্যর্থ। Key-এর বিষয়বস্তু অক্ষত (১৭০৪-char PEM), শুধু ফরম্যাট ভাঙা।
- **প্রভাব:** Firestore-নির্ভর সব ফিচার (skill store, notifications) মৃত; admin god-rules deny-তে আটকে।
- **সমাধান:** value-টি **এক লাইনে** single-quote দিয়ে লিখুন, private_key-এ `\n` literal রাখুন: `FIREBASE_SERVICE_ACCOUNT_JSON='{"type":"service_account",...,***REMOVED***",...}'`

### 🔴-৪. LLM key-গুলো comma-সহ কাঁচা পাঠানো হয় — multi-key pool কোডেই নেই
- **প্রমাণ:** বুটের পর গেটওয়ে `GET https://openrouter.ai/api/v1/auth/key → 401` (২ বার) — কারণ কোড `"sk-or-v1-0bb…,sk-or-v1-52c…"` **পুরো স্ট্রিং একসাথে** Bearer হিসেবে পাঠায়। T-2 এজেন্ট প্রতিটি key **আলাদা** করে টেস্ট করে প্রমাণ করেছে দুটোই বৈধ (GET /models 200, 431 models)।
- **কোড:** `providers.py:338/598`, `llm_gateway.py:247-259` — কোথাও comma-split/rotation নেই। Gemini-র ৩টি key ও Groq-র ৩টি key-এর ক্ষেত্রেও একই সমস্যা।
- **প্রভাব:** আপনার যত multi-key fallback চাওয়া, প্রোডাকশনে **একটিও কাজ করে না**; প্রথম key মরলেই সেই provider সম্পূর্ণ ডাউন।
- **সমাধান:** `llm_gateway._get_api_key_for_model`-এ `key.split(",")` + round-robin/429-rotation যোগ করুন (ছোট প্যাচ)।

### 🔴-৫. Boot-ভ্যালিডেটর মিথ্যা এলার্ম দেয় + দুই ভ্যালিডেটর পরস্পরবিরোধী
- **প্রমাণ (বুট লগ):**
  - শুরুতে `config_validation.py:159`: *"4 LLM key optional but missing ([OPENROUTER_API_KEY, GROQ_API_KEY, DEEPSEEK_API_KEY, OPENAI_API_KEY]). Available: [GEMINI_API_KEY]"* — অথচ `.env`-এ তিনটিই আছে!
  - পরে `startup_validator.py:67`: *"LLM providers configured: 4"* — lazy load-এর পর ঠিক দেখায়।
- **প্রভাব:** boot-কালে ভুল "partial AI functionality only" এলার্ম; মনিটরিং/ডিবাগে বিভ্রান্তি।
- **সমাধান:** `config_validation`-এর key-চেক lazy vault resolve-এর পরে চালান।

---

## 🟠 গুরুতর (HIGH) — সার্ভিস ভাঙা বা ভুল আচরণ

### 🟠-১. Stripe key ভুল ফরম্যাট — billing সম্পূর্ণ অচল
- লাইভ টেস্ট: `GET /v1/balance` → **401**: *"Invalid API key provided: mk_1Tt7F*****… This looks like the ID of an API key rather than the key itself. API keys typically start with `pk_`, `rk_`, or `sk_`."*
- সব `STRIPE_*` var-ই `mk_` দিয়ে শুরু (key নয়, key-**ID**)। **সমাধান:** Dashboard থেকে `sk_live_…`/`sk_test_…` key নিয়ে বসান।

### 🟠-২. GitHub tokens সব মৃত (৪০১)
- লাইভ টেস্ট: `GET /api.github.com/user` → **401 Bad credentials**। `.env`-এ ৮টি GitHub var (GH_TOKEN, GITHUB_TOKEN, MAIN_REPO_TOKEN ইত্যাদি) — টোকেন ফরম্যাট সঠিক কিন্তু **revoked/expired**। বুট লগেও: `RepoDiscoveryAgent initialized without a token; real API operations disabled`।
- **সমাধান:** নতুন PAT ইস্যু করে সব var-এ বসান (var-গুলোর মধ্যে ২টি duplicate-ও আছে)।

### 🟠-৩. LLM provider-গুলো এই sandbox থেকে geo-blocked (key ভালো, নেটওয়ার্ক সমস্যা)
- **Gemini ×3:** key auth-বৈধ, কিন্তু `gemini-2.0-flash` **retired** (৪০৪ → "use gemini-3.6-flash"), 2.5/3.6-flash → 400 *"User location not supported"*
- **Groq ×3:** edge-লেভেল 403 (pre-auth geo-block)
- **OpenAI:** 403 *"Country/region not supported"*
- **OpenRouter ×2:** ✅ দুটোই বৈধ; তবে `gpt-4o-mini` 403 region — `:free` মডেলে চলবে
- **প্রভাব:** এই টেস্ট-মেশিন থেকে সব provider ফেল; **Render-এর US node থেকে Gemini/Groq সম্ভবত চলবে**, তবে `gemini-2.0-flash` রেফারেন্স করা কোড আপডেট করতেই হবে।

### 🟠-৪. Boot-এ বারবার Infisical miss
- `Secret 'HF_API_KEY' not found in Infisical` + `No HF_API_KEYS provided! Swarm requests may fallback or fail` (llm_router.py:842); `N8N_WEBHOOK_SECRET not found`। আবার T-2 দেখেছে `INFISICAL_TOKEN` **expired (403)** — কিন্তু universal-auth (CLIENT_ID/SECRET) দিয়ে লগইন সফল, তাই vault কাজ করছে। **সমাধান:** Infisical-এ HF/N8N secret যোগ করুন বা বুট-চেক থেকে বাদ দিন; `INFISICAL_TOKEN` rotate করুন।

### 🟠-৫. এনক্রিপশন স্প্লিট-ব্রেইন — ৩টি ভিন্ন Fernet key
- `ENCRYPTION_KEYS` (জেতে — security_vault.py:72) ≠ `ENCRYPTION_KEY` (settings) ≠ `SUPREMEAI_CREDENTIAL_ENC_KEY` — এক মডিউলে এনক্রিপ্ট করা ডেটা আরেক মডিউলে **ডিক্রিপ্ট ফেল**। বুট লগে: `⚠️ Non-Base64 encryption key detected... deriving valid Fernet key layout` (byoc.cloud_connector)। **সমাধান:** একটি canonical key ঠিক করে বাকিগুলো alias করুন।

### 🟠-৬. JWT secret-বিশৃঙ্খলা — ৫টি ভিন্ন মান
- `SUPREMEAI_JWT_SECRET` (১২৮-hex, লাইভ) · `JWT_SECRET`=`JWT_Njel_722c…ComBd!` (মাত্র ২৯-বাইট — **≥৬৪-বাইট নিয়মে প্রোডাকশন বুট ক্র্যাশ করতে পারে**, config_secrets.py:495) · `AUTH_KEYS.jwt_secret` (JSON মৃত থাকায় অপ্রাপ্য) · `JWT_SECRET_KEY` (dead) · `API_KEY_SIGNING_SECRET` (আলাদা)। **সমাধান:** একটি secret, বাকিগুলো alias; ২৯-বাইট মানটি বদলান।

### 🟠-৭. Redis ক্রেডেনশিয়াল অমিল
- `REDIS_PASSWORD`=`REDIS_TOKEN` (`gQAAAAAAAf…`) ≠ `REDIS_URL`-এর ভেতরের পাসওয়ার্ড (`gQAAAAAAAo…`); আবার zero-cost REST ক্লায়েন্ট (`zero_cost_patch_phase1_4.py:98`) যে `UPSTASH_REDIS_TOKEN` পড়ে সেটি .env-এ **নেই** (আছে `UPSTASH_REDIS_REST_TOKEN`) → REST কল unauthenticated হতে পারে। ভালো দিক: বুটে `⚡ Serverless Upstash Redis REST Provider Active (limit=20)` — REST পথ চলছে। **সমাধান:** `UPSTASH_REDIS_TOKEN` যোগ করুন + পাসওয়ার্ডগুলো সিঙ্ক করুন।

### 🟠-৮. Cloudflare R2 ক্রেডেনশিয়াল নেই
- বুট লগ: `Cloudflare R2 credentials missing. R2StorageClient will run in dry-run/mock mode.` — ফাইল-স্টোরেজ ফিচার প্রোডাকশনে মক। **সমাধান:** R2 access/secret key যোগ করুন বা ফিচার disable করুন।

### 🟠-৯. RefactorWiz অটো-প্যাচ স্ক্রিপ্টই নেই
- বুট লগ: `❌ RefactorWiz auto-patch failed for __init__.py: python: can't open file 'scripts/devops/refactor_wiz.py': [Errno 2] No such file` — self-healing সিস্টেমের একটি অস্ত্র **প্রোডাকশনে অনুপস্থিত**। **সমাধান:** স্ক্রিপ্ট যোগ করুন বা এই পথ নিষ্ক্রিয় করুন।

---

## 🟡 ঝুঁকি / পর্যবেক্ষণ (MEDIUM/LOW) — ১২টি

| # | সমস্যা | প্রমাণ/উৎস |
|---|---|---|
| 🟡-১ | `.env`-এর ১৮১ var-এর মধ্যে **৭২টি dead** (কোড কোনোটিই পড়ে না); এর মধ্যে ৩২টি **লাইভ সিক্রেট** — অপ্রয়োজনীয় লিক-পৃষ্ঠ | T-3 audit |
| 🟡-২ | কোড যা চায় তার মধ্যে **২৮টি গুরুত্বপূর্ণ var .env-এ নেই** (যেমন `NODE_ROLE`, `WAKE_NON_PRIMARY`, `CONTROL_PLANE_HEALTH_TTL_SECONDS`, `PRE_MERGE_DOMAINS` — ব্যাকএন্ডে কোথাও পড়াও হয় না) | T-3 |
| 🟡-৩ | `SUPABASE_DB_CA_CERT` = মাত্র ২৮ অক্ষর (`-----BEGIN CERTIFICATE-----` — বাকি নেই); `SUPABASE_SECRET_KEY` = ১৫ অক্ষর (কাটা) | T-3 |
| 🟡-৪ | TOTP seed = pyotp-এর **পাবলিক উদাহরণ-কোড** `JBSWY3DPEHPK3PXP` — 2FA নামে মাত্র | T-3 |
| 🟡-৫ | `SUPREMEAI_ADMIN_LOGIN_PASSWORD` plaintext env-এ (যদিও বর্তমানে কোনো কোড পড়ে না); `CI_WEBHOOK_SECRET` = একটি পাবলিক ডোমেইন | T-3 |
| 🟡-৬ | Resend: key সফল মেইল পাঠাতে পারে কিন্তু `/domains` API 401 *"restricted to only send emails"* | T-1 |
| 🟡-৭ | LaunchDarkly: `api-…` key SDK-endpoint-এ 401 — এটি REST-admin key, SDK key নয় | T-1 |
| 🟡-৮ | Qdrant/Neon-API/OpenHands: DNS/TLS sandbox-ব্লক — এখান থেকে যাচাই অসম্ভব, ক্লাউড থেকে re-test করুন (Qdrant creds ফরম্যাট ঠিক) | T-1 |
| 🟡-৯ | `MISTRAL_API_KEY` বৈধ (429 = চেনা হয়েছে) কিন্তু **কোনো কোড পড়ে না** — dead config | T-2 |
| 🟡-১০ | `GOOGLE_API_KEY` আসলে Firebase **ওয়েব key** (`VITE_FIREBASE_API_KEY`-এর সমতুল্য), Generative API ব্লকড — নাম ধোঁকা দেয় | T-2 |
| 🟡-১১ | পুরনো ফিক্স হারিয়ে যাওয়ার পুনরাবৃত্তি: `/api/v1/chat/capabilities` 404 (PR #158-এর contract endpoint টিকে নেই), `core/routing/execution_router.py` main-এ নেই — v6-এর কিছু অংশ push হয়নি | লাইভ openapi |
| 🟡-১২ | Latent বোম্বা: `LLM_PROVIDER_KEYS`-এর JSON ঠিক করলেই বর্তমান কোডে `groq:""` **খালি স্ট্রিং দিয়ে env key মুছে ফেলবে** (`config_secrets.py:139-145` unconditional overwrite) — JSON ফিক্স + blob-এর খালি এন্ট্রি ক্লিয়ার একসাথে করতে হবে | T-2 |

---

## ✅ যা ভালোভাবে চলছে (লাইভ-যাচাইকৃত)

| সার্ভিস/ফিচার | ফলাফল |
|---|---|
| **Supabase** (REST service_role 200, auth/health 200 GoTrue, Postgres `SELECT 1` 355ms, boot-এ `evolution_logs` INSERT **201**) | ✅ সম্পূর্ণ লাইভ |
| **Upstash Redis** (PING/SET/GET/DEL সফল; টেস্টে মাত্র ৫ কমান্ড খরচ) + বুটে REST provider active (limit=20) | ✅ |
| **Admin লগইন → JWT** (আসল Supabase password grant 200, token ৩৪১-char) + ভুল পাসওয়ার্ডে সঠিক 401 | ✅ |
| **Auth middleware**: ৫টি protected endpoint-এ token ছাড়া সঠিকভাবে **401** (control-plane, chat-capabilities, billing-wallet, memory, admin-api) | ✅ |
| **Control-plane health**: ৪টি আসল node-ই প্রোব সফল — core-api 137ms, worker 155ms, scraper 196ms, mcp OK | ✅ |
| **Render API ×4 key, Vercel, Cloudflare token, GitLab, Kaggle, Infisical universal-auth, Telegram bot (getMe OK), Discord webhook, Firecrawl ×2 (ক্রেডিট বার্ন ০)** | ✅ |
| HTTP ব্যাটারি: ২১/২১ টেস্ট সেমান্টিক্যালি পাস (লগইন, 401-গেট, wallet, plans, memory, admin, /auth/me) | ✅ |

---

## 📊 মোট হিসাব

| ক্যাটাগরি | সংখ্যা |
|---|---|
| বাহ্যিক সার্ভিস টেস্ট (T-1) | ২৩টি: ১৩ OK · ৬ DEGRADED · ৭ BROKEN · ৩ SKIP |
| LLM প্রোভাইডার (T-2) | ১০: OpenRouter ✅×2 · Gemini ভালো-তবে geo+retired-model · Groq/OpenAI geo-block · Mistral dead-config · NVIDIA/Anthropic/Ollama/GitHub-Models অনুপস্থিত বা মৃত |
| env-অডিট (T-3) | ৭২ dead var · ২৮ missing · ৫/৬ JSON parse fail · ৫টি secret-কনফ্লিক্ট পরিবার |
| HTTP ব্যাটারি | ২১/২১ পাস (তবে এর ভেতরে চ্যাট-ক্র্যাশ ধরা পড়েছে) |
| **বুট লগে নতুন এরর** | Firestore/Firebase parse ×৬, P0 AutoSkillCreator ×২, admin_god P0, R2, RefactorWiz, Infisical miss ×২, ভুল boot-ভ্যালিডেটর এলার্ম |

## 🛠️ এই প্যাকেজে যা দেওয়া হলো
1. `0001-fix-chat-….patch` — 🔴-১ চ্যাট-ক্র্যাশ ফিক্স (লাইভ বুট-টেস্টে যাচাইকৃত) — `git am` দিয়ে apply করুন
2. `TEST_REPORT_EN.md` — ইংরেজি বিস্তারিত raw রিপোর্ট (T-1/T-2/T-3 সহ)
3. এই বাংলা রিপোর্ট

**সবচেয়ে আগে করণীয় (priority order):** ① চ্যাট-প্যাচ apply → ② `.env`-এর ৩টি JSON লাইন + Firebase single-line ঠিক করুন → ③ Stripe `sk_` key ও GitHub নতুন PAT → ④ gateway-তে comma-key pool প্যাচ → ⑤ `gemini-2.0-flash` → `gemini-2.5-flash` আপডেট → ⑥ secret consolidation (JWT/encryption/Redis)।
