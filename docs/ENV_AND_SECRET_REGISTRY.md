# SupremeAI Environment & Secret Registry
> **Single Source of Truth (SSOT)** for all Environment Variables, API Keys, and Secrets.
> সমস্ত ক্লাউড ডেপ্লয়মেন্ট, সিআই/সিডি পাইপলাইন এবং লোকাল ডেভেলপমেন্টে এই রেজিস্ট্রি অনুসারে এনভায়রনমেন্ট ভ্যারিয়েবল বজায় রাখতে হবে।

---

## 🔐 ১. Critical Security & Auth Secrets (Infisical / Primary Vault)

| ভ্যারিয়েবল নাম | প্রযোজ্য প্ল্যাটফর্ম | বিবরণ ও উদ্দেশ্য | ডিফল্ট / উদাহরণ |
| :--- | :--- | :--- | :--- |
| `JWT_SECRET_KEY` | Backend | ইউজার অথেন্টিকেশন ও অ্যাক্সেস টোকেন সাইনিং | `***` (Required in Prod) |
| `ADMIN_OTP_SECRET` | Backend / Functions | JIT অ্যাডমিন অপারেশন ও প্রিভিলেজড অ্যাক্সেস | `***` |
| `SECURITY_SALT` | Backend | পাসওয়ার্ড ও ক্রেডেনশিয়াল হ্যাশিং সল্ট | `***` |
| `INFISICAL_CLIENT_ID` | Backend / CI | Infisical সিক্রেট ভল্ট অটোমেশন মেশিন আইডি | `***` |
| `INFISICAL_CLIENT_SECRET`| Backend / CI | Infisical সিক্রেট ভল্ট ক্লায়েন্ট সিক্রেট | `***` |
| `INFISICAL_ENV` | Backend | ইনফিসিক্যাল এনভায়রনমেন্ট টার্গেট (`production` / `staging`) | `production` |
| `INFISICAL_TIMEOUT` | Backend | ভল্ট ফেচ টাইমআউট সেকেন্ড | `10` |
| `SUPREMEAI_API_KEY` | Extension / Backend | ইন্টারনাল প্রক্সি গেটওয়ে অথেনটিকেশন কি | `***` |
| `STRICT_ENCRYPTION_CHECK`| Backend | ভল্ট হার্ড এনক্রিপশন এনফোর্সমেন্ট | `true` |
| `STRICT_CORS_TEST` | Backend | সিওআরএস অরিজিন ভ্যালিডেশন টেস্ট ফ্ল্যাগ | `false` |
| `TESTING` | Backend / Tests | টেস্ট মোড আইসোলেশন ফ্ল্যাগ | `false` |
| `DATA_DIR` | Backend / Admin | ডেটাবেস ও লগ স্টোরেজ ডিরেক্টরি | `./data` |
| `DATABASE_URL` | Backend / Store | ক্লাউড পোস্টগ্রেস ডিফল্ট কানেকশন স্ট্রিং | `postgresql://...` |
| `AWS_REGION` | Backend / S3 | এস৩ কম্প্যাটিবল স্টোরেজ রিজিওন | `auto` |
| `API_TIMEOUT_MS` | Backend / Event | ইভেন্ট বাস মেসেজ টাইমআউট | `10000` |
| `API_GATEWAY_HOST` | Backend / Twin | ডিজিটাল টুইন এপিআই গেটওয়ে হোস্ট | `localhost` |
| `AUTOHEAL_MAX_RETRIES` | Backend / DevOps | অটো-হিলার সর্বোচ্চ রিস্টার্ট চেষ্টা | `3` |
| `BACKUP_PROVIDER_URL` | Backend / DevOps | ক্লাউড ফলব্যাক ব্যাকআপ প্রোভাইডার লিঙ্ক | `https://...` |
| `CIRCUIT_BREAKER_THRESHOLD`| Backend / DevOps| সার্কিট ব্রেকার ফেইলিউর ট্রিপ কাউন্ট | `5` |
| `CIRCUIT_BREAKER_TIMEOUT`| Backend / DevOps| সার্কিট ব্রেকার কুলডাউন সেকেন্ড | `60` |
| `CLOUDWATCH_CONCURRENCY` | Backend / DevOps| ক্লাউড ওয়াচম্যান কনকারেন্ট মনিটরিং থ্রেড | `5` |
| `ANOMALY_Z_THRESHOLD` | Backend / DevOps| অ্যানোমালি ডিটেকশন জেড-স্কোর থ্রেশহোল্ড | `3.0` |
| `CHAOS_LATENCY_SPIKE_CHANCE`| Backend / Chaos| কেয়স লেটেন্সি স্পাইক চান্স (০.০ - ১.০) | `0.0` |
| `CHAOS_MAX_LATENCY_SPIKE`| Backend / Chaos | কেয়স সর্বোচ্চ লেটেন্সি স্পাইক (ms) | `500` |
| `CHAOS_PACKET_DROP_RATE` | Backend / Chaos | কেয়স প্যাকেট ড্রপ পারসেন্টেজ | `0.0` |
| `GITHUB_ACTIONS` | CI / Backend | সিআই রানিং এনভায়রনমেন্ট ফ্ল্যাগ | `false` |
| `GITHUB_PERSONAL_ACCESS_TOKEN` | Backend / MCP | গিটহাব এমসিপি সার্ভার এক্সেস টোকেন | `***` |
| `GITHUB_REPOSITORY` | Backend / CI | গিটহাব রেপো নাম | `paykaribazaronline/supremeai` |
| `GITHUB_WORKSPACE` | Backend / CI | ওয়ার্কস্পেস ডিরেক্টরি পাথ | `.` |
| `PROJECT_ROOT` | Backend | ব্যাকএন্ড রুট পাথ | `.` |
| `REPO_ROOT` | Backend | রেপো রুট পাথ | `.` |
| `PERSISTENT_DATA_DIR` | Backend | পারসিস্টেন্ট ডেটা ডিরেক্টরি | `./data` |
| `SUPREMEAI_BASE_DIR` | Backend | নলেজ বেস পাথ | `./data/knowledge` |
| `SUPREMEAI_DATA_DIR` | Backend | ডেটা ডিরেক্টরি | `./data` |
| `SUPREMEAI_MEMORY_FILE_PATH` | Backend | মেমোরি ব্যাকআপ ফাইল পাথ | `./data/memory.json` |
| `SUPREMEAI_PROXIES` | Backend | আউটবাউন্ড প্রক্সি লিস্ট | `""` |
| `SUPREMEAI_PUBLIC_PATHS` | Backend | পাবলিক এপিআই রাউট তালিকা | `"/health,/docs"` |
| `SUPREMEAI_DEFAULT_ENV` | Backend | ডিফল্ট এনভায়রনমেন্ট | `production` |
| `SUPREMEAI_ENV` | Backend | রানটাইম এনভায়রনমেন্ট | `production` |
| `SUPREME_ENV` | Backend | সিস্টেম এনভায়রনমেন্ট | `production` |
| `PRE_COMMIT` | Backend / CI | প্রি-কমিট হুক গার্ড | `false` |
| `PYTEST_CURRENT_TEST` | Backend / Test | পাইটেস্ট রানিং টেস্ট ট্র্যাকার | `""` |
| `PLAYWRIGHT_MCP_EXTENSION_TOKEN` | Backend / MCP | প্লে-রাইট এমসিপি সিকিউরিটি টোকেন | `***` |
| `MCP_ALLOWED_DIR` | Backend / MCP | এমসিপি ফাইলসিস্টেম অ্যাক্সেস লিমিট পাথ | `./data/sandbox` |
| `SSRF_BLOCKLIST_HOSTNAMES` | Backend / Security | এসএসআরএফ ব্লকলিস্টেড ডোমেইন তালিকা | `localhost,127.0.0.1` |
| `SSRF_DNS_CACHE_TTL` | Backend / Security | ডিএনএস রেজোলিউশন ক্যাশ টিটিএল | `300` |
| `RATE_LIMIT_ENABLED` | Backend / Security | গ্লোবাল রেট লিমিটার সক্রিয় কিনা | `true` |

