<tool_call>
<function=write>
<parameter=content>

# SupremeAI কোডবেস অডিট রিপোর্ট

**অডিট তারিখ:** ৬ সেপ্টেম্বর, ২০২৬  
**অডিটার:** Kilo (স্বয়ংক্রিয়)  
**স্কোপ:** সম্পূর্ণ কোডবেস — ব্যাকএন্ড, ফ্রন্টএন্ড, ইনফ্রাস্ট্রাকচার, কনফিগারেশন  
**মোট পরিদর্শিত ফাইল:** ১০০+ ফাইল

---

## সংক্ষিপ্ত সারাংশ

এই রিপোর্টে SupremeAI প্ল্যাটফর্মের সম্পূর্ণ কোডবেসের ক্ষতিকর logical gaps, errors, এবং security vulnerabilities উল্লেখ করা হয়েছে। এই সমস্যাগুলো প্রোডাকশন এনভায়রনমেন্টে以下tra issues created করতে পারে — data breach, account takeover, financial loss, service outage, এবং data corruption।

### শীর্ষক প্রায়োরিটি সমস্যাসমূহ

| প্রায়োরিটি | সমস্যা | ক্যাটাগরি | প্রভাব |
| ----------- | -------- | ----------- | -------- |
| P0 | `localStorage`-এ টোকেন সংরক্ষণ + XSS = একাউন্ট টেকওভার | নিরাপত্তা | অত্যন্ত উচ্চ |
| P0 | `dangerouslySetInnerHTML` দিয়ে AI/ব্যাকএন্ড কনটেন্ট রেন্ডার | নিরাপত্তা / XSS | অত্যন্ত উচ্চ |
| P0 | টোকেন URL query parameter-এ (SSE/WebSocket) | নিরাপত্তা | অত্যন্ত উচ্চ |
| P0 | টেস্ট এনভায়রনমেন্টে auth bypass → production-এ privilege escalation | নিরাপত্তা | অত্যন্ত উচ্চ |
| P1 | ওয়ালেট ডাবল-ক্রেডিট রেস কন্ডিশন | লজিক / অর্থনীতি | উচ্চ |
| P1 | `customerStore` logout-এ ক্লিয়ার হয় না → শেয়ার্ড ডিভাইসে ডেটা লিক | প্রোডাকশন | উচ্চ |
| P1 | টোকেন ক্যাশ ডেসিঙ্ক → লগইনের পর 401 error | প্রোডাকশন | উচ্চ |
| P1 | মেমরি লিক (unbounded dicts/lists) → OOM kill | প্রোডাকশন | উচ্চ |
| P1 | অবৈধ webhook endpoints (no auth) | নিরাপত্তা | উচ্চ |
| P1 | SSRF protection incomplete | নিরাপত্তা | উচ্চ |
| P2 | WebSocket reconnect storm (fixed 5s backoff) | লজিক | মধ্যম |
| P2 | Email template-এ HTML injection | নিরাপত্তা | মধ্যম |
| P2 | Hardcoded secrets in multiple files | নিরাপত্তা | মধ্যম |
| P2 | CORS misconfiguration risk | প্রোডাকশন | মধ্যম |
| P2 | Docker health check missing | ইনফ্রা | মধ্যম |

---

## 1. নিরাপত্তা দুর্বলতাসমূহ (Security Vulnerabilities)

### S-1: `localStorage`-এ অথেন্টিকেশন টোকেন সংরক্ষণ

**ফাইল:** `frontend/src/store/authStore.ts:121,155,85`, `frontend/src/store/adminStore.ts:43`

**বর্ণনা:** অথেন্টিকেশন টোকেন (`supremeai_auth_token`, `supreme_admin_jwt`) `localStorage`-এ প্লেইনটেক্সট হিসেবে সংরক্ষিত। কোনো XSS vulnerability থাকলেই যেকোনো অ্যাটাকার `document.querySelector('selector')` বা `localStorage` অ্যাক্সেস করে টোকেন চুরি করতে পারে। `localStorage` পেজে চলমান যেকোনো JavaScript-এর অ্যাক্সেসযোগ্য (third-party scripts, analytics, compromise dependencies সহ)।

**প্রোডাকশন ইমপ্যাক্ট:** অত্যন্ত উচ্চ। টোকেন চুরি → একাউন্ট টেকওভার → অননুমোদিত API অ্যাক্সেস, ডেটা এক্সফিলট্রেশন, অ্যাডমিন প্রিভিলেজ escalation।

---

### S-2: URL Query Parameter-এ টোকেন পাঠানো (SSE / WebSocket)

**ফাইল:** `frontend/src/pages/user/EvolutionForge/EvolutionForge.tsx:82`, `frontend/src/pages/user/CostDashboard.tsx:63`

**বর্ণনা:** টোকেন সরাসরি URL query string-এ পাঠানো হয় SSE এবং WebSocket কানেকশনের জন্য। URL ব্রাউজার হিস্ট্রি, referrer headers, সার্ভার অ্যাক্সেস লগ, প্রক্সি লগ-এ রেকর্ড হয়। এর ফলে দীর্ঘস্থায়ী credentials লগ অ্যাগ্রিগেশন সিস্টেমে Экспোজ হয় এবং টোকেন revocation কঠিন হয়।

**প্রোডাকশন ইমপ্যাক্ট:** অত্যন্ত উচ্চ। লগের মাধ্যমে টোকেন লিক → লগআউটের পরও অননুমোদিত অ্যাক্সেস।

---

### S-3: `dangerouslySetInnerHTML` দিয়ে ব্যবহারকারী/ব্যাকএন্ড কনটেন্ট রেন্ডার

