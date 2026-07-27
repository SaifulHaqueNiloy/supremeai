# ✅ PHASE 4: আর্কিটেকচারাল ইমপ্রুভমেন্ট — এক্সিকিউশন ট্র্যাকার

**স্ট্যাটাস:** 🔄 চলমান  
**শেষ আপডেট:** ২০২৬-০৭-২৬

---

## 🎯 টাস্ক ১: কনফিগ লেয়ার রিফ্যাক্টরিং
**ফাইল:** `backend/core/config.py` → `backend/core/config/` (নতুন ডিরেক্টরি)  
**স্ট্যাটাস:** ⬜ পেন্ডিং  

`backend/core/config.py` (250+ লাইন) → সাব-কনফিগ মডিউলে ভাগ করা:

- [ ] `backend/core/config/constants.py` — Constants & Enums (ম্যাজিক নম্বর এলিমিনেশন)
- [ ] `backend/core/config/database.py` — DatabaseConfig
- [ ] `backend/core/config/security.py` — SecurityConfig
- [ ] `backend/core/config/llm.py` — LLMConfig
- [ ] `backend/core/config/cache.py` — CacheConfig
- [ ] `backend/core/config/deployment.py` — DeploymentConfig
- [ ] `backend/core/config/__init__.py` — Settings class (মূল ক্লাস)
- [ ] `backend/core/config.py` — ব্যাকওয়ার্ড কম্প্যাটিবল রিডাইরেক্ট

**ইমপ্যাক্ট:** কোড ক্লিনলিনেস ৬০% বাড়বে, কনফিগ অর্গানাইজেশন সহজ হবে

---

## 🎯 টাস্ক ২: ইম্পোর্ট অপটিমাইজেশন সম্পূর্ণ করা
**ফাইল:** পুরো কোডবেস  
**স্ট্যাটাস:** ⬜ আংশিক সম্পন্ন (app_builder.py ✅)  

- [ ] `TYPE_CHECKING` ব্লক যোগ করা — সার্কুলার ইম্পোর্ট প্রতিরোধ
- [ ] `from __future__ import annotations` — সকল ফাইলে
- [ ] লেজি ইম্পোর্ট — heavy modules (LLM, Cache, DB)
- [ ] সার্কুলার ইম্পোর্ট ডিটেকশন + ফিক্স

**ইমপ্যাক্ট:** কোল্ড স্টার্ট ২০-৪০% দ্রুত হবে, ইম্পোর্ট এরর কমবে

---

## 🎯 টাস্ক ৩: ইভেন্ট বাস এনহ্যান্সমেন্ট
**ফাইল:** `backend/core/messaging/event_bus.py`  
**স্ট্যাটাস:** ⬜ পেন্ডিং  

- [ ] ডেড লেটার কিউ (DLQ) — failed events এর জন্য
- [ ] ইভেন্ট রিট্রি মেকানিজম (exponential backoff)
- [ ] ইভেন্ট সোর্সিং প্যাটার্ন — state reconstruction
- [ ] ইভেন্ট ভ্যালিডেশন স্কিমা

**ইমপ্যাক্ট:** সিস্টেম রিলায়েবিলিটি বাড়বে, ডাটা কনসিস্টেন্সি নিশ্চিত হবে

---

## ✅ অগ্রগতি সারসংক্ষেপ

| টাস্ক | স্ট্যাটাস | অগ্রগতি |
|-------|-----------|---------|
| ১. কনফিগ লেয়ার রিফ্যাক্টরিং | ⬜ পেন্ডিং | ০% |
| ২. ইম্পোর্ট অপটিমাইজেশন | ⬜ আংশিক | ২০% |
| ৩. ইভেন্ট বাস এনহ্যান্সমেন্ট | ⬜ পেন্ডিং | ০% |
| **মোট** | **—** | **~৭%** |