---

## ⚡ ২. $0-Cost LLM Muscle Routing (Multi-Provider Fallback Chain)

| ভ্যারিয়েবল নাম | প্রযোজ্য প্ল্যাটফর্ম | বিবরণ ও উদ্দেশ্য | ডিফল্ট / ফলব্যাক |
| :--- | :--- | :--- | :--- |
| `GROQ_API_KEY` | Backend | আল্ট্রা-ফাস্ট Llama-3 70B ইনফারেন্স (0ms ক্যাশিং) | Free Tier Tier-1 |
| `GEMINI_API_KEY` | Backend | Gemini 1.5 Flash / Pro মাল্টি-মোডাল ব্রেইন | Google AI Studio Free |
| `OPENROUTER_API_KEY` | Backend | গ্লোবাল ফ্রি-মডেল ও ডিপসিক/মিস্ত্রাল ফলব্যাক | $0 Cost Router |
| `MISTRAL_API_KEY` | Backend | কোডিং ও রিজন ব্যাকআপ ইঞ্জিন | Mistral Free Tier |
| `COHERE_API_KEY` | Backend | হাই-স্পিড ভেক্টর রি-র‍্যাঙ্কিং ও এম্বেডিং | Free Embed Tier |
| `OLLAMA_URL` | Extension / Local | লোকাল অফলাইন সাপোর্টিং হ্যান্ড | `http://localhost:11434` |
| `LOCAL_MODEL_TIMEOUT` | Backend | লোকাল মডেল ইনফারেন্স টাইমআউট (সেকেন্ড) | `120` |
| `LLM_ROUTER_HOST` | Backend / Twin | ডিজিটাল টুইন রাউটার হোস্ট | `localhost` |
| `STAGEHAND_API_KEY` | Backend / Scraper | স্টেজহ্যান্ড ব্রাউজার অটোমেশন কি | `***` |
| `STAGEHAND_ENV` | Backend / Scraper | স্টেজহ্যান্ড রানটাইম এনভায়রনমেন্ট | `BROWSERBASE` |
| `STAGEHAND_MODEL` | Backend / Scraper | স্টেজহ্যান্ড ভিশন মডেল | `gemini-1.5-flash` |
| `SCRAPER_MAX_CONCURRENCY`| Backend / Scraper | ব্রাউজার স্ক্র্যাপার কনকারেন্ট পেজ লিমিট | `4` |
| `SCRAPER_TIMEOUT_SECONDS`| Backend / Scraper | ব্রাউজার স্ক্র্যাপার পেজ টাইমআউট | `30` |