**ফাইল:** `frontend/src/pages/SharedConversationPage.tsx:233`, `frontend/src/components/search/ChatSearchDialog.tsx:111-115`, `frontend/src/components/artifacts/ArtifactsPanel.tsx:208,230`

**বর্ণনা:** ব্যবহারকারী বা AI-generated কনটেন্ট HTML হিসেবে রেন্ডার করা হয়। `formatMessageContent` ফাংশন `&`, `<`, `>` escape করে, কিন্তু এরপর regex-based markdown replacements (`**bold**`, `` `code` ``) প্রয়োগ করে। এতে initial escape bypass করার mixed safe/unsafe patterns এর মাধ্যমে XSS ভেক্টর তৈরি হয়। `artifact.content` SVG mode-তে **abolutely no sanitization** দিয়ে রেন্ডার হয়।

**প্রোডাকশন ইমপ্যাক্ট:** অত্যন্ত উচ্চ। Stored XSS → session hijacking, admin টোকেন চুরি, CSRF via victim's browser।

---

### S-4: `iframe`-এ `allow-scripts` সহ AI HTML রেন্ডার

**ফাইল:** `frontend/src/components/artifacts/ArtifactsPanel.tsx:195-201`

**বর্ণনা:** HTML/React artifacts `<iframe sandbox="allow-scripts">` এর ভিতরে রেন্ডার করা হয়। `sandbox` top-level navigation ও same-origin access নিষ্ক্রিয় করে, কিন্তু `allow-scripts` JavaScript এক্সিকিউশন অনুমোদন দেয়। ব্যাকএন্ড বা poisoned AI response ম্যালিশিয়াস HTML/JS রিটার্ন করলে iframe-তে এক্সিকিউট হয়।

**প্রোডাকশন ইমপ্যাক্ট:** মধ্যম-উচ্চ। ম্যালিশিয়াস artifact → JavaScript execution → potential data exfiltration বা UI redressing।

---

### S-5: টেস্ট এনভায়রনমেন্টে Auth Bypass → প্রোডাকশন এksen escalation

**ফাইল:** `backend/api/dependencies.py:118-122`

**বর্ণনা:** `get_current_user_token()` যখন `is_test_environment() and settings.is_bypass_allowed` true থাকে, তখন অ্যাডমিন টোকেন রিটার্ন করে। যদি `is_bypass_allowed` accidentalরূপে production-এ `True` সেট হয় (বা misconfigured CI variable), তাহলে যেকোনো unauthenticated request অ্যাডমিন টোকেন পায়।

**প্রোডাকশন ইমপ্যাক্ট:** অত্যন্ত উচ্চ। Silent privilege escalation — full admin API access without credentials।

---

### S-6: ওয়েবহুক endpoints-এ missing বা weak authentication

**ফাইল:** `backend/api/routes/webhooks_ai.py:33-90`

**বর্ণনা:** `/api/v1/webhooks/telegram/send-alert` এবং `/callback` endpoints-এ **কোনো authentication নেই**। যেকোনো external caller approval flows, fake PR merges, অ্যালার্ট spam trigger করতে পারে।

**প্রোডাকশন ইমপ্যাক্ট:** অত্যন্ত উচ্চ। Unauthorized state changes (fake approvals/rejections), alert spam, potential social engineering via Telegram bot।

---

### S-7: Fail-open ওয়েবহুক সিগনেচার ভেরিফিকেশন

**ফাইল:** `backend/api/routes/cdc_webhooks.py:26-37`

**বর্ণনা:** `_verify_webhook_signature()` যখন `SUPABASE_WEBHOOK_SECRET` empty থাকে, তখন `True` রিটার্ন করে। এর মানে সিক্রেট unset থাকলে (misconfigured deployment-এ সাধারণ) সব CDC webhooks accepted হয়।

**প্রোডাকশন ইমপ্যাক্ট:** অত্যন্ত উচ্চ। অ্যাটাকার fake CDC events inject করতে পারে vector DB deletions বা অন্যান্য side effects manipulate করতে পারে।

---

### S-8: Email Template-এ HTML Injection

**ফাইল:** `backend/services/email/email_service.py:133-178`

**বর্ণনা:** `user_name`, `reset_link`, `amount` HTML email bodies-এ direct interpolation করা হয় без escaping। যদি কোনো ভ্যালু HTML/JS contain করে (যেমন malicious user display name `<script>` সেট করে), তাহলে email clients-এর মাধ্যমে stored XSS হয়ে যায়।

**প্রোডাকশন ইমপ্যাক্ট:** মধ্যম-উচ্চ। Trusted email domain থেকে phishing, email clients-এ session hijacking।

---

### S-9: Incomplete SSRF Protection in Scraper

**ফাইল:** `backend/services/scraper/security.py:23-46`

**বর্ণনা:** `is_safe_url()` শুধুমাত্র hardcoded private prefixes ও localhost aliases block করে। এটি DNS resolve করে না (DNS rebinding protection নেই), link-local (`169.254.169.254`) comprehensively block করে না, এবং redirects-এর পর final IP validate করে না।

**প্রোডাকশন ইমপ্যাক্ট:** মধ্যম-উচ্চ। অ্যাটাকার cloud metadata endpoints (`169.254.169.254`) বা internal services-এ DNS rebinding এর মাধ্যমে access পেতে পারে।

---

### S-10: In-memory Rate Limiting Does Not Scale

**ফাইল:** `backend/core/middleware/security.py:93-209`

**বর্ণনা:** `RequestValidationMiddleware.REQUEST_LOG` একটি module-level dict। Multi-worker (Gunicorn/Uvicorn with >1 worker) বা multi-replica deployment-এ, প্রতিটি process এর নিজস্ব isolated rate limit থাকে, অর্থাৎ allowed request rate worker সংখ্যার দ্বারা গুণ Multiple হয়।

