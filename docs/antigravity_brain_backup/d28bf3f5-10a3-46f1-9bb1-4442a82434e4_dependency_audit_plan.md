# SupremeAI 2.0 — Dependency Audit & Version Update Plan
_তারিখ: ২৭ জুলাই, ২০২৬ | বিশ্লেষক: Principal AI Architect_

---

## 📊 অডিট সারসংক্ষেপ (Audit Summary)

| ক্যাটাগরি | সংখ্যা |
| :--- | :--- |
| 🔴 অব্যবহৃত/সরানো উচিত | ১১টি |
| 🟡 Wildcard `*` পিন → নির্দিষ্ট ভার্সনে নামানো উচিত | ১১টি |
| 🟠 Breaking Change Wall (হাত দেওয়া বিপজ্জনক) | ৫টি |
| 🟢 নিরাপদ ভার্সন বাম্প সম্ভব | ৮টি |
| ⚫ Architecture Decision Required | ১টি |

---

## 🔴 ১. অব্যবহৃত ডিপেনডেন্সি (Completely Unused — Remove These)

এই লাইব্রেরিগুলো `backend/` এ একটিও Python ফাইলে `import` করা হয়নি।

| প্যাকেজ | ফাইলে ইম্পোর্ট আছে? | বিকল্প |
| :--- | :--- | :--- |
| `streamlit` | ❌ শূন্য | নেই — সরান |
| `bokeh` | ❌ শূন্য | নেই — সরান |
| `altair` | ❌ শূন্য | নেই — সরান |
| `seaborn` | ❌ শূন্য | নেই — সরান |
| `motor` | ❌ শূন্য (async MongoDB) | নেই — সরান |
| `clickhouse-connect` | ❌ শূন্য | নেই — সরান |
| `influxdb-client` | ❌ শূন্য | নেই — সরান |
| `gspread` | ❌ শূন্য (Google Sheets) | নেই — সরান |
| `oauth2client` | ❌ শূন্য (deprecated Google lib) | `google-auth` দিয়ে কভার |
| `langserve` | ❌ শূন্য | নেই — সরান |
| `opensearch-py` | ❌ শূন্য | নেই — সরান |

> [!CAUTION]
> এই প্যাকেজগুলো প্রতিটি `poetry install` তে অতিরিক্ত ডাউনলোড ও ডিস্ক স্পেস নষ্ট করছে। বিশেষ করে `streamlit` প্রায় ২০০+ MB সাথে টানে।

---

## 🟡 ২. Wildcard `*` পিন ফিক্স (Pin These to Safe Versions)

এই ডিপেনডেন্সিগুলো `"*"` হিসেবে আছে, যেকোনো Breaking Change চলে আসতে পারে।

| প্যাকেজ | বর্তমান | প্রস্তাবিত নিরাপদ পিন |
| :--- | :--- | :--- |
| `uuid6` | `"*"` | `"^0.1.0"` |
| `boto3` | `"*"` | `"^1.38.0"` |
| `defusedxml` | `"*"` | `"^0.7.1"` |
| `beautifulsoup4` | `"*"` | `"^4.13.0"` |
| `posthog` | `"*"` | `"^3.12.0"` |
| `mcp` | `"*"` | `"^1.9.0"` |
| `stripe` | `"*"` | `"^12.1.0"` |
| `neo4j` | `"*"` | `"^5.28.0"` |
| `pydantic-extra-types` | `"*"` | `"^2.10.0"` |
| `pybreaker` | `"*"` | `"^1.2.0"` |
| `statsmodels` | `"*"` | `"^0.14.0"` |

> [!IMPORTANT]
> `poetry lock` রান করার পর `poetry show <package>` দিয়ে বর্তমান resolved ভার্সন চেক করে ঐ ভার্সনটিই `^` দিয়ে পিন করুন।

---

## 🟠 ৩. Breaking Change Wall (স্পর্শ করবেন না এখনই)