---

## 🗄️ ৩. Databases, Vectors & Caching Storage

| ভ্যারিয়েবল নাম | প্রযোজ্য প্ল্যাটফর্ম | বিবরণ ও উদ্দেশ্য | ক্যানোনিকাল ফরম্যাট |
| :--- | :--- | :--- | :--- |
| `SUPABASE_DATABASE_URL`| Backend | Postgres & pgvector `ai_memory` ডাটাবেস | `postgresql://postgres:...@...pooler.supabase.com:6543/postgres` |
| `SUPABASE_URL` | Backend / Frontend | Supabase REST / Auth API এন্ডপয়েন্ট | `https://*.supabase.co` |
| `SUPABASE_KEY` | Backend | Supabase সার্ভিস রোল কি | `***` |
| `SUPABASE_ANON_KEY` | Scripts / Frontend | সুপাবেস রিড-অনলি এনন এপিআই কি | `***` |
| `SUPABASE_SERVICE_ROLE_KEY` | Backend / Scripts | সুপাবেস অ্যাডমিন রোল কি | `***` |
| `SUPABASE_DB_URL` | Backend / Store | সুপাবেস সেকেন্ডারি স্টোর কানেকশন | `postgresql://...` |
| `REDIS_URL` | Backend | Upstash Redis TLS Pub/Sub ও এআই কার্সর সিঙ্ক | `rediss://default:...@...upstash.io:6379` |
| `UPSTASH_REDIS_URL` | Backend | আপস্ট্যাশ রেডিজ ব্যাকআপ ক্লাস্টার | `rediss://default:...@...upstash.io:6379` |
| `REDIS_HOST` | Backend / Twin | ডিজিটাল টুইন রেডিজ হোস্ট | `localhost` |
| `DB_HOST` | Backend / Twin | ডিজিটাল টুইন ডাটাবেস হোস্ট | `localhost` |
| `DEFAULT_SERVICE_HOST` | Backend / Twin | ডিজিটাল টুইন ডিফল্ট সার্ভিস হোস্ট | `localhost` |
| `QDRANT_HOST` | Backend / Twin | কিউড্রান্ট ভেক্টর ডাটাবেস হোস্ট | `localhost` |
| `PINECONE_INDEX` | Backend / Memory | পাইনকোন ভেক্টর ইনডেক্স নেম | `supremeai-memory` |
| `VECTOR_BACKEND` | Backend / Memory | ভেক্টর ইঞ্জিন টাইপ (`pgvector` / `sqlite`) | `pgvector` |
| `MINIO_ENDPOINT` | Backend | অবজেক্ট ও প্রজেক্ট ফাইল স্টোরেজ | S3 Compatible / Cloudflare R2 |
| `MINIO_SECURE` | Backend | মিনআইও টিএলএস এনক্রিপশন সক্রিয় কিনা | `true` |
| `STORAGE_BUCKET` | Backend / Storage | ডিফল্ট অ্যাসেট স্টোরেজ বাকেট নেম | `supremeai-assets` |
| `FIREBASE_STORAGE_BUCKET`| Backend / Storage | ফায়ারবেস স্টোরেজ বাকেট নেম | `supremeai-a.appspot.com` |
| `FIRESTORE_EMULATOR_HOST`| Backend / Firestore | ফায়ারস্টোর এমুলেটর হোস্ট | `""` |
| `FIRESTORE_SQLITE_PATH`| Backend / Firestore | ফায়ারস্টোর লোকাল এসকিউলাইট ক্যাশ পাথ | `./data/firestore.db` |
| `FORCE_FIRESTORE_ADC` | Backend / Firestore | গুগল ক্লাউড অ্যাপ্লিকেশন ডিফল্ট ক্রেডেনশিয়ালস | `false` |
| `GCP_FIRESTORE_COLLECTION`| Backend / Firestore | জিসিপি ফায়ারস্টোর মূল কালেকশন | `supremeai_prod` |
| `GCP_FIRESTORE_SQLITE_PATH`| Backend / Firestore| জিসিপি ফায়ারস্টোর লোকাল পাথ | `./data/gcp_firestore.db` |
| `GCP_PUBSUB_SQLITE_PATH`| Backend / Messaging | পাব/সাব লোকাল মেসেজিং কিউ | `./data/gcp_pubsub.db` |
| `GCP_SERVICE_ACCOUNT_JSON`| Backend / GCP | জিসিপি সার্ভিস একাউন্ট জেসন স্ট্রিং | `"{}"` |
| `R2_ACCOUNT_ID` | Backend / Storage | ক্লাউডফ্লেয়ার R2 অ্যাকাউন্ট আইডি | `***` |
| `R2_BUCKET_NAME` | Backend / Storage | ক্লাউডফ্লেয়ার R2 বাকেট নেম | `supremeai-blobs` |
| `SQLITE_PATH` | Backend / Storage | লোকাল ফলব্যাক এসকিউলাইট ডাটাবেস | `./data/supremeai.db` |
| `PERSISTENCE_PG_POOL_MAX`| Backend / DB | পোস্টগ্রেস কানেকশন পুল ম্যাক্সিমাম সাইজ | `10` |
| `SUPREMEAI_MARKETPLACE_DB`| Backend / Store | স্কিল মার্কেটপ্লেস ডাটাবেস পাথ | `./data/marketplace.db` |
| `MEMORY_MCP_PORT` | Backend / Memory | মেমোরি এমসিপি পোর্ট | `8085` |
| `MEMORY_MCP_TRANSPORT` | Backend / Memory | মেমোরি এমসিপি ট্রান্সপোর্ট প্রটোকল (`stdio`/`sse`) | `stdio` |
| `REDIS_TRAFFIC_MAX_BACKGROUND_TASKS` | Backend | রেডিজ ব্যাকগ্রাউন্ড ট্রাফিক লিমিট | `50` |
| `REDIS_TRAFFIC_METRICS_SAMPLING_RATE`| Backend | ট্রাফিক মেট্রিক্স স্যাম্পলিং রেট | `1.0` |