**প্রোডাকশন ইমপ্যাক্ট:** মধ্যম। Horizontally scaled deployments-এ rate limiting silently bypass হয়।

---

### S-11: Hardcoded Secrets in Multiple Files

**ফাইল:**

- `scripts/devops/test_infisical.py:5-6` — hardcoded Infisical client_id ও client_secret
- `docs/security/pentest/PENETRATION_TESTING_GUIDE.md:351` — hardcoded JWT token
- `backend/core/config_fields.py:38` — hardcoded `dev_password_only` default
- `scripts/deploy/update_infisical_render.py:10` — hardcoded Infisical client_id
- `scripts/security/secrets_rotation_manager.py:65` — hardcoded Redis password

**বর্ণনা:** credentials codebase-এ hardcoded রয়েছে।印度的 version control history-এ 저장 থেকে পূর্ণভাবে unexposed होना কঠিন।

**প্রোডাকশন ইমপ্যাক্ট:** মধ্যম-উচ্চ। Credential exposure → unauthorized access, data breach।

---

## 2. তাত্ত্বিক খাঁটি / ত্রুṭিসমূহ (Logical Gaps / Errors)

### L-1: ওয়ালেট ডাবল-ক্রেডিট রেস কন্ডিশন

**ফাইল:** `backend/api/routes/billing_api.py:59-71, 268-306`

**বর্ণনা:** `_ensure_wallet()` একটি wallet shared `session` এর ভিতরে তৈরি করে এবং তাৎক্ষণিক commit করে (`await session.commit()`)。 Stripe webhook handler একটি নতুন transaction (`async with session.begin()`) открывает যা existing transactions চেক করে এবং wallet update করে। একই `payment_intent.id` এর জন্য দুইটি concurrent webhook delivery commit করার আগে দুটি pass করতে পারে, resulting in double credit।

**প্রোডাকশন ইমপ্যাক্ট:** মধ্যম-উচ্চ। আর্থিক ক্ষতি — double-credited wallets। Idempotency guard আছে কিন্তু check-then-act pattern ডাটাবেজ isolation level-এ atomic নয়।

---

### L-2: অসীম মেমরি লিক (Unbounded Data Structures)

**ফাইল:**

- `backend/core/admin_god.py` — `GodModeAuditLog._entries` (class-level list)
- `backend/services/llm/providers.py` — `_http_clients` dict
- `backend/api/routes/chat_upload.py` — `_uploads` dict
- `backend/api/routes/ci_dashboard_api.py` — `_ci_summaries_store` ও `_ci_history`
- `backend/services/sandbox_service.py` — `active_sandboxes` dict

**বর্ণনা:** এই সব structures monotonically grow হয় eviction, TTL, বা persistence ছাড়া। Long-running processes-এ memory exhaustion হয়ে OOM kill হতে পারে।

**প্রোডাকশন ইমপ্যাক্ট:** মধ্যম-উচ্চ। Render free tier (512 MB) বা যেকোনো constrained container-এ OOM kills।

---

### L-3: Module-level DB Engine Globals Thread-Safety Issue

**ফাইল:** `backend/core/db.py:151-170`

**বর্ণনা:** `_engine` ও `_async_session_factory` module-level globals lazy initialized হয়। `get_session_factory()` lock ব্যবহার করে না, তাই concurrent first calls-এ দুইটি engine তৈরি হতে পারে।

**প্রোডাকশন ইমপ্যাক্ট:** মধ্যম। Startup-এ concurrent load এর সময় double engine creation, connection pool leaks।

---

### L-4: Encryption Key Regenerated on Every Access in Dev Mode

**ফাইল:** `backend/core/config_secrets.py:643-652`

**বর্ণনা:** যদি `.secrets/encryption.key` non-production environment-এ exist না করে, তাহলে `encryption_key` property **প্রতিবার access করার সময়** নতুন Fernet key generate করে (`base64.urlsafe_b64encode(os.urandom(32))`)।

**প্রোডাকশন ইমপ্যাক্ট:** মধ্যম। One key দিয়ে encrypted data অন্য key দিয়ে decrypt করা যায় না, causing silent data corruption বা permanent data loss in dev/staging।

---

### L-5: Browser Processes Leak on Playwright Failures

**ফাইল:** `backend/services/scraper/browser_agent.py:164-170`

**বর্ণনা:** `finally` block `page.close()`, `context.close()`, `browser.close()` কল করে, কিন্তু কোনো intermediate exception থাকলে পরবর্তী cleanup calls skipped হয়ে যায়। `finally`-এ nested try/except নেই।

**প্রোডাকশন ইমপ্যাক্ট:** মধ্যম। Zombie Chromium processes accumulate হয়, host-এর CPU/RAM খরচ করে।

---

### L-6: WebSocket `connect` in `useEffect` Dependency Array → Reconnect Loop

**ফাইল:** `frontend/src/hooks/useWebSocket.ts:187-196`

**বর্ণনা:** `useEffect` dependency array-এ `connect` ও `disconnect` রয়েছে (`[autoConnect, connect, disconnect]`)。 `connect` `useCallback` দিয়ে memoized কিন্তু `resolveUrl` depends on `url`। `url` change করলে `connect` recreate হয়, effect cleanup (disconnect) ও re-run (reconnect) trigger হয়। এর ফলে URL prop change করার সময় rapid disconnect/reconnect storm হতে পারে।

**প্রোডাকশন ইমপ্যাক্ট:** মধ্যম। WebSocket flapping → missed messages, UI flicker, potential server load।

