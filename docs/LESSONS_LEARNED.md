# 🚨 SupremeAI Error & Solution Log (ভুল এবং সমাধানের তালিকা)

এই ফাইলে আমরা প্রজেক্ট ডেভেলপমেন্টের সময় হওয়া বিভিন্ন ভুল (Mistakes), বাগ (Bugs) এবং তাদের স্পেসিফিক সমাধানগুলো (Solutions) গ্রুপ-ভিত্তিক ক্যাটাগরিতে লিস্ট করে রাখব, যাতে ভবিষ্যতে একই ভুল দ্বিতীয়বার না হয়। 

---

## 🏆 The Golden Rule: Sequential Environment Verification
যেকোনো এরর ফিক্স করার আগে বা নতুন কোনো কোড পুশ করার আগে **সবগুলো এনভায়রনমেন্ট (Local -> CI/CD -> Production) ধাপে ধাপে এবং ক্রমানুসারে (Sequentially & Time-wise) চেক করা বাধ্যতামূলক।**
- **ভুল (Mistake):** লোকাল এনভায়রনমেন্ট বা নির্দিষ্ট কোনো ফাইলে সমস্যা না দেখেই সরাসরি প্রোডাকশন বা CI-এর উপর ভিত্তি করে তাড়াহুড়ো করে ফিক্স অ্যাপ্লাই করা।
- **প্রভাব (Impact):** একটি ছোট ফিক্স করতে গিয়ে অন্য এনভায়রনমেন্টে (যেমন: CI/CD বা প্রোডাকশন) বড় ধরণের চেইন-রিয়েকশন বা ক্র্যাশ হওয়া।
- **সমাধান (Solution):** যেকোনো ফিক্সের আগে রুট কজ (Root Cause) অ্যানালাইসিস করতে হবে এবং ধাপে ধাপে লোকাল → CI লগ → টার্গেট সার্ভার (Render/Vercel) চেক করে নিশ্চিত হওয়ার পরই কোড পরিবর্তন করতে হবে।

---

## 🏗️ DevOps & Deployment Errors

### ১. pnpm Workspace URL Error in Render
- **ভুল (Mistake):** `render.yaml` ফাইলে ফ্রন্টএন্ড সার্ভিসের `rootDir` পরিবর্তন করে `frontend` দেওয়া, কিন্তু `pnpm` ওয়ার্কস্পেস সেটআপ অনুযায়ী রুট ফোল্ডার থেকেই প্যাকেজ ইন্সটল করার কথা।
- **প্রভাব (Impact):** `Unsupported URL Type "workspace:"` এরর দিয়ে npm/pnpm ইন্সটলেশন ফেইল করা।
- **সমাধান (Solution):** `render.yaml`-এ ফ্রন্টএন্ডের `rootDir` হিসেবে `.` (রুট) সেট করা, যাতে সে রুট ফোল্ডার থেকে ওয়ার্কস্পেস কনফিগারেশন পায় এবং `buildCommand` হিসেবে `cd frontend && pnpm run build` ব্যবহার করা।

### ২. GitHub Actions `git diff` Failed Due to Unstaged Test Artifacts
- **ভুল (Mistake):** CI ওয়ার্কফ্লোতে `git diff --quiet` ব্যবহার করা, যা ওয়ার্কিং ডিরেক্টরির যেকোনো আনকমিটেড চেঞ্জ ধরলে (যেমন `pytest` চলাকালীন তৈরি হওয়া `.pkl` বা টেম্প ফাইল) ফেইল (Exit 1) করে।
- **প্রভাব (Impact):** লিনিয়ার CI ফেইল হয়ে যাওয়া এবং লকফাইল অটো-আপডেট বন্ধ হয়ে যাওয়া।
- **সমাধান (Solution):** `ci.yml`-এ `git diff --cached --quiet` ব্যবহার করা, যাতে শুধুমাত্র আগে থেকে স্টেজ (`git add`) করা ফাইলের উপর ভিত্তি করে ডিটেকশন হয়।

---

## 🔒 Security, Secrets & Configuration

