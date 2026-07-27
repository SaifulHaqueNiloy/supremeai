# 🗝️ SupremeAI 2.0 — Multi-Platform Master Environment & API Key Registry

_Status: ACTIVE_  
_Last Updated: 2026-07-27_

---

## 📌 Overview

এই মাস্টার রেজিস্ট্রিতে **SupremeAI 2.0** ইকোসিস্টেমের সাথে যুক্ত **সকল ৮+ কানেক্টেড প্ল্যাটফর্ম ও ক্লাউড সার্ভিস** (Render, Vercel, Netlify, Cloudflare, Firebase, Supabase, GitHub, Infisical ইত্যাদি) এর সিক্রেট কনফিগারেশন, API Keys, এবং কোন প্ল্যাটফর্মে কী কী এনভায়রনমেন্ট ভেরিয়াবেল থাকা **MUST (বাধ্যতামূলক)** তা বিস্তারিত বাংলা গাইডলাইনসহ লিপিবদ্ধ করা হলো।

---

## 🌐 1. MULTI-PLATFORM ECOSYSTEM & SERVICE ROLES

SupremeAI 2.0 মাল্টি-ক্লাউড আর্কিটেকচারে নিচের প্ল্যাটফর্মসমূহ কানেক্টেড এবং সক্রিয়:

| Platform / Service | Primary Role (প্রধান কাজ) | Environment Sync Method |
| :--- | :--- | :--- |
| **Render (User Backend)** | Main FastAPI Application & Engine | Environment Group / `.env` Secret File |
| **Render (God Mode Admin)** | System Admin & Operations Dashboard | Environment Group / `.env` Secret File |
| **Vercel** | React / Vite Web Client App | Vercel Project Environment Variables |
| **Netlify** | Secondary / Edge Web Client Host | Netlify Site Environment Variables |
| **Cloudflare** | DNS, SSL, WAF Guard & Edge Workers | Cloudflare Wrangler / Dashboard Secrets |
| **Firebase / GCP** | Push Notifications, Hosting & Cloud KMS | Firebase Service Account JSON / Secret Manager |
| **Supabase** | Cloud PostgreSQL & Authentication Auth | Supabase Dashboard / Connection Strings |
| **Upstash (Redis)** | Global Low-Latency Cache & Rate Limiting | Upstash Console / Environment Keys |
| **GitHub** | Monorepo CI/CD & Worktree Automation | GitHub Repository Secrets & Actions |
| **Infisical** | Enterprise Centralized Secret Vault | Infisical Machine Token / Project Sync |

---

## 🔐 2. MUST-HAVE KEYS PER PLATFORM (কোন প্ল্যাটফর্মে কোন কী থাকা বাধ্যতামূলক)

### 🔹 A. RENDER (Backend Engine & Admin Control)
> **ফাইল রেজিস্ট্রি:** `.env` বা Secret File `/etc/secrets/.env`

* **Core Identity:** `ENV=production`, `SUPREMEAI_JWT_SECRET`, `SUPREMEAI_ENCRYPTION_KEY`, `ENCRYPTION_KEY`, `SUPREMEAI_ADMIN_PASSWORD_HASH`, `SUPREMEAI_ADMIN_TOTP_SECRET`
* **Databases & Cache:** `SUPABASE_DATABASE_URL_POOLER`, `SUPABASE_URL`, `SUPABASE_KEY`, `REDIS_URL`, `UPSTASH_REDIS_REST_URL`, `UPSTASH_REDIS_REST_TOKEN`
* **Integrations:** `STRIPE_API_KEY`, `STRIPE_WEBHOOK_SECRET`, `CI_WEBHOOK_SECRET`, `ADMIN_NOTIFICATION_EMAIL`
* **AI Provider Keys:** `OPENROUTER_API_KEY`, `DEEPSEEK_API_KEY`, `GEMINI_API_KEY`, `GROQ_API_KEY`, `NVIDIA_API_KEY`, `OPENAI_API_KEY`
* **Admin-Only (Only `supremeai-admin`):** `SERVICE_ROLE=admin`, `DOCS_PASSWORD`

---

### 🔹 B. VERCEL & NETLIFY (Web Frontend Clients)
> **কন্টেক্সট:** React / Vite স্টুডিও ক্লায়েন্ট কেবল পাবলিক এবং নিরাপদে ক্লায়েন্ট-সাইডে ব্যবহার উপযোগী কী গ্রহণ করে।