---

## 🌐 ৪. Frontend & Client Portal Variables (Vite / Build-Time)

| ভ্যারিয়েবল নাম | প্রযোজ্য প্ল্যাটফর্ম | বিবরণ ও উদ্দেশ্য | ডিফল্ট ভ্যালু |
| :--- | :--- | :--- | :--- |
| `VITE_PORTAL_TYPE` | Frontend | পোর্টাল টাইপ নির্ধারণ (`admin` বা `user`) | `user` |
| `VITE_ADMIN_BACKEND` | Frontend Admin | অ্যাডমিন পোর্টালের জন্য ক্যানোনিকাল ব্যাকএন্ড URL | `https://supremeai-backend-docker.onrender.com` |
| `VITE_USER_BACKEND` | Frontend User | ইউজার অ্যাপের জন্য ক্যানোনিকাল ব্যাকএন্ড URL | `https://supremeai-backend-docker.onrender.com` |
| `VITE_WS_BASE_URL` | Frontend | রিয়েল-টাইম ভয়েস ও লাইভ ব্রেইন ভিজ্যুয়ালাইজার সকেট | `wss://supremeai-backend-docker.onrender.com` |
| `VITE_API_BASE` | Packages / UI | বেস এপিআই পাথ | `https://supremeai-backend-docker.onrender.com` |
| `VITE_API_URL` | Packages / UI | বেস এপিআই পাথ (ফলব্যাক) | `https://supremeai-backend-docker.onrender.com` |
| `VITE_API_TIMEOUT_MS` | Frontend | ক্লায়েন্ট এপিআই রিকোয়েস্ট টাইমআউট | `15000` |
| `VITE_ENV` | Frontend | ফ্রন্টএন্ড রানটাইম এনভায়রনমেন্ট | `production` |
| `VITE_DEFAULT_ADMIN_EMAIL` | Frontend | ডিফল্ট সুপার অ্যাডমিন ইমেইল | `admin@supremeai.dev` |
| `VITE_GITHUB_REPO` | Frontend | ওয়ার্কস্পেস গিটহাব রিপো লিংক | `paykaribazaronline/supremeai` |
| `VITE_SWARM_HEALTH_POLL_MS`| Frontend | সোয়ার্ম হেলথ পোলিং ইন্টারভাল (ms) | `5000` |
| `VITEST` | Frontend / Test | ভিট টেস্ট এক্সিকিউশন স্টেট ফ্ল্যাগ | `false` |
| `VITE_FIREBASE_API_KEY` | Frontend | ফায়ারবেস অথ ক্লায়েন্ট এপিআই কি | `***` |
| `VITE_FIREBASE_AUTH_DOMAIN` | Frontend | ফায়ারবেস অথ ডোমেন | `supremeai-a.firebaseapp.com` |
| `VITE_FIREBASE_PROJECT_ID` | Frontend | ফায়ারবেস প্রজেক্ট আইডি | `supremeai-a` |
| `VITE_FIREBASE_STORAGE_BUCKET`| Frontend | ফায়ারবেস স্টোরেজ বাকেট | `supremeai-a.appspot.com` |
| `VITE_FIREBASE_MESSAGING_SENDER_ID`| Frontend | মেসেজিং সেন্ডার আইডি | `***` |
| `VITE_FIREBASE_APP_ID` | Frontend | ফায়ারবেস অ্যাপ আইডি | `***` |