### ১. Missing Optional Secrets Causes Server Crash
- **ভুল (Mistake):** `secret_vault.py` ফাইলে সব সিক্রেটকেই সমান গুরুত্ব দিয়ে দেখা। ফলে কোনো ঐচ্ছিক (Optional) সিক্রেট (যেমন: `HF_API_KEY`) মিসিং থাকলেও `RuntimeError` বা `CRITICAL` ইভেন্ট ট্রিগার হয়ে সার্ভার ক্র্যাশ করা।
- **প্রভাব (Impact):** প্রোডাকশনে সার্ভার বারবার শাটডাউন হয়ে যাওয়া।
- **সমাধান (Solution):** সিক্রেটগুলোকে `HARD_REQUIRED_SECRETS` এবং `OPTIONAL_SECRETS`-এ ভাগ করা। ঐচ্ছিক সিক্রেট মিসিং থাকলে ক্র্যাশ না করে শুধু একটি ওয়ার্নিং লগ করা এবং গ্রেসফুলি খালি স্ট্রিং ফলব্যাক হিসেবে ব্যবহার করা।

### ২. Initial Frontend Load Failing with "Missing authentication token"
- **ভুল (Mistake):** ফ্রন্টএন্ড স্টার্টআপের সময় ব্যাকএন্ডের `/api/config/public` কল করে, কিন্তু ঐ রাউটটি `SUPREMEAI_PUBLIC_PATHS` (config_fields.py)-এ অন্তর্ভুক্ত না থাকা। 
- **প্রভাব (Impact):** গ্লোবাল AuthMiddleware একে প্রটেক্টেড রাউট হিসেবে ধরে নিয়ে `401 Unauthorized` দেয়। ফলে ফ্রন্টএন্ড রিয়েল কনফিগ না পেয়ে Safe-Default ফলব্যাকে চলে যায় এবং ইউজারের কাছে "Missing authentication token" টোস্ট দেখায়।
- **সমাধান (Solution):** `backend/core/config_fields.py` এর `supremeai_public_paths` লিস্টে `/api/config/public` যোগ করা।

---

## 🌐 Network & CORS (Frontend-Backend Connection)

### ১. Frontend-Backend CORS Connection Error
- **ভুল (Mistake):** ব্যাকএন্ডের `CORS_ORIGINS` এনভায়রনমেন্ট ভেরিয়েবলে ফ্রন্টএন্ডের লাইভ URL (`supremeai-frontend-xxxx.onrender.com`) যুক্ত না থাকা। 
- **প্রভাব (Impact):** ফ্রন্টএন্ড থেকে ব্যাকএন্ডে API কল করলে ব্রাউজার `Network Error: Failed to fetch` বা `Missing authentication token` এরর দেয়, কারণ ব্যাকএন্ড ঐ অপরিচিত ডোমেইনকে ব্লক করে দেয়।
- **সমাধান (Solution):** ব্যাকএন্ডের `.env` ফাইল এবং Render-এর Environment Variables-এ সঠিক ফ্রন্টএন্ড URL আপডেট করে সিঙ্ক (`sync_secrets_to_render.py`) করা। `render.yaml`-এ URL হার্ডকোড করা থেকে বিরত থাকা।

---

## 💻 Code Level & Syntax Bugs

### ১. Render Deployment Crash (Syntax Error in python)
- **ভুল (Mistake):** Python ফাইলে (যেমন `secret_vault.py`) এডিট করার সময় ভুলবশত ফাইলের ভেতরে `invalid character 'া' (U+09BE)` বা বাংলা কমেন্টের অংশ কোডের ব্লকে চলে গিয়েছিল। 
- **প্রভাব (Impact):** `uvicorn` সার্ভার রান হওয়ার সময় মডিউল ইম্পোর্ট ফেইল করে এবং `No open ports detected` এরর দিয়ে ডিপ্লয়মেন্ট ক্র্যাশ করে।
- **সমাধান (Solution):** ফাইলে থাকা ভুল ক্যারেক্টার বা সিনট্যাক্স মুছে ফেলা এবং এডিটের সময় Python-এর indentation ও syntax ব্লক সতর্কতার সাথে চেক করা।
