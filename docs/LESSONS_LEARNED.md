# 🚨 SupremeAI Error & Solution Log (ভুল এবং সমাধানের তালিকা)

এই ফাইলে আমরা প্রজেক্ট ডেভেলপমেন্টের সময় হওয়া বিভিন্ন ভুল (Mistakes), বাগ (Bugs) এবং তাদের স্পেসিফিক সমাধানগুলো (Solutions) গ্রুপ-ভিত্তিক ক্যাটাগরিতে লিস্ট করে রাখব, যাতে ভবিষ্যতে একই ভুল দ্বিতীয়বার না হয়। 

---

## 🏆 The Golden Rule: Upstream Verification (আগের স্টেজ চেক করা)
যেকোনো এরর ফিক্স করার আগে বা নতুন কোনো কোড পুশ করার আগে **সবগুলো এনভায়রনমেন্ট (Local -> CI/CD -> Production) ধাপে ধাপে এবং ক্রমানুসারে (Sequentially & Time-wise) চেক করা বাধ্যতামূলক।** 
সবচেয়ে বড় কথা হলো: **যে স্টেজে এরর হবে, তার আগের স্টেজগুলো সবার আগে চেক করতে হবে।**
- **ভুল (Mistake):** প্রোডাকশনে (Render) এরর দেখে সাথে সাথে কোড ফিক্স করতে যাওয়া, অথচ খেয়াল না করা যে আগের স্টেজে অর্থাৎ GitHub Actions-এ বিল্ড বা টেস্ট ফেইল করে আছে!
- **প্রভাব (Impact):** একটি ছোট ফিক্স করতে গিয়ে অন্য এনভায়রনমেন্টে (যেমন: CI/CD বা প্রোডাকশন) বড় ধরণের চেইন-রিয়েকশন বা ক্র্যাশ হওয়া এবং সময় নষ্ট হওয়া।
- **সমাধান (Solution):** যদি Production-এ এরর হয়, তবে প্রথমে CI/CD (GitHub) চেক করতে হবে যে সেখানে সব ঠিক ছিল কিনা। যদি CI-তে এরর থাকে, তবে Local এনভায়রনমেন্টে টেস্ট করে নিশ্চিত হতে হবে। অর্থাৎ, **Production -> CI -> Local** এভাবে Upstream Trace করে রুট কজ বের করতে হবে।

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
### ৩. SSE Streams Failing with 401 Unauthorized on Load
- **ভুল (Mistake):** ফ্রন্টএন্ড ইনিশিয়ালাইজ হওয়ার সময় `useServerStream` গ্লোবালি `/api/task/stream` এবং `/api/preferences/default/stream`-এ কানেক্ট করার চেষ্টা করে সার্ভারের হেলথ চেক করার জন্য, কিন্তু এই রাউটগুলো `SUPREMEAI_PUBLIC_PATHS`-এ ছিল না।
- **প্রভাব (Impact):** `EventSource` হেডার পাঠাতে পারে না, এবং টোকেন না থাকায় `AuthMiddleware` 401 এরর থ্রো করে। এর ফলে ব্রাউজার কনসোলে বারবার `Failed to load resource: the server responded with a status of 401` স্প্যাম হতে থাকে।
- **সমাধান (Solution):** যেহেতু এগুলো গ্লোবাল লাইফস্প্যান এবং ডিফল্ট স্ট্রিম, তাই `backend/core/config_fields.py`-এর `supremeai_public_paths` লিস্টে `/api/task/stream` এবং `/api/preferences/default/stream` রাউটগুলো অ্যাড করে দেওয়া।

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
- **সমাধান (Solution):** ফাইলে থাকা ভুল ক্যারেক্টার বা সিনট্যাক্স মুছে ফেলা এবং এডিটের সময় Python-এর indentation ও syntax ব্লক সতর্কতার সাথে চেক করা.

### ২. Frontend 401 Unauthorized on Admin Dashboard Metrics
- **ভুল (Mistake):** ফ্রন্টএন্ডে যখনই রিয়েল-টাইম (SSE) স্ট্রিম কানেক্ট হয়, তখন `useStore.ts`-এর `fetchGateStatus()` ফাংশনটি অটোমেটিক্যালি `/api/admin/metrics/dashboard` এ রিকোয়েস্ট পাঠায় কোনো টোকেন চেক করা ছাড়াই।
- **প্রভাব (Impact):** সাধারণ ইউজার বা পাবলিক পেজ (যেমন `/login`) ভিজিট করলে ব্যাকএন্ড এই রিকোয়েস্ট রিজেক্ট করে এবং কনসোলে ৪০১ আনঅথোরাইজড (401 Unauthorized) এরর স্প্যাম হতে থাকে।
- **সমাধান (Solution):** `fetchGateStatus()` এ API কল করার আগে ক্লায়েন্ট-সাইডেই চেক করা যে লোকাল স্টোরেজে `supreme_admin_jwt` (অ্যাডমিন টোকেন) আছে কি না। টোকেন না থাকলে API কল বাইপাস করা।।
