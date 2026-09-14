# Dual-Channel Zero-Marginal-Cost Execution Engine: Browser Stealth Capabilities & Distributed P2P Worker Grid
**Document:** `docs/plans/features/dual_channel_zero_cost_browser_and_distributed_worker.md`  
**Status:** 🔄 **ACTIVE ARCHITECTURAL SPECIFICATION**  
**Priority:** HIGH (P1)  
**Domain Circle:** Circle C2 (Zero-Cost Computing) + Circle C6 (Browser & Stealth Automation) + Circle C7 (Distributed P2P Grid)  
**Governing Rule:** *AGENTS.md Clause 1 (Rule Hierarchy), Clause 2 (Operational Zero-Gap) & Clause 4 (Zero Magic Boxes)*  
**Origin / Lineage:** Derived from user strategic breakthrough (`আমার একটা মজার বা খারাপ বুদ্ধি মাথায় আস.txt`)

---

## 🎯 1. Executive Summary & Core Paradigm

সুপ্রিম এআই-এর অন্যতম প্রধান সাংবিধানিক দর্শন হলো **Sustainable Near-Zero Compute Cost**। ব্যবহারকারী বা টেন্যান্টের সংখ্যা যখন ১০০ থেকে ১০,০০০ ছাড়িয়ে যাবে, তখন প্রতিটি সাব-টাস্ক ও এআই কোডিং প্রম্পটের জন্য বাণিজ্যিক এপিআই (Claude, OpenAI, Gemini Paid) কল করলে প্ল্যাটফর্মের ইউনিট ইকোনমিক্স ধ্বংস হয়ে যাবে।

এই চ্যালেঞ্জ স্থায়ীভাবে মোকাবিলার জন্য ব্যবহারকারীর উদ্ভাবিত এই আইডিয়াটিকে **২টি কমপ্লিমেন্টারি চ্যানেলে (Two-Way Execution Model)** রূপান্তর করা হয়েছে:

```text
                                USER TASK / PROMPT
                                        │
                         ┌──────────────┴──────────────┐
                         ▼                             ▼
             [WAY 1: BROWSER CAPABILITIES]     [WAY 2: DISTRIBUTED P2P WORKER]
             - In-Built Stealth Automation     - Idle Resource Harvesting
             - Reviewer ➔ Coder Loop           - Zero-Trust Sandboxed Node
             - Anti-Detection & DOM-Strip      - P2P Credit & Incentive Engine
             - Cloudflare / CAPTCHA Bypass     - BYOD (Bring Your Own Device)
                         │                             │
                         └──────────────┬──────────────┘
                                        ▼
                           LOCAL VALIDATION & AST GATE
                           (0-Cost Local Syntax / Linter)
                                        │
                                        ▼
                         SUPREMEAI UNIFIED BRANDED OUTPUT
```

---

## 🌐 2. Way 1: Browser Automation Capabilities (The Stealth Reviewer-Worker Loop)

### 2.1 The Architect-Worker / Critic-Actor Pattern
ব্যবহারকারী যেভাবে ম্যানুয়ালি কোনো এআই (ChatGPT/Claude) থেকে রিভিউ বা ব্লুপ্রিন্ট নিয়ে অন্য কোনো স্পেশালিস্ট এআই (v0/DeepSeek/Qwen) দিয়ে কোড বাস্তবায়ন করান, ব্রাউজার এজেন্ট ঠিক সেই কাজটি হেডলেসলি ও স্বয়ংক্রিয়ভাবে সম্পন্ন করবে:

```text
[Step 1: Architect/Reviewer Session]
   - ইনপুট: ইউজারের গোল বা প্রম্পট
   - টার্গেট: হাই-রিজনিং ওয়েব এআই (Claude Web / ChatGPT Web)
   - আউটপুট: কঠোর আর্কিটেকচার ব্লুপ্রিন্ট ও ইন্টারফেস স্পেক (নো কোড)
              │
              ▼
[Step 2: Coder/Worker Session]
   - ইনপুট: আর্কিটেক্টের ব্লুপ্রিন্ট
   - টার্গেট: কোডিং অপ্টিমাইজড ওয়েব সেশন (v0.dev / Qwen Web / DeepSeek Web)
   - আউটপুট: এক্সিকিউটেবল কোড ইমপ্লিমেন্টেশন
              │
              ▼
[Step 3: Zero-Cost Local Verification]
   - কোনো এআই কল ছাড়াই লোকাল পাইথন AST, Ruff, Biome লিন্টার দিয়ে কোড পরীক্ষা।
   - শতভাগ সিনট্যাক্স সঠিক হলে তবেই রেজাল্ট ইউজারকে ডেলিভারি।
```