---

### L-7: Multiple Overlapping Auth Authorities → State Desync

**ফাইল:** `frontend/src/store/authStore.ts`, `frontend/src/store/customerStore.ts`, `frontend/src/store/adminStore.ts`

**বর্ণনা:** তিনটি separate stores অথেন্টিকেশন state manage করে:

- `authStore` — canonical user session
- `customerStore` — persisted customer profile independent `hydrated` flag সহ
- `adminStore` — admin step-up state

Token clearing `clearCanonicalSession()`, `clearAuthToken()`, `handleAdminLogout()`-এ spread আছে। `clearAuthToken` circular deps এড়াতে dynamically import করে (`apiClient.ts:64-68`), যার ফলে `cachedToken` store reset করার আগে clear হয়। `customerStore` logout-এ independentভাবে persisted থাকে।

**প্রোডাকশন ইমপ্যাক্ট:** মধ্যম-উচ্চ। Logout-এর পর `customerStore` peut-être আগের user profile ধরে রাখে, stale data display করে। Token cache vs localStorage desync 401 loops করতে পারে।

---

### L-8: Race Condition in `authStore.initialize()` — Optimistic Restore vs Verification

**ফাইল:** `frontend/src/store/authStore.ts:189-263`

**বর্ণনা:** Reload-এ `initialize()` অবিলম্বে `status: LOGGED_IN` optimistic user/role data দিয়ে সেট করে (line 224), এরপর asyncভাবে `/api/v1/auth/me` কল করে verify করার জন্য। Verification response এর আগে logged-in UI দেখাবে। Verification 401 দিল টোকেন clear হয়। Optimistic role `normalizeRole(payload?.role)` থেকে derive হয়, যা `god` এবং `superadmin` কে `admin` normalize করে।

**প্রোডাকশন ইমপ্যাক্ট:** কম-মধ্যম। Elevated privileges এর জন্য ছোট্ট time window; backend এই ধরনের токены `/auth/me` এর সময় reject করলে নির্ভর করে।

---

### L-9: Stripe Webhook Idempotency Race Condition

**ফাইল:** `backend/api/routes/billing_api.py:268-306, 395-430`

**বর্ণনা:** ওয়েবহooks ডাটাবেজ-level idempotency check ব্যবহার করে, কিন্তু atomic `INSERT ... ON CONFLICT DO NOTHING` বা distributed lock ব্যবহার করে না। High concurrency-এর সময় একই webhook delivery এর দুইটি copy `SELECT` check pass করতে পারে।

**প্রোডাকশন ইমপ্যাক্ট:** কম-মধ্যম। Stripe/SSLCommerz retry storms-এর সময় rare double-credit events।

---

## 3. প্রোডাকশন রিস্কসমূহ (Production Risks)

### P-1: User-Controlled Timeout (up to 300 seconds)

**ফাইল:** `backend/api/server.py:190-193`

**বর্ণনা:** `process_query()` ক্লায়েন্ট থেকে `timeout_seconds` accept করে (clamped 1–300)। ম্যালিশিয়াস ক্লায়েন্ট 300s সেট করে async worker কে ৫ মিনিট ধরতে পারে।

**প্রোডাকশন ইমপ্যাক্ট:** মধ্যম। Worker exhaustion, cascading latency, এবং অন্যান্য users-এর জন্য 503 errors।

---

### P-2: Docker Sandbox Timeout Container কে Kill করে না

**ফাইল:** `backend/services/sandbox_service.py:108-110`

**বর্ণনা:** `asyncio.wait_for(loop.run_in_executor(None, run_container), timeout=self.timeout)` শুধুমাত্র future cancel করে। Underlying Docker container চালিয়ে যাওয়ার কারণ `self.client.containers.run()` `detach=False` wait-loop timeout ছাড়া কল করা হয়েছে। Container forcefully kill হয় না।

**প্রোডাকশন ইমপ্যাক্ট:** মধ্যম। Runaway containers CPU/memory খরচ করে, এবং user-submitted code-এর infinite loops এর মাধ্যমে DoS।

---

### P-3: In-memory CI Storage Restart-এ ডেটা হারায়

**ফাইল:** `backend/api/routes/ci_dashboard_api.py:183-184`

**বর্ণনা:** CI summaries ও history module-level dicts/lists-এ সংরক্ষিত। Worker restart, deploy, বা crash হলে সব historical data হারায়।

**প্রোডাকশন ইমপ্যাক্ট:** মধ্যম। Deploy-এর পরে dashboard empty state দেখায়; trend analysis permanently broken।

---

### P-4: JWT ও Encryption Secrets লোকাল ফাইলসিস্টেমে লেখা হয়

**ফাইল:** `backend/core/config_secrets.py:514-539, 643-652`

**বর্ণনা:** Non-production-এ, JWT secrets ও encryption keys `.secrets/jwt_secret.key` ও `.secrets/encryption.key`-এ persist করা হয়। Ephemeral container environments (Render, Docker)-এ এই ফাইলগুলি redeploy-এ disappear হয়ে যায়, key rotation এবং data loss causes করে।

**প্রোডাকশন ইমপ্যাক্ট:** মধ্যম। Redeploy-এর পরে users previously stored data decrypt করতে পারে না; sessions unexpectedly invalidated হয়।

---

### P-5: ফাইল রাইট করার আগে ডিস্ক স্পেস বা Quota Check নেই

**ফাইল:** `backend/api/routes/files.py:137-142`

**বর্ণনা:** `write_file()` প্রতি ফাইল ২ MB পর্যন্ত লেখে available disk space চেক করে না। অ্যাটাকার অনেক ফাইল লিখে ডিস্ক ফüll করতে পারে।

