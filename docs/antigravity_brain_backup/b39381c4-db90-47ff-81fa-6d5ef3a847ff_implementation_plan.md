# Implementation Plan: Comprehensive Test Suite Fixes (81 Failures)

টিম লিডার, আমাদের সদ্য সমাপ্ত ম্যাসিভ আর্কিটেকচারাল রিফ্যাক্টরিং (CloudSandboxOrchestrator, TaskRouter, BrowserAgent)-এর কারণে ১৮০৯টি টেস্টের মধ্যে ৮১টি টেস্ট ব্রেক করেছে। এটি খুবই স্বাভাবিক কারণ আমরা কোডবেসের কাপলিং (Coupling) ভেঙে নতুন Abstraction Layer তৈরি করেছি। নিচে এগুলো ধাপে ধাপে ফিক্স করার ইমপ্লিমেন্টেশন প্ল্যান দেওয়া হলো:

## 1. TaskRouter & Fallback Fixes (`AttributeError: 'TaskRouter' object has no attribute 'skill_manager'`)
**Root Cause:** আমরা `TaskRouter`-এর কনস্ট্রাক্টর রিরাইট করে `skill_manager` রিমুভ করেছি।
**Action:** 
- `tests/core/test_agent_factory.py` এবং `test_task_router_fallback.py` ফাইলগুলোতে `skill_manager` এর মক বা রেফারেন্স মুছে ফেলা হবে।
- নতুন `route_and_dispatch` মেথডের সাথে সামঞ্জস্য রেখে টেস্টগুলো আপডেট করা হবে।

## 2. Cloud Sandbox & Local Executor Fixes (`AttributeError: 'CloudSandboxOrchestrator' object has no attribute 'run_code'`)
**Root Cause:** `CloudSandboxOrchestrator` থেকে লোকাল কোড এক্সিকিউশন সরিয়ে `LocalCodeExecutor`-এ নেওয়া হয়েছে।
**Action:**
- `tests/test_sandbox_orchestration_run.py`, `test_stealth_networking.py` ইত্যাদি টেস্টগুলোতে `CloudSandboxOrchestrator`-এর পরিবর্তে `LocalCodeExecutor` মক/ইনজেক্ট করা হবে।

## 3. Browser Agent Fixes (`AttributeError: 'BrowserAgent' object has no attribute 'fetch_page'`)
**Root Cause:** BrowserAgent-এর পূর্ববর্তী মেথডগুলো রিফ্যাক্টর করে মুছে ফেলা হয়েছে বা নাম পরিবর্তন করা হয়েছে।
**Action:**
- `tests/test_advanced.py` এবং `tests/test_sprint_c_tools.py` ফাইলে টেস্টগুলো নতুন আর্কিটেকচার অনুযায়ী আপডেট করা হবে (যেমন `fetch_page` এর বদলে নতুন মেথড কল করা)।

## 4. LLM Gateway Mock Fixes (`AttributeError: module core.llm_gateway has no attribute litellm`)
**Root Cause:** `llm_gateway.py` ফাইলে হয়তো `litellm` সরাসরি ইমপোর্ট করা নেই, কিন্তু টেস্ট ফাইলে `mocker.patch("core.llm_gateway.litellm")` ব্যবহার করা হচ্ছে।
**Action:**
- `tests/core/test_core_missing_coverage.py` এবং `tests/test_llm_gateway.py` তে মকিং পাথগুলো (Mock Paths) ঠিক করা হবে।

## 5. Async/Await & Middleware Fixes (e.g. `TypeError: An asyncio.Future ... is required`)
**Root Cause:** `admin/test_god.py` এবং `test_honeypot_middleware.py` তে অ্যাসিনক্রোনাস কল বা মিডলওয়্যার রিটার্ন টাইপে গড়মিল হয়েছে।
**Action:**
- `test_init_db_concurrent` সহ অন্যান্য টেস্টগুলোতে `pytest.mark.asyncio` যুক্ত করা এবং সঠিকভাবে `await` করা নিশ্চিত করা হবে।

## 6. Secure Credential Store Fixes (`TypeError: string indices must be integers`)
**Root Cause:** ডিক্রিপশন বা ডেটা এক্সেসের সময় Tuple/String কে Dict হিসেবে ট্রিট করা হচ্ছে।
**Action:**
- `tests/test_browser_credentials.py` এবং `test_secure_credential_store.py` তে ডেটা পার্সিং লজিক ফিক্স করা হবে।

---

> [!WARNING]
> **User Review Required:** এই টেস্টগুলো ফিক্স করার জন্য কিছু ক্ষেত্রে মূল সোর্স কোডের (যেমন `TaskRouter` বা `BrowserAgent`) মেথড সিগনেচার একটু মডিফাই করতে হতে পারে যাতে ব্যাকওয়ার্ড কম্প্যাটিবিলিটি বজায় থাকে। 

**প্ল্যানটি অ্যাপ্রুভ করলে "Proceed" বাটনে ক্লিক করুন। আমি সাথে সাথে ব্যাচ-বাই-ব্যাচ ফিক্সিং শুরু করব!**
