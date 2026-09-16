# ইমপ্লিমেন্টেশন প্ল্যান: ডাইনামিক কনট্রোল প্লেন (Zero-Hardcoded Runtime Configuration)

> **কোর আর্কিটেকচারাল গোল্ডেন রুল:**  
> *"DB controls policy, code protects invariants."*  
> সিকিউরিটি বাউন্ডারি, ক্রিপ্টোগ্রাফিক প্রিমিটিভস, ডিবি স্কিমা ও হার্ড সেফটি লিমিট কোডে অপরিবর্তনীয় (Immutable) থাকবে; কিন্তু সমস্ত অপারেশনাল পলিসি, মডেল অর্কেস্ট্রেশন, রেট লিমিট, ফিচার ফ্ল্যাগ এবং বিজনেস প্ল্যান ড্যাশবোর্ড থেকে ডাইনামিক ও লাইভ নিয়ন্ত্রিত হবে।

---

## 🏗️ হাই-লেভেল সিস্টেম আর্কিটেকচার

```mermaid
graph TD
    UI[অ্যাডমিন ড্যাশবোর্ড / Universal Config UI] -->|Admin Config API| API[/admin-api/config/*]
    API -->|Validation & Audit| ControlPlane[Config Control Plane]
    ControlPlane -->|Write with Version++| DB[(PostgreSQL: SystemConfig & Audit Logs)]
    ControlPlane -->|Publish ConfigChanged Event| PubSub[Redis Pub/Sub & Invalidation]
    PubSub --> NodeA[Backend Instance A]
    PubSub --> NodeB[Backend Instance B]
    PubSub --> Worker[Worker Nodes]
    
    CustomerUI[Frontend Client / User Profile] -->|Public API| PublicEndpoints[/api/config/public & /api/v1/models]
    PublicEndpoints --> ConfigSvc[ConfigService Layer]
    ConfigSvc --> L1[L1: Redis Cache]
    L1 -.->|Miss| L2[L2: PostgreSQL DB]
    L2 -.->|DB Down| L3[L3: Last Known Good Snapshot]
    L3 -.->|Failure| L4[L4: Immutable Code Default]
```

---

## 📋 প্রস্তাবিত ফেজসমূহ (Phase 0 – Phase 9)

### Phase 0: Hardcoded Configuration Census (পূর্ণাঙ্গ সেন্সাস ও শ্রেণিবিন্যাস)
- পুরো কোডবেস (`backend/`, `frontend/`, `workers/`, `scripts/`) স্ক্যান করে কনফিগারেশনগুলোর সুনির্দিষ্ট শ্রেণিবিন্যাস করা:
  1. **Runtime & Feature Config** ➔ DB-তে স্থানান্তরযোগ্য (`maxConcurrency`, `features`, `maintenance_mode`)
  2. **AI & Model Orchestration** ➔ Model Registry / DB-তে স্থানান্তরযোগ্য (মডেল রাউটিং, কোটা, ক্যাটালগ)
  3. **Business & Billing** ➔ সাবস্ক্রিপশন ও প্রাইসিং টেবিলে স্থানান্তরযোগ্য
  4. **Immutable Invariants & Safety Bounds** ➔ কোডে সুরক্ষিত থাকবে (JWT algorithm, DB migrations, Hard max caps)

---

### Phase 1: Config Control Plane Foundation & Schema Registry
- **Config Schema Registry তৈরি**: প্রতিটি ডাইনামিক কী-এর জন্য ডেটাটাইপ, রেঞ্জ (`min`/`max`), `allowed_values`, `restart_required` এবং `description` নির্দিষ্ট করা।
- **L1–L4 মাল্টি-টায়ার রেজিলিয়েন্স**:
  - `L1`: Redis Cache (ultra-fast)
  - `L2`: PostgreSQL DB (`system_config` table)
  - `L3`: Last Known Good Snapshot (in-memory / persistent disk snapshot)
  - `L4`: Immutable Code Safe Defaults (কখনই ব্ল্যাকআউট হবে না)
- **রিয়েল-টাইম মাল্টি-ইনস্ট্যান্স ইনভ্যালিডেশন**: Redis Pub/Sub ইভেন্ট (`config:changed`) পাঠিয়ে ক্লাউডের একাধিক ব্যাকএন্ড ইনস্ট্যান্সের লোকাল ক্যাশ একই সাথে ফ্ল্যাশ করা।

---

### Phase 2: Granular Dynamic Public Configuration
- `public_config.py` এক ঢালাও অবজেক্টের বদলে সুনির্দিষ্ট নেইমস্পেস ভিত্তিক করা:
  - `runtime.max_concurrency`
  - `feature.self_healing`
  - `feature.cost_guard`
  - `system.maintenance_mode`
- `/api/config/public` যাতে কোনো কোড ডেপ্লয়মেন্ট ছাড়াই ড্যাশবোর্ড থেকে তাৎক্ষণিক নতুন ফিচার ফ্ল্যাগ ও পাবলিক সেটিংস পরিবেশন করতে পারে।

---

### Phase 3: Dynamic Model Registry & Lifecycle Engine
- **Branding বনাম Model Registry পৃথকীকরণ**:
  - `Branding API` (`branding.py`): শুধু ডিসপ্লে লেবেল ও ফ্যামিলি উপস্থাপন করবে (যেমন: `SupremeAI Deep`)।
  - `Model Registry Engine`: মডেলের প্রযুক্তিগত বৈশিষ্ট্য, স্ট্যাটাস ও লাইফসাইকেল কন্ট্রোল করবে (`enabled`, `selectable`, `routing_enabled`, `cost_weight`, `context_window`, `rollout_percentage`)।