---

## 🚀 ৫. Server Runtime, DevOps, Swarm & Tier-8 Evolution

| ভ্যারিয়েবল নাম | প্রযোজ্য প্ল্যাটফর্ম | বিবরণ ও উদ্দেশ্য |
| :--- | :--- | :--- |
| `RENDER` | Backend | রেন্ডার ক্লাউড হোস্টিং ডিটেকশন |
| `RENDER_SERVICE_ID` | Backend / DevOps | রেন্ডার সার্ভিস আইডি |
| `RENDER_API_KEY_BACKUP` | Backend / DevOps | রেন্ডার অটো-হিলার ব্যাকআপ কি |
| `SUPREMEAI_ADMIN_URL` | Backend / DevOps | অ্যাডমিন ব্যাকএন্ড লিঙ্ক |
| `SUPREMEAI_API_URL` | Backend / DevOps | প্রাইমারি ব্যাকএন্ড লিঙ্ক |
| `SUPREMEAI_BACKEND_URL` | Backend / Gateway | এপিআই গেটওয়ে ব্যাকএন্ড লিঙ্ক |
| `HEALTH_CHECK_INTERVAL` | Backend / DevOps | অটো-হিলার হেলথ চেক ইন্টারভাল |
| `HTTP_TIMEOUT_SECONDS` | Backend / DevOps | ক্লাউড এইচটিটিপি টাইমআউট |
| `ENABLE_CHAOS_MODE` | Backend / Resilience | কেয়স ইঞ্জিনিয়ারিং সক্রিয় কিনা |
| `LOCAL_CHAOS_MODE` | Backend / Resilience | লোকাল ডেভেলপমেন্ট কেয়স সিমুলেশন |
| `STAGING_REPLICA_URL` | Backend / Chaos | কেয়স টেস্টিং ও স্টেজিং ব্যাকএন্ড রিপ্রেজেন্টেশন |
| `UVICORN_ACCESS_LOG` | Backend / Server | ইউভিকর্ন এক্সেস লগ সক্রিয় কিনা |
| `UVICORN_GRACEFUL_SHUTDOWN`| Backend / Server | গ্রেসফুল শাটডাউন এনাবল ফ্ল্যাগ |
| `UVICORN_KEEP_ALIVE_TIMEOUT`| Backend / Server | এইচটিটিপি কিপ-অ্যালাইভ টাইমআউট |
| `UVICORN_LOG_LEVEL` | Backend / Server | ইউভিকর্ন লগ লেভেল (`info`/`debug`/`error`) |
| `UVICORN_SHUTDOWN_REQUESTED`| Backend / Server | শাটডাউন হ্যান্ডলার ফ্ল্যাগ |
| `LOG_DIR` | Backend / Monitoring| সিস্টেম লগ ডিরেক্টরি পাথ |
| `DECISION_MIN_CONFIDENCE` | Backend / Decision | এআই ডিসিশন ইঞ্জিন মিনিমাম কনফিডেন্স |
| `VOICE_DIDI_CONFIDENCE`| Backend / Voice | ভয়েস ডিডি বাংলা স্পিচ অ্যাকুরেসি থ্রেশহোল্ড |
| `VOICE_DIDI_MAX_DURATION`| Backend / Voice | ভয়েস রিকোয়েস্ট ম্যাক্সিমাম ডিউরেশন (সেকেন্ড) |
| `SANDBOX_PAYLOAD` | Backend / Sandbox | মাইক্রো রানটাইম টেস্ট পেলোড |
| `N8N_URL` | Backend / Automation | n8n ওয়ার্কফ্লো অটোমেশন নোড URL |
| `NATS_URL` | Backend / Engine | NATS আল্ট্রা-ফাস্ট মেসেজ বাস URL |
| `POSTHOG_HOST` | Backend / Telemetry | পোস্টহগ অবজারভ্যাবিলিটি এন্ডপয়েন্ট |
| `RESEND_FROM_EMAIL` | Backend / Email | ট্রানজ্যাকশনাল ইমেইল সেন্ডার অ্যাড্রেস |
| `SENTRY_ORG_SLUG` | Backend / Monitoring| সেন্ট্রি অবজারভ্যাবিলিটি অর্গানাইজেশন |
| `SENTRY_PROJECT_SLUG` | Backend / Monitoring| সেন্ট্রি অবজারভ্যাবিলিটি প্রজেক্ট |
| `SERVICE_NAME` | Backend / Core | কোর মাইক্রোসার্ভিস আইডেন্টিফায়ার নেম |
| `SERVICE_VERSION` | Backend / Core | মাইক্রোসার্ভিস রিলিজ ভার্সন |
| `TIER8_AUTO_START` | Backend / Tier-8 | টিয়ার-৮ অটো-ইভোল্যুশন ইঞ্জিন অটোস্টার্ট ফ্ল্যাগ |
| `EVOLUTION_DB_PATH` | Backend / Evolution | ইভোল্যুশন ডেটাবেস পাথ |
| `EVOLUTION_DB_PATH_GCS` | Backend / Evolution | ক্লাউড ইভোল্যুশন জিএসএস ব্যাকআপ |
| `EVO_BENCHMARK_EXPECTED` | Backend / Evolution | ইভোল্যুশন বেঞ্চমার্ক এক্সপেক্টেড স্কোর |
| `EVO_FITNESS_THRESHOLD` | Backend / Evolution | জেনেটিক ফিটনেস থ্রেশহোল্ড |
| `EVO_MAX_GENERATIONS` | Backend / Evolution | সর্বোচ্চ জেনেটিক জেনারেশন সংখ্যা |
| `EVO_MODEL` | Backend / Evolution | ইভোল্যুশন কোর মডেল |
| `EVO_MUTATION_RATE` | Backend / Evolution | জেনেটিক মিউটেশন রেট |
| `EVO_POPULATION_SIZE` | Backend / Evolution | জেনেটিক পপুলেশন সাইজ |
| `EVO_SEED_CONFIG` | Backend / Evolution | ইভোল্যুশন সিড কনফিগ ফাইল |
| `EVO_SELECTION_PRESSURE` | Backend / Evolution | জেনেটিক সিলেকশন প্রেশার রেট |
| `SKILLS_DIR` | Backend / Skills | ডায়নামিক স্কিলস ডিরেক্টরি পাথ |
| `SWARM_MODEL` | Backend / Swarm | সোয়ার্ম এজেন্টের জন্য ডিফল্ট ফ্রি মডেল |
| `SWARM_AGENT_TIMEOUT` | Backend / Swarm | সোয়ার্ম এজেন্ট অপারেশন টাইমআউট |
| `SWARM_BYZANTINE_TOLERANCE`| Backend / Swarm | বাইজেন্টাইন ফল্ট টলারেন্স ফ্ল্যাগ |
| `SWARM_DEFAULT_CONSENSUS` | Backend / Swarm | সোয়ার্ম মেজরিটি কনসেনসাস টাইপ |
| `SWARM_HEARTBEAT_INTERVAL` | Backend / Swarm | সোয়ার্ম হার্টবিট ইন্টারভাল (সেকেন্ড) |
| `MARKETPLACE_AUTO_CURATE` | Backend / Market | স্কিল মার্কেটপ্লেস অটো-কিউরেটর ফ্ল্যাগ |
| `MARKETPLACE_CURATE_INTERVAL`| Backend / Market| মার্কেটপ্লেস কিউরেশন ইন্টারভাল |
| `MARKETPLACE_MIN_RATING` | Backend / Market | স্কিলস মিনিমাম স্টার রেটিং |
| `MARKETPLACE_REVIEW_MODEL` | Backend / Market | মার্কেটপ্লেস রিভিউয়ার মডেল |
| `MARKETPLACE_REVIEW_REQUIRED`| Backend / Market| নতুন স্কিলের জন্য রিভিউর বাধ্যবাধকতা |
| `SELF_IMPROVE_LONG_FUNC_THRESHOLD`| Backend / Tier-8| অটো রিফ্যাক্টরিং লং ফাংশন লিমিট |
| `SELF_IMPROVE_MAX_PROPOSALS`| Backend / Tier-8| সেলফ-ইম্প্রুভমেন্ট সর্বোচ্চ প্রস্তাবনা |
| `SELF_IMPROVE_MIN_CONFIDENCE`| Backend / Tier-8| সেলফ-ইম্প্রুভমেন্ট ন্যূনতম কনফিডেন্স |
| `SELF_IMPROVE_MODEL` | Backend / Tier-8| সেলফ-ইম্প্রুভমেন্ট এআই মডেল |
| `SELF_IMPROVE_NESTING_THRESHOLD`| Backend / Tier-8| নেস্টিং গভীরতা থ্রেশহোল্ড |
| `SELF_IMPROVE_SCAN_INTERVAL`| Backend / Tier-8| সেলফ-ইম্প্রুভ স্ক্যান ইন্টারভাল (ঘণ্টা) |