| Environment Variable | Description (বাংলা বিবরণ) | Target Scope |
| :--- | :--- | :--- |
| `VITE_API_BASE_URL` | Render Backend API URL (`https://supremeai-backend-08zd.onrender.com`) | Build & Runtime |
| `VITE_SUPABASE_URL` | Supabase Public Endpoint | Client Auth |
| `VITE_SUPABASE_ANON_KEY` | Supabase Public Anonymous Key | Client Auth |
| `VITE_STRIPE_PUBLISHABLE_KEY` | Stripe Client Billing Key | Payment UI |
| `VERCEL_ORG_ID` | Vercel Organization Identifier | Deploy Automation |
| `VERCEL_PROJECT_ID` | Vercel Project Identifier | Deploy Automation |
| `VERCEL_TOKEN` | Vercel API Access Deployment Token | CI/CD |

---

### 🔹 C. CLOUDFLARE (Edge Proxy & Security Gate)
> **কন্টেক্সট:** Cloudflare Workers, DNS & WAF Guard

| Secret / Config Name | Description (বাংলা বিবরণ) |
| :--- | :--- |
| `CLOUDFLARE_API_TOKEN` | Zone & DNS Editing Token |
| `CLOUDFLARE_ZONE_ID` | Main Domain Zone Identifier |
| `CLOUDFLARE_ACCOUNT_ID` | Cloudflare Account Identity |
| `WORKERS_AUTH_SECRET` | Edge Proxy Ingress Verification Secret |

---

### 🔹 D. FIREBASE & GOOGLE CLOUD (GCP)
> **কন্টেক্সট:** Auth Integration, Web Push Notifications & Cloud KMS Security

| Variable Name | Description (বাংলা বিবরণ) |
| :--- | :--- |
| `FIREBASE_PROJECT_ID` | Firebase Project Identifier |
| `FIREBASE_SERVICE_ACCOUNT_JSON` | Firebase Admin SDK Auth Credentials |
| `GCP_PROJECT_ID` | Google Cloud Engine Project ID |
| `GCP_KMS_KEY_RING` | KMS Key Ring Identifier for Data Encryption |
| `GCP_REGION` | Cloud Region (e.g. `us-central1`) |

---

### 🔹 E. SUPABASE (Cloud Database Hub)

| Variable / Secret Name | Description (বাংলা বিবরণ) |
| :--- | :--- |
| `SUPABASE_URL` | Supabase REST / Realtime Base Endpoint |
| `SUPABASE_KEY` | Public Anon API Key |
| `SUPABASE_SECRET_KEY` | Service Role Admin Key (Bypasses RLS) |
| `SUPABASE_DATABASE_URL` | Direct Direct PostgreSQL Connection String (Port 5432) |
| `SUPABASE_DATABASE_URL_POOLER` | PgBouncer Connection Pooler String (Port 6543) |
| `SUPABASE_ACCESS_TOKEN` | Management API Token (CLI & Migrations) |
| `SUPABASE_JWKS_URL` | Supabase Auth JWT Public Keys endpoint |

---

### 🔹 F. GITHUB ACTIONS (Monorepo CI/CD & Security Gateways)
> **লোকেশন:** Repository Secrets (`Settings -> Secrets and variables -> Actions`)

| Secret Name | Description (বাংলা বিবরণ) |
| :--- | :--- |
| `GITHUB_TOKEN` / `GITHUB_API_TOKEN` | GitHub CLI and API Automation Access |
| `RENDER_API_KEY` | Primary Render Account API Key |
| `RENDER_API_KEY_BACKUP` | Admin Workspace Render API Key |
| `RENDER_DEPLOY_HOOK_URL` | Auto Deployment Trigger URL |
| `VERCEL_TOKEN` | Auto Deployment Trigger Token |
| `CI_WEBHOOK_SECRET` | Webhook Signature Verification |

---

### 🔹 G. INFISICAL (Enterprise Vault & Single Source of Truth)

| Variable Name | Description (বাংলা বিবরণ) |
| :--- | :--- |
| `INFISICAL_TOKEN` | Infisical Project Access Token |
| `INFISICAL_CLIENT_ID` | Machine Identity Client ID |
| `INFISICAL_CLIENT_SECRET` | Machine Identity Client Secret |

---

## 🛠️ 3. AUTOMATED MULTI-PLATFORM SYNC PROTOCOL

AGENTS.md-এর নিয়ম অনুযায়ী:
> **Multi-Platform Secret Synchronization:**
> যেকোনো API key বা secret পরিবর্তন করা হলে তা **একসাথে সমস্ত কানেক্টেড প্ল্যাটফর্মে রিয়েল-টাইমে আপডেট করা বাধ্যতামূলক**।

সিক্রেট পরিবর্তন হলে নিচের কমান্ডটি ব্যবহার করে সিঙ্ক ভ্যালিডেট করুন:
```bash
# Verify Render & connected environment configurations
python .github/scripts/verify-render-deploy.py
```
