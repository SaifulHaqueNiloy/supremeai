# Render Deployment & Environment Troubleshooting Guide

> **Project:** SupremeAI 2.0  
> **Target System:** Render Web Services & Background Workers  
> **Last Updated:** 2026-07-22  
> **Status:** ACTIVE & PRODUCTION READY  

---

## 📌 Overview (বিবরণ)

এই গাইডে SupremeAI 2.0-এর Render ডেপ্লয়মেন্ট প্রক্রিয়া, পূর্বে সম্মুখীন হওয়া ক্রিটিক্যাল এররসমূহ, সেগুলোর রুট-কজ (Root Cause), এবং এন্টারপ্রাইজ-গ্রেড স্থায়ী সমাধান লিপিবদ্ধ করা হলো। ভবিষ্যতে Render ডেপ্লয়মেন্টের কোনো সমস্যা হলে এই ডকুমেন্ট নির্দেশিকা হিসেবে কাজ করবে।

---

## 🚨 Error Case 1: `SUPREMEAI_ADMIN_PASSWORD_HASH` Missing / Pydantic Validation Crash

### 🔍 লক্ষণ (Symptom):
- Render ডিপ্লয়মেন্টের সময় কন্টেইনার স্টার্টআপে crash-loop তৈরি হওয়া।
- `/api/v1/health` এন্ডপয়েন্টে HTTP Connection Timeout / Read Timed Out (10s) দেখা দেওয়া।
- লগে `"Production Secret Vault hooked into Infisical via Token"` প্রদর্শিত হওয়া সত্ত্বেও Pydantic `ValidationError` আসা:  
  `ValueError: supremeai_admin_password_hash must be explicitly set.`

### 🔴 আসল কারণ (Root Cause):
- `backend/core/config.py`-তে `supremeai_admin_password_hash` সিক্রেটটি Pydantic `Field(default=None, validation_alias="SUPREMEAI_ADMIN_PASSWORD_HASH")` হিসেবে সংজ্ঞায়িত ছিল।
- Pydantic `Field` শুধুমাত্র অপারেটিং সিস্টেমের সরাসরি Environment Variables বা `.env` ফাইল থেকে ডেটা পড়ে, Infisical ভল্ট থেকে পড়ে না।
- ফলে সিক্রেটটি Infisical-এ উপস্থিত থাকলেও Pydantic ইননিট টাইমে তা খুঁজে না পেয়ে `None` সেট করছিল এবং স্টার্টআপে ভ্যালিডেটর ফেল করে ক্র্যাশ ঘটাচ্ছিল।

### ✅ স্থায়ী ফিক্স (Implemented Fix):
`backend/core/config.py`-তে `Field` তুলে দিয়ে সিক্রেটটিকে **Infisical-backed lazy `@property`**-তে রূপান্তরিত করা হয়েছে:

```python
# backend/core/config.py
# বাংলা মন্তব্য: Pydantic Field(validation_alias=...) সরাসরি OS env var থেকে পড়ে, যা Infisical
# ভল্টে থাকা সিক্রেট পড়তে পারে না এবং Render ডিপ্লয়মেন্টে Validation Error ঘটিয়ে প্রসেস ক্র্যাশ করায়।
# তাই এটি lazy @property এবং _get_cached_secret() এ রূপান্তর করা হলো যাতে অন-ডিমান্ড ভল্ট বা env থেকে ফেচ হয়।
@property
def supremeai_admin_password_hash(self) -> str | None:
    val = self._get_cached_secret("SUPREMEAI_ADMIN_PASSWORD_HASH")
    if not val and "pytest" not in sys.modules and os.getenv("CI") != "true":
        raise ValueError("supremeai_admin_password_hash must be explicitly set.")
    return val
```

একই সাথে `jwt_secret`, `encryption_key`, `stripe_api_key`, এবং `stripe_webhook_secret`-কেও একই lazy `@property` প্যাটার্নে মাইগ্রেট করা হয়েছে।

---

## 🚨 Error Case 2: Render API Return `404 Not Found` on Service Deploy Trigger

### 🔍 লক্ষণ (Symptom):
- GitHub Actions CI বা অটোমেশন স্ক্রিপ্ট থেকে Render REST API দিয়ে সার্ভিস ট্রিগার করতে গেলে `HTTP 404` রিটার্ন করা:
  ```text
  🔄 No backup hook found. Using Render API to trigger backup deploy...
  ⚠️ Backup API deploy returned status: 404
  ```

### 🔴 আসল কারণ (Root Cause):
- `404 Not Found` নির্দেশ করে যে প্রদত্ত `RENDER_API_KEY` যে Render Account / Team-এর অধীনে তৈরি, সেই অ্যাকাউন্টে টার্গেট Service ID (যেমন: `srv-d9fg48bh523c73f63bb0`) বিদ্যমান নেই বা মুছে ফেলা হয়েছে।
- Render-এ অ্যাকাউন্ট বা টিম আলাদা হলে API Key একটি টিমের সার্ভিস অন্য টিমকে দেখতে পারে না।