- **ফ্রন্টএন্ডের স্ট্যাটিক অপশন উচ্ছেদ**:
  - `ProfilePage.tsx` এবং `commandRegistry.ts`-এর ফিক্সড মডেল ড্রপডাউন বাদ দিয়ে সরাসরি ডাইনামিক মডেল ক্যাটালগ এপিআই কনজিউম করা।

---

### Phase 4: Schema-Driven Universal Admin Config Editor
- `ConfigEditor.tsx` কে রিফ্যাক্টর করে **স্কিমা-চালিত স্বয়ংক্রিয় ইউআই** তৈরি করা:
  - `boolean` ➔ টগল সুইচ (Toggle Switch)
  - `integer` / `float` ➔ রেঞ্জ ভ্যালিডেশন সহ নাম্বার ইনপুট
  - `enum` ➔ ড্রপডাউন সিলেক্ট
  - `json` ➔ কোড এডিটর / কী-ভ্যালু পেয়ার
- নতুন কোনো কনফিগারেশন যোগ করলে ফ্রন্টএন্ডে আর একটি লাইনও কোড লিখতে হবে না; শুধু ব্যাকএন্ড স্কিমায় যোগ করলেই ফ্রন্টএন্ড স্বয়ংক্রিয়ভাবে ইনপুট ফিল্ড রেন্ডার করবে।

---

### Phase 5: Dynamic Billing & Subscription Plans
- `billing_plans.py`-এর পাইথন স্ট্যাটিক ডিকশনারি রিপ্লেস করে বিজনেস-এনটিটি ডাটাবেস টেবিল (`subscription_plans` ও `plan_features`) তৈরি।
- পেমেন্ট প্রোভাইডার অবজেক্ট আইডি (`price_id`) ভ্যালিডেশন লেয়ার নিশ্চিত করা, যাতে ড্যাশবোর্ড থেকে ভুল প্রাইস আইডি বসালে পেমেন্ট গেটওয়ে ক্র্যাশ না করে।
- `/api/v1/billing/plans` এপিআই ডাইনামিক প্ল্যান পরিবেশন করবে।

---

### Phase 6: Config Versioning, Rollback & Audit Logging
- প্রতিটি কনফিগ পরিবর্তনের জন্য অডিট হিস্ট্রি সংরক্ষণ (`who`, `what`, `old_value`, `new_value`, `timestamp`, `version`).
- ভুল কনফিগ এন্ট্রি হলে এক ক্লিকে পূর্ববর্তী ভালো কনফিগে ফিরে যাওয়ার জন্য **One-Click Rollback** মেকানিজম তৈরি।

---

### Phase 7: Multi-Instance Synchronization & Quota Tuning
- `admin_dashboard.py`-তে হার্ডকোডেড প্রোভাইডার কোটা (Gemini: 50, OpenRouter: 40, Groq: 30, Render: 50, Global: 150) ডাইনামিক কোটা পুলে স্থানান্তর করা।
- ড্যাশবোর্ড থেকেই লাইভ ক্লাউড ও এআই প্রোভাইডার কোটা অ্যাডজাস্ট করার সক্ষমতা।

---

### Phase 8: Constitution CI Automated Enforcement
- আমাদের GitHub Actions CI পাইপলাইনে একটি অটোমেটেড লিন্টার/গার্ড রুল যোগ করা:
  - ডেভেলপার যদি কোনো নতুন ফিচার বা রুট ফাইলে হার্ডকোডেড কনফিগ (যেমন: `MAX_CONCURRENCY = 5` বা স্ট্যাটিক মডেল অ্যারে) পুশ করে, তবে CI ব্যর্থ হবে এবং ডাইনামিক কনফিগ স্কিমায় রেজিস্ট্রেশন করার জন্য সতর্ক করবে।
  - অনুমোদিত ইনভেরিয়েন্ট হলে তা সুনির্দিষ্ট ডিক্লারেশন দিয়ে এপ্রুভ করতে হবে।

---

### Phase 9: Full Verification & Resilience Testing
- **Failover Injection Test**: Redis অফলাইন করে L2 (Postgres) এবং L3 (Last Known Good) ফলব্যাক টেস্ট করা।
- **Multi-Instance Sync Test**: ইনস্ট্যান্স ১ থেকে কনফিগ চেঞ্জ করলে ইনস্ট্যান্স ২-তে লাইভ রিফ্লেক্ট হওয়ার টেস্ট।
- **End-to-End UI Verification**: অ্যাডমিন ড্যাশবোর্ড থেকে টগল পরিবর্তন করে ব্রাউজারে রিলোড ছাড়াই নতুন ফিচার এক্টিভেশন যাচাই।

---

## 🎯 বাস্তবায়ন শুরু করার সুনির্দিষ্ট পদক্ষেপ

আমরা এখন **Phase 0 (কনফিগ সেন্সাস ও স্কিমা রেজিস্ট্রেশন)** এবং **Phase 1 (ConfigService এর L1-L4 ও ভ্যালিডেশন লেয়ার)** দিয়ে কোডবেসে কাজ শুরু করতে পারি। আপনার চূড়ান্ত সবুজ সংকেত পেলে সরাসরি কোডিং এক্সিকিউশনে যাব।
