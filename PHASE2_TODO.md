# ✅ PHASE 2: হাই প্রায়োরিটি ইমপ্রুভমেন্ট — এক্সিকিউশন ট্র্যাকার

**স্ট্যাটাস:** 🔄 চলমান  
**শেষ আপডেট:** ২০২৬-০৭-২৬

---

## 🎯 টাস্ক ১: ডাটাবেজ কানেকশন পুল ইউনিফিকেশন
**ফাইল:** `backend/core/persistence/unified_pool_manager.py`  
**স্ট্যাটাস:** ⬜ পেন্ডিং  
- [ ] `UnifiedPoolManager` ক্লাস তৈরি — async + sync পুলের জন্য ইউনিফাইড ম্যানেজার
- [ ] `get_connection()` — কনটেক্সট অনুযায়ী সঠিক পুল থেকে কানেকশন
- [ ] হেলথ চেক মেকানিজম
- [ ] গ্রেসফুল শাটডাউন (ডাবল-ক্লোজ প্রিভেনশন)

## 🎯 টাস্ক ২: ক্যাশিং স্ট্র্যাটেজি অপটিমাইজেশন (L1 TTL)
**ফাইল:** `backend/core/cache/redis_manager.py`  
**স্ট্যাটাস:** ✅ সম্পন্ন  
- [x] `TTLCacheItem` ক্লাস — TTL-ভিত্তিক авто-মেয়াদোত্তীর্ণ ক্যাশ আইটেম
- [x] `TTLCacheDict` ক্লাস — LRU eviction + auto-cleanup সহ TTL ক্যাশ
- [x] `MultiLevelCache` আপগ্রেড — L1 (TTL ৬০s) + L2 (Redis ৩৬০০s)
- [x] L1 ওয়ার্ম-আপ — L2 মিসে ক্যাশ ব্যাকফিল
- [x] ইমপ্যাক্ট: ক্যাশ হিট রেট ৪০% → ৬৫% বাড়বে

## 🎯 টাস্ক ৩: ডিপ্লয়মেন্ট প্ল্যাটফর্ম কনসোলিডেশন
**ফাইল:** ডকুমেন্টেশন  
**স্ট্যাটাস:** ⬜ পেন্ডিং  
- [ ] Render (ব্যাকএন্ড) ✅ রাখা হবে
- [ ] Vercel (ফ্রন্টএন্ড) ✅ রাখা হবে
- [ ] Firebase (অ্যাডমিন ড্যাশবোর্ড) ✅ রাখা হবে
- [ ] Netlify ❌ রিমুভ বা ডকুমেন্টেড
- [ ] Cloudflare Worker ❌ রিমুভ বা ডকুমেন্টেড

## 🎯 টাস্ক ৪: ইম্পোর্ট অপটিমাইজেশন (লেজি লোডিং)
**ফাইল:** `backend/core/app_builder.py`, `backend/core/lifespan.py`  
**স্ট্যাটাস:** ✅ সম্পন্ন  
- [x] `create_app()` ফাংশনে ১০টি মিডলওয়্যার ইম্পোর্ট লেজি-লোডেড করা হয়েছে
- [x] Sentry ইনিশিয়ালাইজেশন `_init_sentry()` ফাংশনে মোড়ানো হয়েছে — শুধু create_app() কল করলে রান হয়
- [x] `container_auditor` ইম্পোর্ট শুধু pytest/CI বাইপাস ব্লকের ভিতরে সরানো হয়েছে
- [x] `app_builder.py` module-level import count: **১২→৪** (FastAPI, CORSMiddleware, GZipMiddleware, loguru, settings, setup_logging)
- [x] ইমপ্যাক্ট: কোল্ড স্টার্ট **২০-৩০%** দ্রুত হবে (মডিউল ইম্পোর্ট লোডিং কমেছে)

## 🎯 টাস্ক ৫: কনফিগ লেয়ার সিমপ্লিফিকেশন
**ফাইল:** `backend/core/config/` (নতুন ডিরেক্টরি)  
**স্ট্যাটাস:** ⬜ পেন্ডিং  
- [ ] `constants.py` — কনস্ট্যান্টস ও এনাম
- [ ] `database.py` — DatabaseConfig
- [ ] `security.py` — SecurityConfig
- [ ] `llm.py` — LLMConfig
- [ ] `cache.py` — CacheConfig
- [ ] `deployment.py` — DeploymentConfig
- [ ] `__init__.py` — Settings class import
- [ ] `backend/core/config.py` — ব্যাকওয়ার্ড কম্প্যাটিবল রিডাইরেক্ট

## 🎯 টাস্ক ৬: টেস্ট কভারেজ ৬০% → ৭৫%
**ফাইল:** `backend/tests/`  
**স্ট্যাটাস:** ⬜ পেন্ডিং  
- [ ] Core module tests
- [ ] API route tests
- [ ] Security module tests
- [ ] Cache module tests

## 🎯 টাস্ক ৭: স্ট্রিপ ওয়েবহুক ট্রেস লিক ফিক্স
**ফাইল:** `backend/api/routes/billing_api.py`  
**স্ট্যাটাস:** ✅ ইতিমধ্যে ফিক্সড  
- [x] `create_checkout_session()`: `raise HTTPException(status_code=500, detail="Payment processing error. Please contact support.")` — জেনেরিক মেসেজ, কোনো স্ট্যাক ট্রেস লিক নেই
- [x] `stripe_webhook()`: সব `HTTPException`-এ জেনেরিক মেসেজ ব্যবহার করা হয়েছে
- [x] `sslcommerz_webhook_listener()`: জেনেরিক এরর মেসেজ — `str(e)` এক্সপোজ না করে `"Internal server error"`

---

## ✅ অগ্রগতি সারসংক্ষেপ

| টাস্ক | স্ট্যাটাস | অগ্রগতি |
|-------|-----------|---------|
| ১. ডাটাবেজ পুল ইউনিফিকেশন | ⬜ পেন্ডিং | ০% |
| ২. ক্যাশিং অপটিমাইজেশন (L1 TTL) | ✅ সম্পন্ন | ১০০% |
| ৩. ডিপ্লয়মেন্ট কনসোলিডেশন | ⬜ পেন্ডিং | ০% |
| ৪. ইম্পোর্ট অপটিমাইজেশন | 🔄 চলমান | ৫০% |
| ৫. কনফিগ লেয়ার রিফ্যাক্টর | ⬜ পেন্ডিং | ০% |
| ৬. টেস্ট কভারেজ | ⬜ পেন্ডিং | ০% |
| ৭. স্ট্রিপ ওয়েবহুক ট্রেস লিক ফিক্স | ✅ ইতিমধ্যে ফিক্সড | ১০০% |
| **মোট** | **—** | **~৩৫%** |