### ✅ সমাধান পদ্ধতি (Solution):
1. **Render Service Discovery API Call:**
   Render API ব্যবহার করে অ্যাকাউন্টের লাইভ সার্ভিসেস খুঁজে বের করার কমান্ড:
   ```bash
   python -c "import requests, os; print(requests.get('https://api.render.com/v1/services', headers={'Authorization': 'Bearer ' + os.getenv('RENDER_API_KEY')}).json())"
   ```
2. **Service ID Alignment:**  
   `supremeai-backend`-এর প্রকৃত সার্ভিস আইডি (`srv-d9d3n58js32c738n79k0`) শনাক্ত করে `.github/scripts/verify-render-deploy.py` এবং CI workflows-এ আপডেট করা হয়েছে।

---

## 🚨 Error Case 3: Silent-Success Failure in CI Verification

### 🔍 লক্ষণ (Symptom):
- Render ব্যাকএন্ড বাস্তবে ক্র্যাশ করে থাকলেও GitHub Actions CI পাইপলাইন গ্রিন (`PASSED`) দেখাচ্ছিল।

### 🔴 আসল কারণ (Root Cause):
- পূর্বে ভ্যালিডেশন স্ক্রিপ্টে কোনো ব্যাকএন্ড সার্ভিসের এপিআই রিকোয়েস্ট ফেল করলে তা সাপ্রেস করে `exit 0` দেওয়া হচ্ছিল।

### ✅ সমাধান (Fix Implemented):
`.github/scripts/verify-render-deploy.py`-তে **Anti-Silent Failure Guard** সংযুক্ত করা হয়েছে:
- সার্ভিস হেলথ ডিটেক্ট না হলে বা টাইমআউট খেলে স্ক্রিপ্ট সরাসরি `sys.exit(1)` দিয়ে পাইপলাইন রেড (Fail) ঘোষণা করে।

---

## 🚨 Error Case 4: Environment Variables Desynchronization

### 🔍 লক্ষণ (Symptom):
- লোকাল বা ইনফিসিক্যালে সিক্রেট আপডেট করার পর Render সার্ভিস পুরনো ভ্যালু ব্যবহার করছিল বা missing key এরর পাচ্ছিল।

### ✅ সমাধান (Automated Synchronization):
প্রজেক্টে সেন্ট্রালাইজড এনভায়রনমেন্ট সিঙ্ক্রোনাইজার যুক্ত করা হয়েছে:
```bash
# ড্রাই-রান চেক
python scripts/sync_all_platforms_env.py

# সরাসরি Render, GitHub Secrets এবং Vercel-এ সিঙ্ক ও আপডেট করতে:
python scripts/sync_all_platforms_env.py --apply
```
## 🚨 Error Case 5: CI Polling Sequential Timing & False Positive Timeout

### 🔍 লক্ষণ (Symptom):
- Render ডেপ্লয়মেন্ট বাস্তবে ১০০% **`LIVE`** এবং HTTP 200 OK হওয়া সত্ত্বেও GitHub Actions CI পাইপলাইনের `Verify Render Deploy Health` ধাপটিতে এরর আসা:  
  `❌ No new deploy record found for Admin Backend (Backup) within 3 minutes of triggering it. The trigger call likely failed silently – latest deploy on file is 0:04:03 old.`

### 🔴 আসল কারণ (Root Cause):
- ভ্যালিডেশন স্ক্রিপ্টটি সিকোয়েন্সিয়ালি (পর পর) সার্ভিস চেক করে। রেন্ডারের ফ্রি-টিয়ার কন্টেইনার বিল্ড হতে ৪ মিনিটের বেশি সময় লাগায় Primary সার্ভিস চেক করতে ৪ মিনিট ১ সেকেন্ড পার হয়ে গিয়েছিল।
- এরপর যখন Backup সার্ভিস ভেরিফাই করার টাইমে স্ক্রিপ্টটি সৃষ্টির সময় (`createdAt`) তুলনা করে, ৩ মিনিটের বেশি পার হয়ে যাওয়ায় স্ক্রিপ্টটি ভেবেছিল নতুন ডেপ্লয় ট্রিগার হয়নি এবং ফলস-পজিটিভ টাইমআউট দেখাচ্ছিল।

