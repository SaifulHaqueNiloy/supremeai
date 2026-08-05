# 📋 SupremeAI 2.0 — পর্যায়ভিত্তিক সম্পূর্ণ অডিট চেকলিস্ট (Master Audit Checklist)

এই চেকলিস্টের মাধ্যমে সুপ্রিমএআই ২.০ প্রজেক্টের প্রতিটি মডিউল ও সাব-সিস্টেম আলাদাভাবে অডিট, টেস্ট এবং ভেরিফাই করা যাবে।

---

## 🎯 অডিট ব্যবহারের নিয়ম (How to Use)
- প্রতিটি সেকশন স্বাধীন (Independent)। যেকোনো একটি সেকশন ধরে অডিট শুরু করা যাবে।
- অডিট সম্পন্ন হলে `[ ]` কে `[x]` এ রূপান্তর করুন।
- কোনো ত্রুটি বা মক উপাদান পাওয়া গেলে পাশে নোট রাখুন।

---

## 1. ⚙️ backend/ — FastAPI Backend Core
- [ ] **1.1 Authentication & Authorization Guard**
  - [ ] Auth endpoints (`/api/v1/auth/login`, `/register`) সঠিকভাবে কাজ করছে?
  - [ ] JWT token Generation, Refresh & Expiry ঠিকমত কাজ করছে?
  - [ ] Admin Endpoints-এ Role-based Access Control (RBAC) বলবৎ আছে?
- [ ] **1.2 Multi-Cloud & LLM Router (`backend/core/llm_router/`)**
  - [ ] Provider Fallback Mechanism (Moonshot ➔ DeepSeek ➔ Together AI) টেস্ট করা হয়েছে?
  - [ ] Multi-tenant Rate Limiting & Token Quota (80% Cap rule) চেক নিশ্চিত?
  - [ ] LLM Router Mocking ছাড়া আসল ক্লাউড প্রোভাইডারে কাজ করছে?
- [ ] **1.3 Tenant DB & Memory (`backend/core/tenant_db/`)**
  - [ ] Firestore & Redis Connection Pooling এবং Health Check ঠিক আছে?
  - [ ] Multi-tenant schema and dynamic connection switcher অডিট করা হয়েছে?
- [ ] **1.4 Pytest Unit & Integration Coverage**
  - [ ] `pnpm backend:test` বা `pytest` পাস করছে?
  - [ ] টেস্ট কভারেজ কি ন্যূনতম **>= 38%** অর্জিত হয়েছে?

---

## 2. 💻 apps/studio-client/ — React/Vite Web & Desktop Client
- [ ] **2.1 User Portal Pages Audit**
  - [ ] Login (`/login`) & Register (`/register`) Screen
  - [ ] Workspace & Agent Hub (`/workspace`, `/workspace/agent`)
  - [ ] IDE & Web Chat (`/workspace/ide`)
  - [ ] Integrations & Skills Catalog (`/integrations`, `/skills-catalog`)
  - [ ] Architect Tower, Swarm & Evolution Forge (`/architect-tower`, `/swarm`, `/evolution-forge`)
  - [ ] Billing & Profile (`/billing`, `/profile`)
- [ ] **2.2 Admin Portal Pages Audit (`/admin/*`)**
  - [ ] Admin God Mode Dashboard & Interactive Chat Tab
  - [ ] Real-time User Quota & Activity Monitoring
- [ ] **2.3 Client Code Integrity**
  - [ ] `npx tsc --noEmit` টাইপচেক কোনো এরর ছাড়া পাস করে?
  - [ ] `npx vite build --mode production` কোনো ওয়ার্নিং/এরর ছাড়া সম্পন্ন হয়?
  - [ ] কোনো বাটনে `onClick` হ্যান্ডলার ছাড়া খালি বা মক স্টেট নেই তো?

---

## 3. 📱 apps/mobile/ — Flutter Mobile Application
- [ ] **3.1 Auth & Navigation Flow**
  - [ ] Dynamic Theme (Light/Dark Mode) সঠিক?
  - [ ] Screen Routing & State Management (Provider/Riverpod/Bloc) অডিট করা হয়েছে?
- [ ] **3.2 API & Real-time Integration**
  - [ ] WebSocket Stream & SSE Real-time Response প্রাপ্তি সঠিক?
  - [ ] Push Notifications (Firebase Messaging) কানেকশন সঠিক?
- [ ] **3.3 Build Verification**
  - [ ] `flutter analyze` ও `flutter test` গ্রিন (Pass)?

---