### 2.2 Active Codebase Components for Way 1
- **Stealth Browser Engine:** [`backend/tools/browser/browser_stealth.py`](file:///f:/supremeai/backend/tools/browser/browser_stealth.py)  
  - রিয়েলিস্টিক ইউজার-এজেন্ট রোটেশন
  - CSP বাইপাস ও ফিঙ্গারপ্রিন্ট মাস্কিং
  - প্রক্সি রোটেশন সাপোর্ট (`ProxyManager`)
- **Web Fallback Agent:** [`backend/tools/browser/web_fallback_agent.py`](file:///f:/supremeai/backend/tools/browser/web_fallback_agent.py)  
  - অটো-নেভিগেশন, ইনপুট ফিলিং ও ডায়নামিক বাটন ক্লিক।
  - একটি প্ল্যাটফর্ম লিমিটে পৌঁছালে অন্যটিতে ইনস্ট্যান্ট ফলব্যাক।
- **Headless Resource Guard:**  
  - DOM-Strip মোড: পেজের অপ্রয়োজনীয় CSS, ইমেজ বা ট্র্যাকার লোড না করে শুধু টেক্সট স্ট্রিম ফিল্টার করা (মেমরি খরচ ৮০% হ্রাস)।

---

## ⚡ 3. Way 2: Distributed P2P Worker Grid (Idle Resource Harvesting)

### 3.1 The Concept: "Hardware Sharing without Server Burnout"
সেন্ট্রাল সার্ভারে ১০০টি ব্রাউজার কনটেইনার চালালে ৫০+ জিবি র‍্যাম নষ্ট হয় এবং ডাটা সেন্টার আইপি ক্লাউডফ্লেয়ার ব্লকে পড়ে। কিন্তু ব্যবহারকারীদের নিজস্ব ডিভাইসের অলস রিসোর্স (Idle Compute) কাজে লাগালে সার্ভার খরচ শূন্যে নেমে আসে:
- **Zero Central RAM Load:** ভারী ব্রাউজার রেন্ডারিং ইউজারের নিজস্ব পিসির লোকাল র‍্যামে চলবে।
- **Residential IPs:** কোনো ক্লাউডফ্লেয়ার বা ক্যাপচা নেই, কারণ ট্রাফিকের উৎস ইউজারের নিজস্ব বাসাবাড়ি বা অফিসের রেসিডেনসিয়াল আইপি।
- **BYOS (Bring Your Own Session):** ব্যবহারকারী তার লোকাল ব্রাউজারে ইতিমধ্যে যেসব অ্যাকাউন্টে লগইন আছেন, সেগুলো দিয়েই কাজ সম্পন্ন হবে।

### 3.2 Active Codebase Components for Way 2
- **P2P Resource Broker:** [`backend/p2p/resource_broker.py`](file:///f:/supremeai/backend/p2p/resource_broker.py)  
  - নোড রেজিস্ট্রেশন (`register_node`), হার্টবিট মনিটরিং এবং ম্যাচমেকিং।
  - ক্যাপাবিলিটি অনুযায়ী সেরা নোড নির্বাচন (`find_best_node`)।
- **Zero-Trust MicroVM Sandbox:** [`backend/core/microvm_sandbox.py`](file:///f:/supremeai/backend/core/microvm_sandbox.py)  
  - অন্য কোনো পিয়ারের কোড যাতে হোস্ট ডিভাইসের ফাইল সিস্টেমে হাত দিতে না পারে, সেজন্য কঠোর স্যান্ডবক্সিং।
- **P2P Credit & Incentive Engine:** [`backend/p2p/credit_system.py`](file:///f:/supremeai/backend/p2p/credit_system.py)  
  - ব্যবহারকারী তার অলস ডিভাইস দিয়ে যতগুলো টাস্ক প্রসেস করবে, সে অনুপাতে সে SupremeAI প্রো ক্রেডিট বা ফ্রি টোকেন পাবে।

---

## 📱 4. Multi-Device Adaptive Strategy (Desktop vs Mobile)

| ক্ষেত্র | ডেস্কটপ / ল্যাপটপ ইউজার | মোবাইল ওয়েব / অ্যাপ ইউজার |
|---|---|---|
| **এক্সিকিউশন মোড** | **Way 2 (Local P2P Node / Extension)** | **Way 1 (Serverless Stealth Pool or Desktop Companion)** |
| **রিসোর্স চাপ** | ইউজারের ডিভাইসে স্বাভাবিক (অলস সময় কার্যকর) | মোবাইলে ০% মেমরি ও ব্যাটারি চাপ |
| **আইপি প্রোটেকশন** | নিজস্ব রেসিডেনসিয়াল আইপি (১০০% নিরাপদ) | `browser_stealth.py` প্রক্সি রোটেশন পুল |
| **মোবাইল সমাধান** | নোড হিসেবে ক্রেডিট আর্ন করবে | ইউজারের বাসায় থাকা অনলাইন পিসির সাথে P2P পেয়ারিং অথবা লাইটওয়েট সার্ভারলেস ফলব্যাক |

---

## 🔒 5. Brand Identity & Unified Facade (Zero External Leakage)

সংবিধান অনুযায়ী ফ্রন্টএন্ডে ব্যবহারকারী কোনো থার্ড-পার্টি প্ল্যাটফর্ম বা ব্যাকগ্রাউন্ড মেশিনের নাম দেখবে না:
1. **SupremeAI Orchestrator Facade:** ব্যাকগ্রাউন্ডে যাই কাজ করুক, রেসপন্স ফিল্টার হয়ে ইউনিফাইড SupremeAI স্টাইলে আসবে।
2. **Permission First:** ব্যবহারকারী স্পষ্টভাবে সম্মতি দেবেন যে তার ডিভাইস অলস সময়ে (Idle State + Charging + Wi-Fi) কম্পিউট গ্রিডে অংশ নেবে কিনা।
3. **Smart Interruption:** ব্যবহারকারী মাউস বা কীবোর্ডে হাত দেওয়া মাত্র লোকাল ওয়ার্কার সাথে সাথে পজ (Pause) হয়ে মূল ইউজারকে শতভাগ পিসি স্পিড ফিরিয়ে দেবে।

---

## 📅 6. Zero-Gap Integration Action Plan

1. **Circle C2 + C6 Wiring:** `backend/tools/browser/web_fallback_agent.py` এর মধ্যে মাল্টি-এজেন্ট "Reviewer ➔ Coder" লুপ যুক্ত করা।
2. **P2P Broker Activation:** `backend/p2p/resource_broker.py` এর সাথে `backend/api/routes/zero_cost.py` এন্ডপয়েন্ট সংযুক্ত করা।
3. **Frontend Consent UI:** ইউজার সেটিংস পেজে "Contribute Idle Compute & Earn Pro Credits" অপশন দৃশ্যমান করা।
