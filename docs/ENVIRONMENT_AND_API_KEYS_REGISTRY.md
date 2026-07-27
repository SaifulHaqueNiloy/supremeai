# 🗝️ SupremeAI 2.0 — Comprehensive Environment Variables & API Key Registry

_Status: ACTIVE_  
_Last Updated: 2026-07-27_

---

## 📌 Overview

এই ডকুমেন্টেশনে **SupremeAI 2.0** প্রজেক্টের ব্যবহারিক সকল Environment Variable, Secret এবং API Key-এর তালিকা প্রদান করা হয়েছে। কোনো প্ল্যাটফর্মে (Render Backend, Render Admin, Vercel, Infisical) কোন কোন কী **অবশ্যই থাকতে হবে (MUST)** এবং কোনগুলো **ঐচ্ছিক (OPTIONAL)** তা বিস্তারিত বাংলা বিবরণসহ নিচে সাজানো হলো।

---

## 🚀 1. MUST HAVE (প্রতিটি সার্ভিস/প্ল্যাটফর্মে বাধ্যতামূলক)

নিচের সিক্রেটসমূহ **`supremeai-backend`** এবং **`supremeai-admin`** উভয় সার্ভিসে অবশ্যই থাকতে হবে। মিসিং থাকলে Fail-Fast Security অনুযায়ী সার্ভার চালু হবে না।

| Environment Variable | Description (বাংলা বিবরণ) | Type / Scope |
| :--- | :--- | :--- |
| `ENV` | এনভায়রনমেন্ট নাম (`production`, `staging`, `local`) | General |
| `SUPREMEAI_JWT_SECRET` | JWT টোকেন জেনারেট ও ভ্যালিডেশনের গোপন চাবি | Core Security |
| `SUPREMEAI_ENCRYPTION_KEY` | সিস্টেম ডাটা এনক্রিপশন চাবি | Core Security |
| `ENCRYPTION_KEY` | জেনারেল পেলোড এনক্রিপশন চাবি | Core Security |
| `SUPREMEAI_ADMIN_PASSWORD_HASH` | অ্যাডমিন অ্যাকাউন্টের হ্যাশড পাসওয়ার্ড | Admin Auth |
| `SUPREMEAI_ADMIN_TOTP_SECRET` | 2FA / TOTP ভেরিফিকেশনের সিক্রেট | Admin Auth |
| `CI_WEBHOOK_SECRET` | GitHub Actions CI/CD অটোমেশন সিক্রেট | CI/CD |
| `SUPABASE_URL` | Supabase প্রজেক্ট URL | Database / Auth |
| `SUPABASE_KEY` | Supabase Anon / API Key | Database / Auth |
| `SUPABASE_DATABASE_URL_POOLER` | Supabase PostgreSQL Connection Pooler String | Database Connection |
| `REDIS_URL` | Upstash Redis Connection String | Cache & Rate Limit |
| `UPSTASH_REDIS_REST_URL` | Upstash REST API URL | Cache fallback |
| `UPSTASH_REDIS_REST_TOKEN` | Upstash REST Bearer Token | Cache fallback |
| `ADMIN_NOTIFICATION_EMAIL` | সিস্টেম অ্যালার্ট পাঠানোর ইমেইল (e.g. `admin@supremeai.io`) | Alert System |

---

## 🤖 2. AI PROVIDER API KEYS (AI Hub & Multi-Agent Engine)

AI এজেন্টের জন্য প্রয়োজনীয় API Key সমূহ। যেকোনো একটি সক্রিয় থাকলেই সিস্টেম কাজ করবে, তবে ফলব্যাক (Auto-Fallback) এবং PSI (Provider Selection Intelligence) নিশ্চিত করতে সবগুলি থাকা বাঞ্ছনীয়।

