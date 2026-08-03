# 🚀 GitHub Action CI/CD টেস্ট ফেইলিয়ুর বিশ্লেষণ ও সমাধান কর্মপরিকল্পনা (Work Plan)

**তারিখ:** ২ আগস্ট, ২০২৬  
**রান আইডি (Run ID):** `30712804379`  
**ওয়ার্কফ্লো:** `🧠 SupremeAI Core CI`  
**স্ট্যাটাস:** ❌ FAILED (`🐍 Backend (Test)` জব)

---

## 📌 ১. মূল সমস্যা সংক্ষেপ (Executive Summary)

সর্বশেষ GitHub Action পেজিনেটিং টেস্ট সেশনে `🐍 Backend (Test)` জবে বেশ কিছু টেস্ট কেস ফেইল করেছে। মূলত ব্যাকএন্ড টেস্ট স্যুটের ৩টি প্রধান মডিউলে (Core Health Checker, Core Config Settings এবং Config API Routes) মেথড সিগনেচার পরিবর্তন এবং মকিং অসঙ্গতির কারণে এই ফেইলিয়ুরগুলো ঘটেছে।

---

## 🔍 ২. চিহ্নিত ত্রুটিসমূহ (Identified Test Failures)

### ২.১ `tests/test_core_health_check.py`
- **ত্রুটি ১:** `AttributeError: ComprehensiveHealthChecker object does not have attribute '_check_database_internal'`
  - **কারণ:** `ComprehensiveHealthChecker` ক্লাসে `_check_database_internal` প্রাইভেট মেথডের নাম পরিবর্তন বা রিফ্যাক্টরিং করা হলেও টেস্ট স্যুটে পুরনো মেথড প্রাইভেট নেম মোশন দিয়ে মক করা হচ্ছে।
- **ত্রুটি ২:** HealthStatus মকিং এসারশন অমিল (`HEALTHY` vs `DEGRADED` / `UNHEALTHY`)
  - **কারণ:** `test_check_external_services_some_missing`, `test_check_external_services_exception`, এবং `test_check_all_with_exception` টেস্টগুলিতে সেটিংস বা সার্ভিসের এরর সাপ্রেস হয়ে সবসময় ডিফল্ট `HEALTHY` স্টেট রিটার্ন করছে।

### ২.২ `tests/test_core_config.py`
- **ত্রুটিসমূহ:**
  - `test_settings_production_complete_validation`
  - `test_settings_encryption_key_not_empty`
  - `test_settings_stripe_configuration`
  - `test_settings_ci_webhook_secret`
  - `test_settings_redis_url`
  - `test_settings_gemini_api_key`
  - `test_settings_openrouter_api_key`
  - `test_settings_supabase_configuration`
- **কারণ:** প্রোডাকশন সেটিংস ভ্যালিডেশন এবং এনভায়রনমেন্ট ভ্যারিয়েবল চেকিং মেকানিজম আপডেট করার পর টেস্ট টেস্ট কেসগুলির মক ভ্যালু কারেন্ট ভ্যালিডেশন স্কিমার সাথে মিলছে না।

### ২.৩ `tests/test_api_config_routes.py`
- **ত্রুটিসমূহ:**
  - `test_get_config_by_key_success`
  - `test_get_config_by_key_not_found`
  - `test_update_config_by_key_success`
  - `test_update_config_by_key_with_various_types`
  - `test_get_config_by_key_special_characters`
  - `test_update_config_by_key_special_characters`
- **কারণ:** রাউটের প্রটেকশন ডিপেনডেন্সি ও রিপোজিটরি মকিং অবজেক্টের রেসপন্স ফরম্যাটের সাথে মিল না থাকা।

### ২.৪ `tests/test_jit_otp.py` & `tests/test_simulator.py`
- **ত্রুটিসমূহ:**
  - `test_partial_match_same_subnet_is_caution_not_otp`
  - `test_partial_match_same_user_agent_is_caution_not_otp`
  - `test_simulator_profile_endpoints`
  - `test_simulator_install_uninstall`
- **কারণ:** JIT OTP ট্র্যাকিং লজিক এবং সিমুলেটর এপিআই রাউট আপডেট হওয়ার ফলে এসারশন স্টেট ফেইল করছে।

---

## 🛠️ ৩. সমাধান ও বাস্তবায়ন ধাপ (Action Steps & Implementation Plan)

### 🔹 ধাপ ১: `ComprehensiveHealthChecker` টেস্ট ফিক্স
- `backend/core/health_check.py` এর ফিল্ড ও মেথড স্ট্রাকচার অনুযায়ী `test_core_health_check.py`-এ সঠিক মেথড নেম মক করা।
- এক্সসেপশন হ্যান্ডলিং কেসে `HealthStatus.UNHEALTHY` এবং `HealthStatus.DEGRADED` প্রপারলি প্রডিউস ও এসার্ট করা।

### 🔹 ধাপ ২: `test_core_config.py` সেটিংস এসারশন আপডেট
- `Settings` স্কিমার সাম্প্রতিক ফিল্ড রিকোয়ারমেন্ট অনুযায়ী এনভায়রনমেন্ট ভ্যারিয়েবল মক প্যাচ হালনাগাদ করা।

### 🔹 ধাপ ৩: `test_api_config_routes.py` ডিপেনডেন্সি মকিং ঠিক করা
- রাউট লেভেলে এডমিন অথেনটিকেশন ও ডিপেনডেন্সি ইনজেকশন ওভাররাইড চেক করে সঠিক HTTP স্ট্যাটাস কোড (200 / 404) এসার্ট করা।

### 🔹 ধাপ ৪: JIT OTP ও Simulator টেস্ট হালনাগাদ
- সিকিউরিটি স্কোরের ট্র্যাকিং থ্রেশহোল্ড অনুযায়ী টেস্ট ডাটা অ্যাডজাস্ট করা।

### 🔹 ধাপ ৫: লোকাল টেস্টিং ও ভ্যালিডেশন
- `pytest` দিয়ে লোকালি টেস্ট রান করে সব টেস্ট পাস নিশ্চিত করা।
- রফ (Ruff) টাইপচেক ও স্ক্যান সফল করা।

---

## 🎯 ৪. প্রত্যাশিত ফলাফল (Target Outcome)
- **CI Build:** `🧠 SupremeAI Core CI` ওয়ার্কফ্লো ১০০% সবুজ (Passed)।
- **Test Coverage:** ব্যাকএন্ড টেস্ট কভারেজ কোটা বজায় রাখা।
- **Zero Breakage:** কোন বিদ্যমান প্রোডাকশন কোড বা মডিউল যাতে ভেঙে না পড়ে।