**প্রোডাকশন ইমপ্যাক্ট:** মধ্যম। Disk-full crash, ডাটাবেজ corruption, failed log rotation।

---

### P-6: Checkout URL Construction-এ Spoofable Origin/Referer Headers

**ফাইল:** `backend/api/routes/billing_api.py:144-150`

**বর্ণনা:** `checkout_base` fallback হিসেবে `request.headers.get("origin")` বা `request.headers.get("referer")` ব্যবহার করে। এই headers client-controlled এবং spoof করা যায়।

**প্রোডাকশন ইমপ্যাক্ট:** মধ্যম। Open redirect বা phishing — অ্যাটাকার malicious domain-এ checkout URL point করতে পারে।

---

### P-7: `customerStore` Logout-এ ক্লিয়ার হয় না

**ফাইল:** `frontend/src/store/customerStore.ts:24-64`, `frontend/src/store/authStore.ts:178-187`

**বর্ণনা:** ব্যবহারকারী logout করলে `authStore` ও `adminStore` টোকেন ক্লিয়ার করে, কিন্তু `customerStore` পুরো user profile, chat history, projects, preferences `localStorage`-এ retain করে। একই ব্রাউজারে অন্য user login করলে আগের user এর chat history ও projects immediately visible হয়।

**প্রোডাকশন ইমপ্যাক্ট:** মধ্যম-উচ্চ। Shared devices-এ users এর মধ্যে ডেটা লিকেজ।

---

### P-8: `apiClient` ও `localStorage` এর মধ্যে টোকেন ক্যাশ ডেসিঙ্ক

**ফাইল:** `frontend/src/services/apiClient.ts:30,101-103`, `frontend/src/store/authStore.ts:121`

**বর্ণনা:** `authStore.login()` টোকেন `localStorage`-এ লেখে কিন্তু `updateTokenCache()` কল করে না। এর ফলে `apiClient` এর in-memory `cachedToken` null থাকে login ও পরবর্তী API call এর মধ্যে। এই সময় span-এ requests `Authorization` header ছাড়া পাঠানো হয়।

**প্রোডাকশন ইমপ্যাক্ট:** মধ্যম। Login এর পরবর্তী API call-এ 401 errors, confusing UX।

---

### P-9: Mock Email Mode silently fails

**ফাইল:** `backend/services/email/email_service.py:70-73`

**বর্ণনা:** যখন `api_key` missing থাকে, service একটি mock message logs করে এবং `False` রিটার্ন করে। Callers exception raise করে না, তাই password resets এবং welcome emails silently dropped হয়।

**প্রোডাকশন ইমপ্যাক্ট:** মধ্যম। Users critical emails (password resets, billing alerts) পায় না, support tickets এবং account lockouts triggers হয়।

---

### P-10: Global Module-level Singletons with No Recovery

**ফাইল:** Multiple — `_http_clients`, `_supabase_client`, `_minio_instance`, `redis_manager` ইত্যাদি

**বর্ণনা:** Module-level singletons ব্যবহার করা হয়েছে। Connection pool exhausted বা remote service flap হলে stale client recreate করার কোনো মেকানিজম নেই। Process restart ছাড়া recovery হয় না।

**প্রোডাকশন ইমপ্যাক্ট:** মধ্যম। Network blips-এর পর stale connections; process restart ছাড়া automatic recovery নেই।

---

### P-11: WebSocket Reconnect Storm (Fixed 5s Backoff)

**ফাইল:** `frontend/src/pages/user/CostDashboard.tsx:90`

**বর্ণনা:** WebSocket `onclose` `setTimeout(connectWebSocket, 5000)` trigger করে, fixed ৫ সেকেন্ড delay সহ। Max reconnect limit, jitter, বা backoff নেই। সার্ভার down থাকলে প্রতিটি ৫ সেকেন্ডে reconnect storm তৈরি হয়।

**প্রোডাকশন ইমপ্যাক্ট:** মধ্যম। Outage-এর সময় server load amplification, mobile-এ battery drain।

---

### P-12: `useServerStream` Health Probe Bypasses Auth

**ফাইল:** `frontend/src/hooks/useServerStream.ts:30-34`

**বর্ণনা:** Health probe (`fetch(`${API_BASE_URL}/api/v1/health`)`) কোনো `Authorization` header পাঠায় না। যদি backend health endpoint authentication চায় (বা reverse proxy 401/403 রিটার্ন করে), তাহলে probe সবসময় "offline" দেখাবে, aunque server healthy থাকে।

**প্রোডাকশন ইমপ্যাক্ট:** মধ্যম। False "offline" status → degraded UX, unnecessary SSE reconnect storms।

---

### P-13: Missing Error Boundaries on Lazy Routes

**ফাইল:** `frontend/src/App.tsx:18-29`

**বর্ণনা:** Lazy-loaded routes (`AdminShell`, `AgentWorkspace`, `AIStudio` ইত্যাদি) `<React.Suspense>` দিয়ে wrapped কিন্তু individual `<ErrorBoundary>` দিয়ে নয়। কোনো lazy chunk crash হলে (যেমন `EvolutionForge`, `SkillCatalog`), error root boundary-এ bubble up হবে, failing module-এর বদলে পুরো app কে crash করতে পারে।

**প্রোডাকশন ইমপ্যাক্ট:** মধ্যম। Single component failure → full app white screen।

---

### P-14: Redis Exposed Without Authentication (Local Docker Compose)

**ফাইল:** `docker-compose.yml:153-168`