| প্যাকেজ | বর্তমান | নতুন | ঝুঁকি |
| :--- | :--- | :--- | :--- |
| `langchain` | `^0.3.7` | 1.0 | **Hard Breaking** — API redesign |
| `langchain-community` | `^0.3.7` | 1.0 | **Hard Breaking** |
| `langchain-core` | `^0.3.15` | 1.0 | **Hard Breaking** |
| `langgraph` | `^0.2.39` | 2.x | Major API changes |
| `langchain-google-genai` | `^2.0.6` | — | LangChain-1.0-এর আগে করবেন না |

> [!WARNING]
> LangChain 1.0 (April 2026) এ পুরনো ফাংশন সরিয়ে `langchain-classic`-এ নিয়ে গেছে। যতক্ষণ না কোড migrate করা হয়, এই ভার্সনগুলো `^0.3.x`-এ রাখুন।

---

## 🟢 ৪. নিরাপদ ভার্সন বাম্প (Safe to Update Now)

| প্যাকেজ | বর্তমান | প্রস্তাবিত | কারণ |
| :--- | :--- | :--- | :--- |
| `openai` | `^1.54.0` | `^1.95.0` | Tool-calling ও Structured Output উন্নত |
| `litellm` | `^1.50.0` | `^1.74.0` | Multi-provider routing নতুন ফিচার |
| `supabase` | `^2.11.0` | `^2.15.0` | Auth helper ও realtime improvement |
| `firebase-admin` | `^6.5.0` | `^6.8.0` | Minor security patches |
| `qdrant-client` | `^1.12.1` | `^1.14.0` | Vector DB query optimization |
| `pymongo` | `^4.10.0` | `^4.13.0` | Connection pooling improvement |
| `elasticsearch` | `^8.16.0` | `^8.20.0` | Minor feature updates |
| `mlflow` | `^2.17.0` | `^2.22.0` | Model tracking সাপোর্ট |

---

## ⚫ ৫. Architecture Decision (Desktop App)

**সমস্যা:** দুটি প্রতিযোগী Desktop অ্যাপ কৌশল:

| App | Framework | Electron Version |
| :--- | :--- | :--- |
| `apps/desktop/` | Electron (পুরনো) | `^28.0.0` (২০২৩) |
| `apps/studio-client/` | Electron (নতুন) | `^41.8.0` (২০২৬) |

**সুপারিশ:** `apps/desktop/` archive করুন। Desktop build শুধু `studio-client` থেকে নিন।

---

## 📋 Implementation Roadmap

### Phase 1 — এখনই (৩০ মিনিট) 🔥
- [ ] `pyproject.toml` থেকে ১১টি অব্যবহৃত প্যাকেজ সরান
- [ ] ১১টি `*` wildcard পিন করুন নির্দিষ্ট ভার্সনে
- [ ] `poetry lock` পুনরায় রিজেনারেট করুন
- [ ] **প্রত্যাশিত সুবিধা:** venv ৫০০ MB+ ছোট, CI ২-৩ মিনিট দ্রুত

### Phase 2 — এই সপ্তাহে (১ ঘণ্টা) 
- [ ] ৮টি নিরাপদ ভার্সন বাম্প করুন
- [ ] `poetry lock` + pytest রান করুন কিছু ভাঙেনি নিশ্চিত করতে

### Phase 3 — পরবর্তী Sprint
- [ ] `apps/desktop/` deprecate/archive করুন
- [ ] Desktop build শুধুমাত্র `studio-client` থেকে

### Phase 4 — ৩-৫ দিনের পরিকল্পনা
- [ ] LangChain 1.0 Migration Guide অনুসরণ করুন
- [ ] সব `langchain.*` import চিহ্নিত করে `langchain-classic`-এ মাইগ্রেট করুন

---

## 💰 প্রত্যাশিত সুবিধা (Phase 1 + 2 সম্পন্ন হলে)

| সুবিধা | আনুমানিক মান |
| :--- | :--- |
| CI Build Time হ্রাস | ~৩-৪ মিনিট |
| venv ডিস্ক ব্যবহার হ্রাস | ~৬০০ MB+ |
| Breaking Change ঝুঁকি হ্রাস | উল্লেখযোগ্য |
| `poetry install` সময় হ্রাস | ~৩-৫ মিনিট |