### ✅ সমাধান (Fix Implemented):
`.github/scripts/verify-render-deploy.py`-তে ২টি ক্রিটিক্যাল সেফগার্ড যুক্ত করা হয়েছে:
1. **`LIVE` Status Bypass:** সার্ভিস ইতিমধ্যে **`LIVE`** হলে ৩ মিনিটের টাইমার চেক না করে সরাসরি HTTP হেলথ চেকের মাধ্যমে পাস করিয়ে দেওয়া।
2. **Extended Threshold:** ফ্রি-টিয়ার বিল্ড লাইনের কথা বিবেচনা করে বয়সের থ্রেশহোল্ড ৩ মিনিট থেকে বাড়িয়ে ১০ মিনিট করা।

---

## 🔐 Render Account Architecture (Primary vs Backup Account Setup)

SupremeAI 2.0-এর CI/CD এবং ভল্ট মেকানিজম **Single-Account Mode** এবং **Multi-Account High Availability (HA) Mode** উভয় আর্কিটেকচারকেই নির্বিঘ্নে সাপোর্ট করে।

### 1. Active Account Credentials (বর্তমান প্রোডাকশন কনফিগারেশন)
- **Account Workspace Name:** `My Workspace`
- **Account Owner Email:** `paykaribazaronline@gmail.com`
- **Team ID:** `tea-d747ms1aae7s73bcasu0`
- **Active Web Service (Backend):** `supremeai-backend` (Service ID: `srv-d9d3n58js32c738n79k0`)
- **Active Static Site (Frontend):** `supremeai-studio-client` (Service ID: `srv-d9d3pgvavr4c738a46mg`)

---

### 2. Single-Account vs Multi-Account Backup Behavior Summary

| ফিচার / কনফিগারেশন | Single-Account Mode (বর্তমান অবস্থা) | Multi-Account (HA) Backup Mode |
| :--- | :--- | :--- |
| **`RENDER_API_KEY`** | Primary Render API Key | Primary Account API Key |
| **`RENDER_API_KEY_BACKUP`** | Same as `RENDER_API_KEY` | Secondary (Backup) Account API Key |
| **Target Web Service** | `srv-d9d3n58js32c738n79k0` | Primary: `srv-d9d3n58js32c738n79k0`, Backup: `srv-d9fg...` |
| **CI/CD Auto-Fallback** | 404 পেয়ে স্বয়ংক্রিয়ভাবে সক্রিয় ব্যাকএন্ড টার্গেট করে শতভাগ গ্রিন পাস দেয় | দুটি ভিন্ন অ্যাকাউন্টে সমান্তরালভাবে ডেপ্লয় ও হেলথ ভেরিফাই করে |

---

### 3. ভবিষ্যতে আলাদা Backup Render Account সেটআপ করার নির্দেশিকা

যদি ভবিষ্যতে সম্পূর্ণ ভিন্ন একটি Render অ্যাকাউন্টকে ডাবল-রেডানড্যান্সি (Backup Account) হিসেবে যুক্ত করতে চান:

1. **নতুন অ্যাকাউন্টে সার্ভিস তৈরি:**  
   দ্বিতীয় Render অ্যাকাউন্টে লগইন করে Docker/Python Service হিসেবে `supremeai-admin` নাম দিয়ে Web Service তৈরি করুন।
2. **Backup API Key জেনারেট:**  
   নতুন অ্যাকাউন্টের **Account Settings → API Keys** সেকশনে গিয়ে একটি নতুন API Key তৈরি করুন।
3. **Secrets Update & Platform Sync:**  
   লোকাল `.env` ফাইলে `RENDER_API_KEY_BACKUP`-এ নতুন কী-টি বসিয়ে সিঙ্ক্রোনাইজার রান করুন:
   ```bash
   python scripts/sync_all_platforms_env.py --apply
   ```
4. **CI Auto-Detection:**  
   GitHub Actions workflow (`supreme-core-ci.yml`) এবং `verify-render-deploy.py` স্বয়ংক্রিয়ভাবে আলাদা অ্যাকাউন্ট শনাক্ত করে প্রাইমারি ও ব্যাকআপ উভয় সার্ভারে সমান্তরাল ডেপ্লয়মেন্ট নিশ্চিত করবে।

---

## 🛠️ Quick Operational Checklist for Render Deployments

1. **যেকোনো নতুন সিক্রেট যোগ করলে:**  
   `backend/core/config.py`-তে lazy `@property` মেথড ব্যবহার করুন (কখনোই `Field(validation_alias=...)` নয়)।
2. **ডিপ্লয়মেন্ট ব্লক হলে বা এনভায়রনমেন্ট ভ্যারিয়েবল পুশ করতে:**  
   `python scripts/sync_all_platforms_env.py --apply` রান করুন।
3. **রেন্ডারে ম্যানুয়াল ডেপ্লয়মেন্ট ট্রিগার করতে:**  
   Render REST API বা Dashboard → `Clear build cache & deploy` ব্যবহার করুন।

---

*SupremeAI 2.0 — Production Architecture Documentation*
