# GitHub Action CI #1269 & Commit `247d4f48b1` Deep Analysis Report

**তারিখ:** ২৭ জুলাই, ২০২৬  
**প্রজেক্ট:** SupremeAI 2.0  
**কমিট হ্যাশ:** `247d4f48b1bb3bd826f5084c270ccb09d07b5986`  
**কমিটার:** SupremeAI CI Bot (`ci-bot@supremeai.dev`)  
**আহ্বায়ক/প্রসঙ্গ:** GitHub Actions CI Run #1269 (Backend core dependency fix)

---

## 🎯 ১. সারসংক্ষেপ ও কাজের মূল উদ্দেশ্য (Executive Summary)

GitHub Actions CI run #1269-এ পুশ করা commit **`247d4f48b1`**-এর মাধ্যমে Backend CI Build Fail/Disk Outage সমস্যার মূল কারণ চিহ্নিত করে সমাধান করা হয়েছে।

পূর্বে CI রানারগুলোতে `poetry install --with dev` চালানোর সময় `torch` এবং `sentence-transformers` লাইব্রেরিগুলোর সাথে বিশাল আকারের CUDA Toolkit binaries (`nvidia-nccl-cu12`, `cu13`) স্বয়ংক্রিয়ভাবে ডাউনলোড হতো। এর ফলে GitHub-hosted CPU রানারের মেমোরি ও ডিস্ক স্পেস নিঃশেষ হয়ে `poetry install` ফেইল করছিল। এই কমিটে PyTorch-কে একটি **Optional `[tool.poetry.group.ml]`** ডিপেনডেন্সিতে সরিয়ে নেওয়া হয়েছে এবং সম্পর্কিত Module Import Guard তৈরি করা হয়েছে।

---

## 🔍 ২. সমস্যা ও সমাধান বিশ্লেষণ (Root Cause & Chain Analysis)

এই কমিটে ৪টি পর্যায়ক্রমিক সমস্যা চিহ্নিত করে সমাধান করা হয়েছে:

### 📌 Root Cause 1: PyTorch Hard Dependency & Out-of-Disk Error
- **সমস্যা:** `torch` এবং `sentence-transformers` মূল `pyproject.toml`-এর ডিফল্ট ডিপেনডেন্সি লিস্টে ছিল। এর ফলে CPU-only GitHub Actions রানারে ২টি পূর্ণাঙ্গ CUDA GPU Stack ডাউনলোড হয়ে ডিস্ক ফুল হয়ে যাচ্ছিল (Zero-Cost কাঠামোর বিপরীত)।
- **বিশ্লেষণ:** কোডবেসে অনুসন্ধান করে দেখা যায়, `evolution/*` মডিউলগুলো ব্যবহৃত হচ্ছে না এবং `sentence-transformers` কল করা মডিউলগুলো ইতিমধ্যেই `try/except ImportError` গার্ড দিয়ে সুরক্ষিত।
- **সমাধান:** `torch` ও `sentence-transformers`-কে পৃথক অপশনাল গ্রুপ `[tool.poetry.group.ml]`-এ সরিয়ে নেওয়া হয়েছে এবং `poetry.lock` পুনরায় জেনারেট করা হয়েছে।

---

### 📌 Root Cause 2: Unconditional Evolution Submodule Imports
- **সমস্যা:** `backend/core/__init__.py` এবং `backend/evolution/__init__.py`-তে PyTorch-নির্ভর মডিউলগুলোকে কোনো ট্রাই-ক্যাচ ছাড়া সরাসরি ইম্পোর্ট করা হচ্ছিল। যেহেতু `core` মডিউল প্রায় পুরো অ্যাপ্লিকেশনে ইম্পোর্ট হয়, তাই `torch` ইনস্টল না থাকলে পুরো ব্যাকএন্ড ক্র্যাশ করত।
- **সমাধান:** উভয় `__init__.py` ফাইলে `try/except ImportError` গার্ড বসানো হয়েছে এবং `EVOLUTION_COMPONENTS_AVAILABLE` এবং `TORCH_COMPONENTS_AVAILABLE` ফ্ল্যাগ দেয়া হয়েছে। PyTorch না থাকলে clear `RuntimeError` বার্তা প্রদান করা হয়েছে ("poetry install --with ml run করুন")।

---

### 📌 Root Cause 3: Non-existent `core.auth` Import in LLM Gateway
- **সমস্যা:** `api/routes/llm_gateway.py` ফাইলে `get_current_user` ইম্পোর্ট করা হচ্ছিল `core.auth` নামক একটি মডিউল থেকে, যা এই কোডবেসে কখনোই ছিল না। ফলে এটি নীরব 404/ক্র্যাশ ঘটাত।
- **সমাধান:** `api/dependencies.py` থেকে `get_current_user_token` সঠিকভাবে ইম্পোর্ট করার জন্য আপডেট করা হয়েছে।

---

### 📌 Root Cause 4: Health Endpoint Mocking vs Real Contract
- **সমস্যা:** `backend/core/app_builder.py`-এর `/health` এন্ডপয়েন্টে শুধু হার্ডকোডেড `status: healthy` ছিল। এটি আসল Redis ping বা API key কনফিগারেশন চেক করত না।
- **সমাধান:** `app_builder.py`-তে বাস্তবসম্মত Health check বসানো হয়েছে যা Redis সংযোগ এবং startup validator-এর LLM provider keys স্ক্যান করে সঠিক স্ট্যাটাস (ok/degraded) রিটার্ন করে।

---

## 📁 ৩. পরিবর্তিত ফাইলসমূহ (Changed Files List)

| ফাইল | লাইন পরিবর্তন | মূল পরিবর্তন |
| :--- | :--- | :--- |
| `backend/pyproject.toml` | +২৩, -২ | PyTorch & sentence-transformers কে অপশনাল `ml` গ্রুপে নেওয়া হয়েছে এবং বাংলা কমেন্ট যোগ করা হয়েছে। |
| `backend/poetry.lock` | +১৪৪, -১৪৪ | `groups` ফিল্ডে `ml` ট্যাগিং আপডেট এবং lock hash পুনরায় জেনারেট। |
| `backend/core/__init__.py` | +৮৯, -৩৭ | Evolution মডিউলগুলোর জন্য `try/except ImportError` ইম্পোর্ট গার্ড। |
| `backend/evolution/__init__.py` | +৭, -০ | Evolution submodules ইম্পোর্ট গার্ড ও ফেইলসেফ ফলব্যাক। |
| `backend/core/app_builder.py` | +৩৭, -১ | বাস্তবমুখী Redis ও LLM Key Health Check যুক্ত করা হয়েছে। |

---

## 🧪 ৪. ভেরিফিকেশন ও ফলাফল (Verification Status)

1. **ইমেজ সাইজ ও ডিস্ক অপটিমাইজেশন:** `poetry install --with dev` রানারে venv সাইজ **~২.৫ জিবিতে** নেমে এসেছে (পূর্বে পুরো ডিস্ক নিঃশেষ হয়ে যেত)।
2. **লিন্ট ও টাইপ চেক:** `ruff` এবং `py_compile` সম্পূর্ণ ক্লিন।
3. **টেস্ট কভারেজ:** `tests/test_health.py`-এর ৩/৩টি টেস্টই সফলভাবে পাস করেছে।