**বর্ণনা:** Local docker-compose-এ Redis `REDIS_PASSWORD` requirement নেই। External networks-এ exposed থাকলে অননুমোদিত accessPossible।

**প্রোডাকশন ইমপ্যাক্ট:** মধ্যম-উচ্চ। Unauthorized Redis access → data exfiltration, cache poisoning।

---

### P-15: PostgreSQL Default Credentials Fallback

**ফাইল:** `docker-compose.yml:174-176`

**বর্ণনা:** `${POSTGRES_PASSWORD:-postgres}` fallback ব্যবহার করা হয়েছে। Explicit `POSTGRES_PASSWORD` environment variable required না করলে default credentials ব্যবহার হয়।

**প্রোডাকশন ইমপ্যাক্ট:** মধ্যম-উচ্চ। Common attack vector — default credentials দিয়ে unauthorized DB access।

---

### P-16: OTel Collector Ports Exposed to All Interfaces

**ফাইল:** `docker-compose.production.yml:229-231`

**বর্ণনা:** OTel collector ports সব interfaces-এ bind করা হয়েছে (`4317:4317`, `4318:4318`, `8888:8888`, `13133:13133`). অন্যান্য observability components-এর মতো `127.0.0.1` দিয়ে bind করা উচিত।

**প্রোডাকশন ইমপ্যাক্ট:** মধ্যম। Untrusted networks-এ OTel data exposed, potential data exfiltration via telemetry。

---

## 4. ইনপুট ভ্যালিডেশন সমস্যাসমূহ (Input Validation Issues)

### V-1: `formatMessageContent` Partial Escape + Regex Injection

**ফাইল:** `frontend/src/pages/SharedConversationPage.tsx:35-43`

**বর্ণনা:** ফাংশন প্রথমে `&`, `<`, `>` escape করে, এরপর regex replacements (`**bold**`, `` `code` ``) প্রয়োগ করে। Regex `/\\*\\*(.*?)\\*\\*/g` এবং `` /`([^`]+)`/g `` already-escaped string-এ প্রয়োগ হয়। replacement strings (`<strong>$1</strong>`, `<code ...>$1</code>`) inject হয় `$1` কে further escaping ছাড়া। Initial escape bypass করার mixed patterns থাকলে XSS possible।

**প্রোডাকশন ইমপ্যাক্ট:** মধ্যম। Shared conversation content এর মাধ্যমে stored XSS।

---

### V-2: `highlightMatch` Regex Injection

**ফাইল:** `frontend/src/components/search/ChatSearchDialog.tsx:35-43`

**বর্ণনা:** ব্যবহারকারীর search query regex special characters এর জন্য escape করা হয়, কিন্তু replacement HTML (`<mark class="...">$1</mark>`) directly inject করা হয়। যদি backend `highlighted` field return করে unsanitized HTML সহ, তাহলে তা raw রেন্ডার হয়। additionally, regex user-provided text-এ length limits ছাড়া operate করে, pathological input দিয়ে ReDoS vector তৈরি করে।

**প্রোডাকশন ইমপ্যাক্ট:** মধ্যম। Search results এর মাধ্যমে XSS; large text-এ complex queries দিয়ে ReDoS।

---

### V-3: `highlightSyntax` Naive Regex Replacement

**ফাইল:** `frontend/src/components/artifacts/ArtifactsPanel.tsx:67-100`

**বর্ণনা:** Syntax highlighting sequential regex replacements strings, comments, numbers, keywords-এর জন্য প্রয়োগ করে। String regex `/("[^"]*"|'[^']*'|`[^`]*`)/g` escaped quotes handle করে না। 더 importantly, replacements raw code-এ HTML-escaping ছাড়া প্রয়োগ করা হয়। Code string এ `<script>` থাকলে string-highlighting regex `<span>` wrap করার আগে HTML হিসেবে রেন্ডার হয়ে যাবে।

**প্রোডাকশন ইমপ্যাক্ট:** মধ্যম। Malicious code artifacts এর মাধ্যমে XSS।

---

### V-4: Chat Input Not Sanitized Before API Submission

**ফাইল:** `frontend/src/hooks/useChat.ts:69-73, 155-158`

**বর্ণনা:** ব্যবহারকারীর chat input ব্যাকএন্ডে `message: userMsg.content` হিসেবে পাঠানো হয় client-side sanitization বা length limit ছাড়া। ব্যাকএন্ড validate করবে, কিন্তু client-side guard absence কারণে extremely large inputs বা prompt-injection patterns backend-এ filtered ছাড়া reach করে।

**প্রোডাকশন ইমপ্যাক্ট:** কম-মধ্যম। Backend DoS via huge payloads; backend insufficiently guarded হলে prompt injection।

---

### V-5: WebSocket/SSE `JSON.parse` Without Size Bounds

**ফাইল:** `frontend/src/hooks/useWebSocket.ts:114`, `frontend/src/pages/user/EvolutionForge/EvolutionForge.tsx:91`, `frontend/src/store/sessionCockpitStore.ts:101`

**বর্ণনা:** WebSocket ও SSE messages `JSON.parse` করা হয় `event.data` size validate ছাড়া। ম্যালিশিয়াস বা buggy server multi-GB payloads পাঠাতে পারে, browser tab freeze বা crash হতে পারে।

**প্রোডাকশন ইমপ্যাক্ট:** মধ্যম। Client-side DoS via oversized messages।

---

### V-6: CORS Origin Auto-Derivation Risk

**ফাইল:** `backend/core/config_validation.py:421-445`

**বর্ণনা:** যখন `USER_CORS_ORIGINS` / `ADMIN_CORS_ORIGINS` সেট করা না থাকে, তখন সিস্টেম `ALLOWED_HOSTS` থেকে CORS origins derive করে শুধুমাত্র warning দিয়ে। এটি production-এ CORS misconfiguration silently possible করে।

