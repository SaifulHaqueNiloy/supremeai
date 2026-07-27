# 🗝️ SupremeAI 2.0 — Multi-Platform Master Matrix (Table View)

_Status: ACTIVE_  
_Last Updated: 2026-07-27_

---

## 📌 Master Environment Matrix (সব প্ল্যাটফর্মের সংকলন টেবিল)

নিচের টেবিলে **SupremeAI 2.0** ইকোসিস্টেমের সকল এনভায়রনমেন্ট ভেরিয়েবল এবং কোন কোন প্ল্যাটফর্মে সেই ভেরিয়েবলটি থাকা **REQUIRED (বাধ্যতামূলক ✅)**, **OPTIONAL (ঐচ্ছিক 🟡)**, অথবা **NOT APPLICABLE (প্রযোজ্য নয় ❌)** তা একনজরে দেখানো হলো:

| Environment Variable / Secret Name | Render Backend | Render Admin | Vercel / Netlify | Cloudflare | Firebase / GCP | GitHub Actions | Infisical | Description (বাংলা বিবরণ) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **`ENV`** | ✅ MUST | ✅ MUST | 🟡 Opt | ❌ | ❌ | ❌ | ✅ MUST | এনভায়রনমেন্ট নাম (`production`/`staging`) |
| **`SUPREMEAI_JWT_SECRET`** | ✅ MUST | ✅ MUST | ❌ | ❌ | ❌ | ❌ | ✅ MUST | JWT টোকেন সিক্রেট |
| **`SUPREMEAI_ENCRYPTION_KEY`** | ✅ MUST | ✅ MUST | ❌ | ❌ | ❌ | ❌ | ✅ MUST | ডেটা এনক্রিপশন চাবি |
| **`ENCRYPTION_KEY`** | ✅ MUST | ✅ MUST | ❌ | ❌ | ❌ | ❌ | ✅ MUST | পে-লোড এনক্রিপশন চাবি |
| **`SUPREMEAI_ADMIN_PASSWORD_HASH`** | ✅ MUST | ✅ MUST | ❌ | ❌ | ❌ | ❌ | ✅ MUST | হ্যাশড অ্যাডমিন পাসওয়ার্ড |
| **`SUPREMEAI_ADMIN_TOTP_SECRET`** | ✅ MUST | ✅ MUST | ❌ | ❌ | ❌ | ❌ | ✅ MUST | Admin 2FA TOTP সিক্রেট |
| **`CI_WEBHOOK_SECRET`** | ✅ MUST | ✅ MUST | ❌ | ❌ | ❌ | ✅ MUST | ✅ MUST | CI Webhook সিগনেচার secret |
| **`ADMIN_NOTIFICATION_EMAIL`** | ✅ MUST | ✅ MUST | ❌ | ❌ | ❌ | ❌ | ✅ MUST | সিকিউরিটি নোটিফিকেশন ইমেইল |
| **`SUPABASE_URL`** | ✅ MUST | ✅ MUST | ❌ | ❌ | ❌ | ❌ | ✅ MUST | Supabase API Endpoint |
| **`SUPABASE_KEY`** | ✅ MUST | ✅ MUST | ❌ | ❌ | ❌ | ❌ | ✅ MUST | Supabase Public Client Key |
| **`SUPABASE_SECRET_KEY`** | 🟡 Opt | 🟡 Opt | ❌ | ❌ | ❌ | ❌ | ✅ MUST | Supabase Admin Secret Key |
| **`SUPABASE_DATABASE_URL_POOLER`** | ✅ MUST | ✅ MUST | ❌ | ❌ | ❌ | ❌ | ✅ MUST | PostgreSQL PgBouncer URL (6543) |
| **`REDIS_URL`** | ✅ MUST | ✅ MUST | ❌ | ❌ | ❌ | ❌ | ✅ MUST | Upstash Redis Connection String |
| **`UPSTASH_REDIS_REST_URL`** | ✅ MUST | ✅ MUST | ❌ | ❌ | ❌ | ❌ | ✅ MUST | Upstash REST API URL |
| **`UPSTASH_REDIS_REST_TOKEN`** | ✅ MUST | ✅ MUST | ❌ | ❌ | ❌ | ❌ | ✅ MUST | Upstash REST Bearer Token |
| **`OPENROUTER_API_KEY`** | 🟡 Opt | 🟡 Opt | ❌ | ❌ | ❌ | ❌ | ✅ MUST | OpenRouter Model Hub Key |
| **`DEEPSEEK_API_KEY`** | 🟡 Opt | 🟡 Opt | ❌ | ❌ | ❌ | ❌ | ✅ MUST | DeepSeek Code Reasoning Key |
| **`GEMINI_API_KEY`** | 🟡 Opt | 🟡 Opt | ❌ | ❌ | ❌ | ❌ | ✅ MUST | Google Gemini API Key |
| **`GROQ_API_KEY`** | 🟡 Opt | 🟡 Opt | ❌ | ❌ | ❌ | ❌ | ✅ MUST | Groq Ultra-Fast Llama-3 Key |
| **`NVIDIA_API_KEY`** | 🟡 Opt | 🟡 Opt | ❌ | ❌ | ❌ | ❌ | ✅ MUST | NVIDIA NIM Inference Key |
| **`OPENAI_API_KEY`** | 🟡 Opt | 🟡 Opt | ❌ | ❌ | ❌ | ❌ | ✅ MUST | OpenAI GPT-4o Key |
| **`ANTHROPIC_API_KEY`** | 🟡 Opt | 🟡 Opt | ❌ | ❌ | ❌ | ❌ | ✅ MUST | Anthropic Claude 3.5 Key |
| **`HF_API_KEY`** | 🟡 Opt | 🟡 Opt | ❌ | ❌ | ❌ | ❌ | ✅ MUST | HuggingFace Open Models Key |
| **`FIRECRAWL_API_KEY`** | 🟡 Opt | 🟡 Opt | ❌ | ❌ | ❌ | ❌ | ✅ MUST | Firecrawl Web Scraper Key |
| **`DEVIN_API_KEY`** | 🟡 Opt | 🟡 Opt | ❌ | ❌ | ❌ | ❌ | ✅ MUST | Devin Autonomous Coding Agent Key |
| **`RUNWAY_API_KEY`** | 🟡 Opt | 🟡 Opt | ❌ | ❌ | ❌ | ❌ | 🟡 Opt | Runway AI Video Gen Key |
| **`KLING_API_KEY`** | 🟡 Opt | 🟡 Opt | ❌ | ❌ | ❌ | ❌ | 🟡 Opt | Kling AI Video Gen Key |
| **`RUNPOD_API_KEY`** | 🟡 Opt | 🟡 Opt | ❌ | ❌ | ❌ | ❌ | 🟡 Opt | RunPod GPU Training Key |
| **`STRIPE_API_KEY`** | ✅ MUST | ✅ MUST | ❌ | ❌ | ❌ | ❌ | ✅ MUST | Stripe Billing Secret Key |
| **`STRIPE_PUBLISHABLE_KEY`** | ✅ MUST | ✅ MUST | ✅ MUST | ❌ | ❌ | ❌ | ✅ MUST | Stripe Public Client Key |
| **`STRIPE_WEBHOOK_SECRET`** | ✅ MUST | ✅ MUST | ❌ | ❌ | ❌ | ❌ | ✅ MUST | Stripe Webhook Signature Secret |
| **`VITE_API_BASE_URL`** | ❌ | ❌ | ✅ MUST | ❌ | ❌ | ❌ | ❌ | Frontend Base Backend URL |
| **`VITE_SUPABASE_URL`** | ❌ | ❌ | ✅ MUST | ❌ | ❌ | ❌ | ❌ | Client-side Supabase URL |
| **`VITE_SUPABASE_ANON_KEY`** | ❌ | ❌ | ✅ MUST | ❌ | ❌ | ❌ | ❌ | Client-side Supabase Key |
| **`CLOUDFLARE_API_TOKEN`** | ❌ | ❌ | ❌ | ✅ MUST | ❌ | ❌ | ✅ MUST | Cloudflare Zone Edit Token |
| **`CLOUDFLARE_ZONE_ID`** | ❌ | ❌ | ❌ | ✅ MUST | ❌ | ❌ | ✅ MUST | Cloudflare Domain Zone ID |
| **`FIREBASE_SERVICE_ACCOUNT_JSON`**| ❌ | ❌ | ❌ | ❌ | ✅ MUST | ❌ | ✅ MUST | Firebase Admin SDK JSON |
| **`GCP_KMS_KEY_RING`** | 🟡 Opt | 🟡 Opt | ❌ | ❌ | ✅ MUST | ❌ | ✅ MUST | GCP KMS Key Ring Name |
| **`GITHUB_TOKEN` / `GITHUB_API_TOKEN`** | 🟡 Opt | 🟡 Opt | ❌ | ❌ | ❌ | ✅ MUST | ✅ MUST | GitHub API Automation Token |
| **`RENDER_API_KEY`** | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ MUST | ✅ MUST | Primary Render API Token |
| **`RENDER_API_KEY_BACKUP`** | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ MUST | ✅ MUST | Admin Render API Token |
| **`VERCEL_TOKEN`** | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ MUST | ✅ MUST | Vercel Deployment Token |
| **`INFISICAL_TOKEN`** | ✅ MUST | ✅ MUST | ❌ | ❌ | ❌ | ❌ | ✅ MUST | Infisical Project Access Token |
| **`SERVICE_ROLE`** | ❌ | ✅ MUST | ❌ | ❌ | ❌ | ❌ | ❌ | Admin Service Role Flag (`admin`) |
| **`DOCS_PASSWORD`** | ❌ | ✅ MUST | ❌ | ❌ | ❌ | ❌ | ✅ MUST | Admin Docs Protected Password |

---

## 💡 Quick Rules Summary

1. **Backend & Admin (Render):** `.env` সিক্রেট ফাইল আপলোড করা সম্পন্ন। Render Backend এবং Render Admin উভয় সার্ভিসে ৬১টি ভেরিয়েবলই লাইভ সিঙ্কড রয়েছে।
2. **Frontend Clients (Vercel / Netlify):** কেবল `VITE_` প্রিফিক্সড ক্লায়েন্ট ভেরিয়েবল ও কানেক্টেড কীসমূহ Vercel-এ সক্রিয় রয়েছে (৮৭টি কী)।
3. **CI/CD Automation (GitHub Actions):** `RENDER_API_KEY`, `VERCEL_TOKEN` এবং `CI_WEBHOOK_SECRET` সিক্রেট হিসেবে সেট করা রয়েছে।