| API Key Name | Primary Purpose (মূল ব্যবহার) | Provider | Status |
| :--- | :--- | :--- | :--- |
| `OPENROUTER_API_KEY` | Kimi K2.5 / DeepSeek V3 / Multi-model Hub | OpenRouter | 🌟 High Priority |
| `DEEPSEEK_API_KEY` | Code Execution & Reasoning (PSI-002) | DeepSeek | 🌟 High Priority |
| `GEMINI_API_KEY` | Fast Reasoning & Large Context | Google Gemini | 🌟 High Priority |
| `GROQ_API_KEY` | Ultra-fast Llama-3 Inference | Groq | Recommended |
| `NVIDIA_API_KEY` | High Performance NIM Inference | NVIDIA Cloud | Recommended |
| `OPENAI_API_KEY` | GPT-4o / Embeddings Fallback | OpenAI | Recommended |
| `ANTHROPIC_API_KEY` | Claude 3.5 Sonnet Integration | Anthropic | Optional |
| `HF_API_KEY` | Open-Source Models Inference | HuggingFace | Optional |
| `FIRECRAWL_API_KEY` | Web Scraping & Deep Extraction Agent | Firecrawl | Agent Tooling |
| `DEVIN_API_KEY` | Autonomous Coding Engine | Devin AI | Agent Tooling |

---

## 🛍️ 3. THIRD-PARTY INTEGRATIONS & SERVICES

| Variable Name | Purpose (বাংলা বিবরণ) | Platform Needed |
| :--- | :--- | :--- |
| `STRIPE_API_KEY` | Stripe Secret Key (সাবস্ক্রিপশন ও পেমেন্ট) | Backend & Admin |
| `STRIPE_PUBLISHABLE_KEY` | Stripe Client Publishable Key | Backend & Admin |
| `STRIPE_WEBHOOK_SECRET` | Stripe Webhook Sign Verification | Backend |
| `GITHUB_TOKEN` / `GITHUB_API_TOKEN` | GitHub API Access & Worktree Automation | Backend |
| `GITHUB_CLIENT_ID` | OAuth Authentication | Backend |
| `DISCORD_WEBHOOK_URL` | Discord Channel Alert Notifications | Backend |
| `DISCORD_OTP_WEBHOOK_URL` | Just-In-Time (JIT) OTP Alerts | Backend |
| `RESEND_API_KEY` | Email Dispatch Service | Backend |
| `VERCEL_TOKEN` / `VERCEL_PROJECT_ID` | Vercel Deployment Tracking | CI/CD & Deploy |

---

## ⚙️ 4. SERVICE-SPECIFIC ENV VARIABLES

যেসব এনভায়রনমেন্ট ভেরিয়েবল নির্দিষ্ট সার্ভিসের ভূমিকা অনুযায়ী আলাদা হতে পারে:

### A. `supremeai-backend` (Main API Engine)
- `CORS_ORIGINS`: Frontend ক্লায়েন্ট অরিজিনসমূহ (Comma-separated)
- `ALLOWED_HOSTS`: ব্যাকএন্ড হোস্ট ডোমেইনসমূহ
- `LOW_MEMORY_MODE`: `true` (Render free-tier 512MB RAM লিমিট বজায় রাখার জন্য)

### B. `supremeai-admin` (Admin Control Hub)
- `SERVICE_ROLE`: `admin`
- `ADMIN_CORS_ORIGINS`: Admin Portal Frontend URLs
- `DOCS_PASSWORD`: Swagger / ReDoc প্রোডাকশন পাসওয়ার্ড

---

## 🛡️ 5. OPTIONAL / SAFE FALLBACK KEYS (Crash-Proof)

নিচের সিক্রেটগুলো অনুপস্থিত থাকলে সিস্টেম ক্র্যাশ **করবে না**, সুন্দরভাবে গ্রেসফুল ফলব্যাক বা মকিং করবে:
1. `DISCORD_BOT_TOKEN` (Webhook থাকলে প্রয়োজন নেই)
2. `LAUNCHDARKLY_API_KEY` (Feature flag fallback)
3. `GCP_KMS_KEY_RING` (KMS অনুপস্থিত হলে Software Encryption fallback)
4. `SENTRY_DSN` (অ্যালার্ট ট্রেসিং বন্ধ থাকবে)

---

## 💡 Best Practice & Maintenance Recommendation

1. **Secret File Upload:** Render Dashboard-এ **Secret Files (`.env`)** ফিচার ব্যবহার করে সরাসরি এই সম্পূর্ণ কী-লিস্ট আপলোড করুন।
2. **Real-Time Platform Sync Rule:** যদি লোকাল `.env` বা Infisical-এ কোনো সিক্রেট আপডেট হয়, তবে সেন্ট্রাল সিঙ্ক স্ক্রিপ্ট দিয়ে আপডেট নিশ্চিত করুন:
   ```bash
   python scripts/sync_all_platforms_env.py
   ```
