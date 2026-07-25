# 📌 Step 14: মডেল রাউটিং

> **Layer:** 4 — System Evolution & Smart Tooling (Evolution)  
> **Status:** Implemented

---

## 📝 বিবরণ

কাজের ধরণ অনুযায়ী লোকাল মডেল (WebLLM/Ollama) এবং এক্সটার্নাল এআই-এর মধ্যে বুদ্ধিমত্তার সাথে সুইচ করা।

---

## 🛠️ আর্কিটেকচারাল কম্পোনেন্ট

- `backend/core/llm_router.py`
- `backend/brain/smart_router.py`
- `backend/brain/expert_router.py`
