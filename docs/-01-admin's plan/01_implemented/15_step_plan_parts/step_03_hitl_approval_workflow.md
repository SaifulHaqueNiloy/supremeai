# 📌 Step 3: হিউম্যান-ইন-দ্য-লুপ (HITL) এপ্রুভাল

> **Layer:** 1 — Core Architecture & Security (Foundation & Security)  
> **Status:** Implemented

---

## 📝 বিবরণ

প্রতিটি স্পর্শকাতর কাজ (কোড পুশ, নতুন সাইট ভিজিট, স্কিল জেনারেশন) সম্পন্ন করার আগে ড্যাশবোর্ডে পারমিশন রিকোয়েস্ট ওয়ার্কফ্লো।

---

## 🛠️ আর্কিটেকচারাল কম্পোনেন্ট

- `backend/api/routes/webhooks_ai.py`
- Telegram Interactive Approval Buttons (`Approve PR` / `Reject`)
- JIT OTP verification for sensitive operations (`CPS-003`)