## 4. 🧩 tools/vscode-extension/ — VS Code Extension
- [ ] **4.1 Real-Time AI Completion (`SupremeAIChatView.ts`)**
  - [ ] IDE Chat View & Inline Code Completion কাজ করছে?
  - [ ] Local fallback & token optimization (IDE-001 ~ IDE-004) মানা হচ্ছে?
- [ ] **4.2 Build & Packaging**
  - [ ] VS Code extension compile & `.vsix` packaging কোনো এরর দেয় না?

---

## 5. ☁️ CI/CD Pipelines & Cloud Infrastructure (`.github/workflows/`)
- [ ] **5.1 Monorepo CI (`supreme-core-ci.yml`)**
  - [ ] Main Repo ➔ Staging Repo (Direct Push via `MIRROR_REPO_TOKEN`) সঠিক?
  - [ ] Staging Repo ➔ Main Repo (Auto Promotion PR via `MAIN_REPO_TOKEN`) কাজ করছে?
  - [ ] Pytest, Vitest, & Preflight steps গ্রিন (Pass)?
- [ ] **5.2 Environment & Secrets Sync (`scripts/sync_all_platforms_env.py`)**
  - [ ] `.env` ফাইলের সিক্রেট পরিবর্তন হলে তা GitHub Actions, Render, Vercel, Infisical-এ অটো সিঙ্ক হয়?

---

## 6. 🔐 Security, Privacy & Compliance Audit
- [ ] **6.1 Zero Hardcoded Secrets Guard**
  - [ ] কোডবেসের কোথাও প্লেইনটেক্সট API Key/Token hardcode করা নেই?
- [ ] **6.2 JIT OTP & High-Privilege Action Guard**
  - [ ] ডিলিট বা সেনসিটিভ অ্যাডমিন অ্যাকশনে On-spot JIT OTP চাওয়া হয়?
- [ ] **6.3 PII Data Masking Check**
  - [ ] AI Prompt-এ ইউজার ফোন, ইমেইল বা পাসওয়ার্ড পাঠানোর আগে Mask করা হচ্ছে?

---

## 7. 📄 Documentation & Knowledge Audit
- [ ] **7.1 Architecture & API Docs**
  - [ ] OpenAPI / Swagger Spec (`/docs`) আপডেট করা আছে?
  - [ ] `docs/bangla/` এবং `docs/english/` নথিপত্র কোডবেসের সাথে সিঙ্কড?

---

## 8. 🏗️ Infrastructure, Containers & Cloud Workers (`infrastructure/`)
- [ ] **8.1 Cloudflare Workers & Gateways**
  - [ ] `infrastructure/cloudflare_worker.js` ও `wrangler.toml` রুট করা সঠিক?
- [ ] **8.2 Docker & Production Compose**
  - [ ] `docker-compose.prod.yml` এবং `docker-compose.yml` কোনো পোর্ট কনফ্লিক্ট ছাড়া চলে?
- [ ] **8.3 Multi-Cloud Infrastructure (Render / Terraform)**
  - [ ] `render.yaml` ও `render.admin.yaml` পরিবেশ কনফিগারেশন সঠিক?
  - [ ] `infrastructure/terraform/` স্টেট ও প্রোভাইডার সেটিংস অডিট করা হয়েছে?

---

## 9. 🧠 Dynamic Skills Registry & Auto-Repair (`skills/`)
- [ ] **9.1 Skills Registry & Installer (`skills/registry.py`, `installer.py`)**
  - [ ] ডাইনামিক স্কিল লোডার ও রেজিস্ট্রি ফাংশনালিটি কাজ করছে?
  - [ ] স্কিল ইনস্টলেশন ফেইল করলে auto-repair মেকানিজম কাজ করে?
- [ ] **9.2 Skills Marketplace API (`skills/marketplace.py`)**
  - [ ] মার্কেটপ্লেস স্কিল স্কিমা (`schema.py`) ভ্যালিডেশন পাস করে?

---

## 10. ⚡ Performance Benchmark & Zero-Cost Quotas
- [ ] **10.1 Performance Benchmark (`scripts/benchmark/perf_benchmark.py`)**
  - [ ] `python scripts/benchmark/perf_benchmark.py --url http://127.0.0.1:8000 --requests 50` সফলভাবে সম্পন্ন হয়?
  - [ ] Response latency cutoff (P99 < 2000ms) বজায় আছে?
- [ ] **10.2 Free-Tier Quota Monitor**
  - [ ] Render 750 free hours limit মনিটরিং স্ক্রিপ্ট কার্যকর?
  - [ ] Cloudflare & Vercel-এর ফ্রী লিমিট ক্যাপ ওভারল্যাপ করছে না?

