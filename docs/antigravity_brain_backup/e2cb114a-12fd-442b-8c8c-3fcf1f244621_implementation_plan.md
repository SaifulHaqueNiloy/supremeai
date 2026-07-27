# GitHub Repository Clean-Up Plan

আমি ইতিমধ্যেই আপনার নতুন "ZTO Master Plan"-এর সমস্ত চেঞ্জ লোকাল গিট-এ কমিট করে ফেলেছি। এখন আপনি চাচ্ছেন এগুলো পুশ করতে এবং গিটহাবের ১৩৮টি অতিরিক্ত ব্রাঞ্চ মুছে ফেলে শুধু প্রয়োজনীয়গুলো রাখতে।

যেহেতু গিটহাব থেকে সরাসরি ব্রাঞ্চ মুছে ফেলা একটি বড় এবং ধ্বংসাত্মক (destructive) কাজ, তাই একটি ফর্মাল ব্লুপ্রিন্ট ও আপনার পারমিশন দরকার।

## User Review Required
> [!CAUTION]
> আমরা গিটহাব API ব্যবহার করে রিমোট থেকে ১৩০+ ব্রাঞ্চ চিরস্থায়ীভাবে ডিলিট করব। দয়া করে নিচের "Branch Keep List" টি দেখে নিশ্চিত করুন যে আপনার দরকারি কোনো ব্রাঞ্চ বাদ পড়ছে না তো!

## Proposed Changes

### 1. Push Core Changes
আমি লোকাল কমিটটি (`feat: complete Master Plan ZTO - DAG Orchestrator, Guardian and Reflection integration`) গিটহাবের `main` ব্রাঞ্চে পুশ করব।

### 2. Github Branch Cleanup Script
আমি `scripts/clean_github_branches.py` নামে একটি পাইথন স্ক্রিপ্ট লিখব যা:
- আপনার `.env` ফাইলের `GITHUB_TOKEN` বা `GITHUB_PAT_AUTO_FIX` ব্যবহার করবে।
- `paykaribazaronline/supremeai` রিপোজিটরি থেকে সব ব্রাঞ্চ ফেচ (fetch) করবে।
- **Branch Keep List (যেগুলো ডিলিট হবে না):** `main`, `master`, `develop` (বা আপনার বলা স্পেসিফিক কোনো নাম)।
- বাকি সব অতিরিক্ত (stale/feature/bugfix) ব্রাঞ্চ API-এর মাধ্যমে ডিলিট করে দেবে।

## Open Questions
> [!IMPORTANT]
> ১. `main` এবং `develop` বাদে আর কোনো নির্দিষ্ট ব্রাঞ্চ (যেমন: `staging`, `production`) কি সেভ করে রাখতে হবে?
> ২. `.env` ফাইলে `GITHUB_TOKEN`, `GITHUB_PAT_AUTO_FIX`, এবং `GITHUB_PAT_NILOYJOY7` আছে। আমি কি `GITHUB_PAT_AUTO_FIX` ব্যবহার করব?

## Verification Plan
- স্ক্রিপ্টটি প্রথমে একটি "Dry Run" করবে (অর্থাৎ ডিলিট না করে শুধু দেখাবে কোন কোন ব্রাঞ্চ ডিলিট হতে যাচ্ছে)।
- আপনি কনফার্ম করলে আমি ফাইনাল রান দিয়ে গিটহাব ক্লিন করে দেব।
