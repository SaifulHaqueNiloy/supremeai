# Sentinel Agent Implementation Plan

আপনার ডাটাবেস প্রস্তুত, এখন আমাদের "Sentinel Agent" ইমপ্লিমেন্ট করার পালা। এই এজেন্টটি ডাটাবেস মনিটর করবে, এরর অ্যানালাইজ করবে এবং অটোমেটিক হিলিং লজিক ট্রিগার করবে।

## Architecture Decision (FastAPI BackgroundTasks vs Celery)

> [!TIP]
> **Recommendation: Hybrid approach using Native Asyncio & FastAPI BackgroundTasks.**
>
> **কেন Celery নয়?** SupremeAI 2.0-এর লক্ষ্য "Zero-cost operation"। Celery ব্যবহার করলে আমাদের আলাদা Worker Process এবং Redis/RabbitMQ মেসেজ ব্রোকার রান রাখতে হবে, যা ক্লাউডে অতিরিক্ত খরচ বাড়াবে। 
> **কেন FastAPI?** FastAPI-এর ভেতরে `asyncio` লুপ এবং `BackgroundTasks` ব্যবহার করলে একই কন্টেইনারে কোনো অতিরিক্ত রিসোর্স ছাড়াই আমরা এজেন্ট রান করতে পারব। 

## Mode of Operation: Hybrid (Event-Driven + Periodic)

আমরা একটি **Hybrid Model** ব্যবহার করব, যা দুটি মোডেই কাজ করবে:
1. **Periodic (Time-Driven):** `asyncio` লুপ ব্যবহার করে প্রতি ৫ মিনিট পর পর `ApiEndpoint` এবং `SystemDependency` চেক করবে।
2. **Event-Driven (Trigger-Based):** কোনো রিকোয়েস্টে এরর বা ল্যাটেন্সি হলে FastAPI Middleware থেকে সরাসরি `BackgroundTasks`-এর মাধ্যমে ইমিডিয়েট ইনভেস্টিগেশন ট্রিগার করবে।

## Proposed Changes

### 1. Core Logic [NEW]
#### [NEW] [sentinel_agent.py](file:///c:/Users/n/supremeai/supremeai_2.0/backend/core/sentinel_agent.py)
- **Observation**: `monitor_endpoints()` এবং `check_dependencies()` ফাংশন তৈরি।
- **Analysis**: ল্যাটেন্সি বা ভার্সন ড্রিফট ডিটেক্ট করে `SystemIncident` টেবিলে লগ করা।
- **Action**: ক্রিটিক্যাল এরর হলে `auto_remediate()` লজিক ট্রিগার করা।

### 2. Lifespan Integration [MODIFY]
#### [MODIFY] [main.py](file:///c:/Users/n/supremeai/supremeai_2.0/backend/main.py)
- FastAPI-এর `lifespan` ইভেন্টে `asyncio.create_task()` এর মাধ্যমে Sentinel Agent-এর Periodic Loop অ্যাড করা।

### 3. Middleware Trigger [MODIFY]
#### [MODIFY] [middleware.py](file:///c:/Users/n/supremeai/supremeai_2.0/backend/core/middleware.py) (if exists, or in main.py)
- `dispatch` মেথডে `BackgroundTasks` অ্যাড করা, যাতে 500 ইন্টার্নাল এরর বা স্লো রেসপন্স হলে ইভেন্ট-ড্রিভেন মোডে Sentinel Agent কল হয়।

---

## User Review Required

> [!IMPORTANT]
> **আপনার মতামত প্রয়োজন:**
> ১. আমরা কি `Zero-cost` মেইনটেইন করার জন্য `Celery`-এর বদলে সম্পূর্ণ `FastAPI Native` (Asyncio) লুপ ব্যবহার করে এগোবো? 
> ২. Periodic চেকগুলো কি প্রতি ৫ মিনিটে রান করব, নাকি আরও বেশি/কম ইন্টারভ্যালে? 

প্ল্যানটি অ্যাপ্রুভ করলে আমি এজেন্ট কোডিং শুরু করব।