**প্রোডাকশন ইমপ্যাক্ট:** মধ্যম। Silent CORS misconfiguration → unintended cross-origin access।

---

### V-7: No Client-Side Rate Limiting on Chat

**ফাইল:** `frontend/src/hooks/useChat.ts:42-43`

**বর্ণনা:** `send()` শুধুমাত্র `if (!input.trim() || loading) return;` চেক করে। কোনো rate limiting নেই (যেমন max 1 message per second, max message length)। ব্যবহারকারী spam clicks দিয়ে hundreds of API requests fire করতে পারে, exhausting backend quota বা aggressively triggering rate limits।

**প্রোডাকশন ইমপ্যাক্ট:** কম-মধ্যম। Backend rate limit storms; cost inflation।

---

## 5. ইনফ্রাস্ট্রাকচার ও কনফিগারেশন সমস্যাসমূহ (Infrastructure & Config Issues)

### I-1: Missing HEALTHCHECK in Service Dockerfiles

**ফাইল:** `backend/services/worker/Dockerfile`, `backend/services/browser/Dockerfile`, `backend/services/ecosystem/Dockerfile`

**বর্ণনা:** Worker, browser, এবং ecosystem services-এর Dockerfiles-এ HEALTHCHECK নেই। Container unhealthy হওয়ার পরও orchestration layer detect করতে পারে না।

**প্রোডাকশন ইমপ্যাক্ট:** মধ্যম। Unhealthy containers traffic গ্রহণ করতে থাকে, causing silent failures।

---

### I-2: Backend Service Missing Persistent Volume Mounts (Production)

**ফাইল:** `docker-compose.production.yml:12-65`

**বর্ণনা:** `supremeai-backend` service-এ কোনো volume mount নেই। `/app/data`, `/app/uploads`, বা `/app/logs`-এ written data container restart এ instantly lost হয়।

**প্রোডাকশন ইমপ্যাক্ট:** মধ্যম-উচ্চ। Data loss on container restart; uploads disappear; logs lost for debugging。

---

### I-3: Redis Password Exposed in Process List

**ফাইল:** `docker-compose.production.yml:141`

**বর্ণনা:** Healthcheck-এ `redis-cli -a ${REDIS_PASSWORD}` ব্যবহার করা হয়েছে, যা process list-এ পাসওয়ার্ড expose করে।

**প্রোডাকশন ইমপ্যাক্ট:** মধ্যম। Password exposed in `ps aux` output, accessible to any user on the host。

---

### I-4: Prometheus `--web.enable-lifecycle` enables Admin API

**ফাইল:** `docker-compose.production.yml:178`

**বর্ণনা:** `--web.enable-lifecycle` flag unauthenticated users কে Prometheus configuration modify ও data delete করার অনুমোদন দেয়।

**প্রোডাকশন ইমপ্যাক্ট:** মধ্যম। Unauthorized configuration changes, data deletion via admin API。

---

### I-5: No Network Segmentation / Policies

**ফাইল:** `docker-compose.yml`, `docker-compose.production.yml`

**বর্ণনা:** সব services একটি single `supremeai-network` bridge network শেয়ার করে network policies ছাড়া। Service-to-service communication ports-এ unrestricted।

**প্রোডাকশন ইমপ্যাক্ট:** মধ্যম। Lateral movement possible; compromised container可以从其他 serviços communicate করতে পারে。

---

### I-6: Security Scanners Use `continue-on-error: true`

**ফাইল:** `.github/workflows/ci.yml:171-176, 185-189, 192-194`

**বর্ণনা:** BOLA/IDOR detector, blocking call detector, webhook signature checker, rate limit checker, RLS/RBAC auditor সব `continue-on-error: true` ব্যবহার করে। এর মানে critical security findings build কে fail করবে না।

**প্রোডাকশন ইমপ্যাক্ট:** মধ্যম। Security vulnerabilities silently pass through CI, deployed to production。

---

### I-7: Low Code Coverage Thresholds

**ফাইল:** `.github/workflows/ci.yml:49-50`

**বর্ণনা:** Backend coverage threshold 35% এবং frontend 9%। এগুলো extremely low এবং minimal safety net provide করে।

**প্রোডাকশন ইমপ্যাক্ট:** মধ্যম। Bugs এবং regressions easily pass through CI undetected。

---

### I-8: Fail-Open Behavior When Infisical is Unavailable

**ফাইল:** `backend/core/security/secret_vault.py:160-161, 238`

**বর্ণনা:** Infisical down বা circuit breaker open থাকলে vault environment variables-এ fallback হয়। Production-এ এটি secrets expose করতে পারে যদি environment variables vault থেকে less protected হয়।

**প্রোডাকশন ইমপ্যাক্ট:** মধ্যম-উচ্চ। Secrets exposure during vault outages; fail-closed behavior required for critical secrets in production。

---

### I-9: Hardcoded `dev_password_only` Default for Docs Auth

**ফাইল:** `backend/core/config_fields.py:37-40`

**বর্ণনা:** Documentation auth-এর জন্য hardcoded `dev_password_only` default। Production-এ docs auth enabled থাকলেও password missing থাকলে validator auto-generates করে, কিন্তু default value本身 a liability।

**প্রোডাকশন ইমপ্যাক্ট:** মধ্যম-উচ্চ। Weak default password docs-কে expose করতে পারে; logs/error messages-এ leak হতে পারে।

---

### I-10: `ENFORCE_ANTI_HACKING=false` Default

**ফাইল:** `.env.example:94`

