# 📌 Step 1: পাইপলাইন অপ্টিমাইজেশন (CI/CD Automation)

> **Layer:** 1 — Core Architecture & Security (Foundation & Security)  
> **Status:** Implemented

---

## 📝 বিবরণ

সিআই/সিডি (CI/CD) অটোমেশন এবং গিটহাব অ্যাকশনস-এর মাধ্যমে কোড-টু-ক্লাউড অটো-ডিপ্লয়মেন্ট পাইপলাইন ও এনভায়রনমেন্ট সেটআপ।

---

## 🛠️ আর্কিটেকচারাল কম্পোনেন্ট

- `.github/workflows/monorepo_ci_cd.yml`
- `dorny/paths-filter` দ্বারা চেইঞ্জ ডিটেকশন
- Poetry + pytest (Backend)
- pnpm + turbo (Frontend)
- Google Cloud Run + Firebase Hosting অটো ডিপ্লয়মেন্ট