**বর্ণনা:** `ENFORCE_ANTI_HACKING` এর default `false`। এটি production-এ copy করার সময় explicit override না করলে anti-hacking protections disabled থাকে।

**প্রোডাকশন ইমপ্যাক্ট:** মধ্যম-উচ্চ। Anti-hacking measures disabled → increased attack surface。

---

## 6. প্রোডাকশন এম্প্যাক্ট সামারি

### Immediate Actions Required (P0 — Do Now)

| # | Problem | File | Action |
| --- | --------- | ------ | -------- |
| 1 | `localStorage` + XSS = account takeover | `authStore.ts`, multiple | Move tokens to HttpOnly secure cookies; sanitize all `dangerouslySetInnerHTML` usage |
| 2 | Token in URL query params | `EvolutionForge.tsx`, `CostDashboard.tsx` | Move token to headers (Authorization) or WebSocket handshake message |
| 3 | Test auth bypass in prod | `api/dependencies.py` | Remove/guard `is_bypass_allowed`; make it impossible in production |
| 4 | Unauthenticated webhooks | `webhooks_ai.py` | Add HMAC authentication to all webhook routes |
| 5 | Fail-open webhook signature | `cdc_webhooks.py` | Fail closed when secret is missing; require explicit secret |

### Short-term Actions (P1 — Within 1 Sprint)

| # | Problem | File | Action |
| --- | --------- | ------ | -------- |
| 6 | Wallet double-credit race | `billing_api.py` | Use DB-level atomic upserts or `SELECT ... FOR UPDATE` |
| 7 | customerStore not cleared on logout | `authStore.ts`, `customerStore.ts` | Clear `customerStore` on logout |
| 8 | Token cache desync | `authStore.ts`, `apiClient.ts` | Call `updateTokenCache()` after login |
| 9 | Unbounded memory leaks | `admin_god.py`, `ci_dashboard_api.py`, `sandbox_service.py` | Add TTL/eviction; replace with Redis/PostgreSQL |
| 10 | SSRF protection incomplete | `scraper/security.py` | Add DNS resolution, post-redirect validation, comprehensive IP blocking |
| 11 | Email HTML injection | `email_service.py` | Sanitize all user inputs or use template engine with auto-escaping |
| 12 | Hardcoded secrets | Multiple files | Rotate all credentials; load from env/Infisical |
| 13 | CORS misconfiguration risk | `config_validation.py` | Make missing CORS origins a hard error in production |
| 14 | Docker health check missing | `worker/Dockerfile`, `browser/Dockerfile` | Add HEALTHCHECK to all service Dockerfiles |

### Medium-term Actions (P2 — Within 1 Month)

| # | Problem | File | Action |
| --- | --------- | ------ | -------- |
| 15 | WebSocket reconnect storms | `CostDashboard.tsx` | Implement exponential backoff with jitter and max reconnect limit |
| 16 | Browser process leaks | `browser_agent.py` | Add nested try/except in finally block for Playwright cleanup |
| 17 | In-memory CI storage | `ci_dashboard_api.py` | Persist CI data to PostgreSQL/Redis with TTL |
| 18 | OTel ports exposed | `docker-compose.production.yml` | Bind OTel ports to `127.0.0.1` |
| 19 | Prometheus admin API | `docker-compose.production.yml` | Remove `--web.enable-lifecycle` |
| 20 | Security scanners non-blocking | `ci.yml` | Remove `continue-on-error: true` from security scanners |
| 21 | Low code coverage | `ci.yml` | Increase backend to 80%, frontend to 70% |
| 22 | Missing error boundaries | `App.tsx` | Add per-route ErrorBoundary components |

### Long-term Actions (P3 — Architectural Improvements)

| # | Problem | Action |
| --- | --------- | -------- |
| 23 | Network segmentation | Implement network policies / service mesh for Docker networks |
| 24 | Python version mismatch | Align Python versions across all Dockerfiles |
| 25 | Nginx headers | Add security headers (X-Content-Type-Options, X-Frame-Options, HSTS) |
| 26 | Image tags | Remove `latest` tag fallback; require explicit version tags |
| 27 | PostgreSQL connections | Review `max_connections`; consider PgBouncer |
| 28 | Fail-closed Infisical | Implement fail-closed behavior for critical secrets in production |
| 29 | Disk quota checks | Add disk space checks before file writes; container-level limits |
| 30 | Stale singletons | Add health check/recovery mechanism for global singletons |

---

## 7. পুরোFinding-এর তালিকা (Category-wise)

### নিরাপত্তা (Security)

1. `localStorage`-এ টোকেন → XSS takeover
2. URL-এ টোকেন → লগ লিক
3. `dangerouslySetInnerHTML` → stored XSS
4. `iframe allow-scripts` → sandbox escape
5. Client-side role bypass (UX guards only)
6. Admin secret in request body
7. Test auth bypass → production escalation
8. Unauthenticated webhook endpoints
9. Fail-open webhook signature verification
10. CI webhook secret in body (not header)
11. Email template HTML injection
12. Incomplete SSRF protection
13. In-memory rate limiting (not scaling)
14. Hardcoded secrets in multiple files
15. MinIO/S3 empty default credentials
16. Admin password hash empty fallback

### তাত্ত্বিক (Logical)

1. Wallet double-credit race condition
2. Unbounded memory leaks (OOM)
3. Module-level DB engine thread-safety
4. Encryption key regenerated on every access
5. Browser process leaks on Playwright failures
6. WebSocket reconnect loop risk
7. Multiple overlapping auth stores (state desync)
8. Auth store optimistic restore race
9. Stripe webhook idemp

The model hit its output limit, so this response may be incomplete.
