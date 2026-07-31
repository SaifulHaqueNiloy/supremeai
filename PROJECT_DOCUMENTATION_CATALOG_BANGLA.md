# SupremeAI 2.0 — সমগ্র প্রজেক্ট ডকুমেন্টেশন ইনভেন্টরি ও নির্দেশিকা (Project Documentation Catalog)

> **ডকুমেন্টের অবস্থা:** লাইভ ও হালনাগাদ  
> **প্রস্তুতির তারিখ:** ৩১ জুলাই, ২০২৬  
> **ভাষাগত মাধ্যম:** বাংলা (Bangla)  
> **সারসংক্ষেপ:** এই ডকুমেন্টে SupremeAI 2.0 প্রজেক্টের অধীনস্থ সমস্ত প্রধান ফাইল, নির্দেশিকা, স্থাপত্য নকশা, রানবুক এবং টেস্ট রিপোর্টের বিবরণ সংকলিত হয়েছে। একাধিক ডকুমেন্টে একই বিষয়বস্তু থাকলে কোনটি সর্বাধিক হালনাগাদ ও নির্ভুল (Latest & Most Accurate) তা স্পষ্টভাবে চিহ্নিত করা হয়েছে।

---

## 📌 ১. রুট লেভেল ও কোর গভর্ন্যান্স ডকুমেন্ট (Root & Governance Documents)

| ডকুমেন্টের নাম | ফাইল লোকেশন (File Path) | মূল বিষয়বস্তু ও বিবরণ | সর্বশেষ ও নির্ভুলতা স্থিতি (Status) |
| :--- | :--- | :--- | :--- |
| **`AGENTS.md`** | `AGENTS.md` | প্রজেক্ট ওভারভিউ, আর্কিটেকচারাল রুলস, AI এজেন্টের আচরণবিধি, CI/CD নিয়মাবলী এবং অন-স্পট সিকিউরিটি প্রোটোকল। | **সর্বাধিক নির্ভুল (Single Source of Truth for AI/Agents)** |
| **`README.md`** | `README.md` | SupremeAI 2.0-এর পরিচয়, মাল্টি-ক্লাউড ফ্রি-টিয়ার অর্কেস্ট্রেশন, প্রজেক্ট ইনস্টলেশন ও রানবুক নির্দেশিকা। | **সর্বশেষ ও আপডেট** |
| **`CONTRIBUTING.md`** | `CONTRIBUTING.md` | ওপেন সোর্স ও টিম কন্ট্রিবিউশন গাইডলাইন, Pull Request নিয়মাবলী। | **সক্রিয়** |
| **`FAILING_TESTS.md`** | `FAILING_TESTS.md` | ব্যাকএন্ড ও ইন্টিগ্রেশন টেস্টের ব্যর্থতার কারণ ও ট্র্যাকিং হিস্ট্রি। | **অডিট রেকর্ড** |
| **`FINAL_PROJECT_SUMMARY_BANGLA.md`** | `FINAL_PROJECT_SUMMARY_BANGLA.md` | সম্পূর্ণ প্রজেক্টের বাংলা সারসংক্ষেপ, ফ্রি-টিয়ার অর্কেস্ট্রেশনের ফলাফল এবং সফলতার তথ্য। | **সর্বশেষ বাংলা সারসংক্ষেপ** |
| **`GITHUB_ACTIONS_FIX_SUMMARY_BANGLA.md`** | `GITHUB_ACTIONS_FIX_SUMMARY_BANGLA.md` | GitHub Actions CI/CD ওয়ার্কফ্লো ফিক্স ও গ্রিন বিল্ড সংক্রান্ত বাংলা সারসংক্ষেপ। | **সর্বশেষ ওয়ার্কফ্লো ফিক্স রেকর্ড** |
| **`MOCK_TESTS_DOCUMENTATION_BANGLA.md`** | `MOCK_TESTS_DOCUMENTATION_BANGLA.md` | ব্যাকএন্ড টেস্টে আসল এপিআই কলের বদলে সাশ্রয়ী মক টেস্ট ব্যবহারের বিস্তৃত বাংলা নির্দেশিকা। | **সর্বশেষ মক টেস্ট নির্দেশিকা** |
| **`task_progress.md`** | `task_progress.md` | সাম্প্রতিক সিস্টেম ডেভেলপমেন্ট ও কাজের অগ্রগতির সামারি ট্র্যাকার। | **লাইভ ট্র্যাকার** |
| **`LICENSE`** | `LICENSE` | প্রজেক্টের MIT সফ্টওয়্যার লাইসেন্স ফাইল। | **অফিসিয়াল** |

---

## 📌 ২. ডেভেলপার গাইডলাইন ও আর্কিটেকচার (`docs/developer-guide/`)

| ডকুমেন্টের নাম | ফাইল লোকেশন (File Path) | মূল বিষয়বস্তু ও বিবরণ | সর্বশেষ ও নির্ভুলতা স্থিতি (Status) |
| :--- | :--- | :--- | :--- |
| **`01-PROJECT-SETUP.md`** | `docs/developer-guide/01-PROJECT-SETUP.md` | স্থানীয় এনভায়রনমেন্ট সেটআপ, Poetry, Node.js এবং Docker রানারের ধাপসমূহ। | **সর্বাধিক নির্ভুল (Numbered Guide)** |
| **`02-TESTING-STRATEGY.md`** | `docs/developer-guide/02-TESTING-STRATEGY.md` | pytest, Vitest এবং Flutter টেস্ট স্ট্র্যাটেজি ও কভারেজ পলিসি। | **সর্বাধিক নির্ভুল** |
| **`03-CI-CD-PIPELINE.md`** | `docs/developer-guide/03-CI-CD-PIPELINE.md` | GitHub Actions, Cloud Run, Firebase Deploy ও সিআই/সিডি অটোমেশন। | **সর্বাধিক নির্ভুল** |
| **`04-SECURITY-HARDENING.md`** | `docs/developer-guide/04-SECURITY-HARDENING.md` | JIT OTP ভেরিফিকেশন, সিবিএসি সিকিউরিটি, সিক্রেট সিংক্রোনাইজেশন। | **সর্বাধিক নির্ভুল** |
| **`05-BACKEND-ARCHITECTURE.md`** | `docs/developer-guide/05-BACKEND-ARCHITECTURE.md` | FastAPI ব্যাকএন্ড ডিজাইন, Provider Selection Intelligence (PSI)। | **সর্বাধিক নির্ভুল** |
| **`06-FRONTEND-DEVELOPMENT.md`** | `docs/developer-guide/06-FRONTEND-DEVELOPMENT.md` | Studio React Client এবং Flutter Mobile App স্ট্রাকচার। | **সর্বাধিক নির্ভুল** |
| `index.md` / `getting-started.md` | `docs/developer-guide/index.md` | ডেভেলপার পোর্টাল ইমপোর্ট ও গাইড ওভারভিউ। | সাধারণ নির্দেশিকা (`01-PROJECT-SETUP.md` বেশি আপডেটেড) |
| `architecture.md` | `docs/developer-guide/architecture.md` | প্রজেক্টের হাই-লেভেল আর্কিটেকচারাল ডায়াগ্রাম ও ডেটাফ্লো। | মূল ব্যাকএন্ডের জন্য `05-BACKEND-ARCHITECTURE.md` রেফার করুন |
| `coding-standards.md` | `docs/developer-guide/coding-standards.md` | Python (Ruff/MyPy) এবং TypeScript কোডিং স্ট্যান্ডার্ড। | প্রজেক্ট স্ট্যান্ডার্ড |
| `configuration-management.md` | `docs/developer-guide/configuration-management.md` | `.env` সিঙ্ক ও মাল্টি-প্ল্যাটফর্ম সিক্রেট ম্যানেজমেন্ট। | অত্যন্ত গুরুত্বপূর্ণ সিক্রেট ডক |
| `database-management.md` | `docs/developer-guide/database-management.md` | PostgreSQL, Redis এবং Firestore ডেটাবেস স্কিমা ও মাইগ্রেশন। | ডেটাবেস নির্দেশিকা |
| `deployment.md` / `testing.md` | `docs/developer-guide/deployment.md` | ডিপ্লয়মেন্ট ও টেস্টিং গাইডলাইন। | `03-CI-CD-PIPELINE.md` ও `02-TESTING-STRATEGY.md` এর হালনাগাদ রূপ |
| `troubleshooting.md` | `docs/developer-guide/troubleshooting.md` | ডেভেলপমেন্ট ও লোকাল এনভায়রনমেন্ট সমস্যা সমাধান। | সাধারণ নির্দেশিকা |

---

## 📌 ৩. সিস্টেম অপারেশন ও ট্রাবলশুটিং (`docs/operations/`)

| ডকুমেন্টের নাম | ফাইল লোকেশন (File Path) | মূল বিষয়বস্তু ও বিবরণ | সর্বশেষ ও নির্ভুলতা স্থিতি (Status) |
| :--- | :--- | :--- | :--- |
| **`FULLSTACK_ERROR_FIX_AND_TROUBLESHOOTING_GUIDE.md`** | `docs/operations/FULLSTACK_ERROR_FIX_AND_TROUBLESHOOTING_GUIDE.md` | ফুলস্ট্যাক অ্যাপ্লিকেশন, ডিপেনডেন্সি এরর এবং ব্যাকএন্ড সমস্যা সমাধানের মাস্টার নির্দেশিকা। | **সর্বাধিক নিখুঁত অপারেশনাল গাইড** |
| **`RENDER_DEPLOYMENT_TROUBLESHOOTING_GUIDE.md`** | `docs/operations/RENDER_DEPLOYMENT_TROUBLESHOOTING_GUIDE.md` | Render Cloud Deploy ফেইলিউর, এনভায়রনমেন্ট সিক্রেট মিসম্যাচ এবং মেমোরি ফিক্স রানবুক। | **Render ডিপ্লয়মেন্টের জন্য সেরা** |

---

## 📌 ৪. ভিএস কোড এক্সটেনশন ডকস (`tools/vscode-extension/`)

| ডকুমেন্টের নাম | ফাইল লোকেশন (File Path) | মূল বিষয়বস্তু ও বিবরণ | সর্বশেষ ও নির্ভুলতা স্থিতি (Status) |
| :--- | :--- | :--- | :--- |
| **`README_BANGLA.md`** | `tools/vscode-extension/README_BANGLA.md` | SupremeAI VS Code Extension ব্যবহারের সম্পূর্ণ বাংলা নির্দেশিকা ও ফিচার বিবরণী। | **সর্বশেষ ও সর্বাধিক নির্ভুল বাংলা ডক** |
| **`ARCHITECTURE_BN.md`** | `tools/vscode-extension/ARCHITECTURE_BN.md` | এক্সটেনশনের অভ্যন্তরীণ আর্কিটেকচার, প্যানেল ও প্রোভাইডারসমূহের বাংলা টেকনিক্যাল ওভারভিউ। | **আর্কিটেকচারের জন্য সেরা** |
| **`INTEGRATION_GUIDE_BN.md`** | `tools/vscode-extension/INTEGRATION_GUIDE_BN.md` | ভিএস কোড এক্সটেনশনের সাথে ব্যাকএন্ড অর্কেস্ট্রেটর ইন্টিগ্রেশন নির্দেশিকা। | **ইন্টিগ্রেশনের জন্য সেরা** |
| `README_BN.md` | `tools/vscode-extension/README_BN.md` | ভিএস কোড এক্সটেনশন বাংলা ডক (পুরাতন ভার্সন)। | `README_BANGLA.md` দ্বারা প্রতিস্থাপিত |
| `README.md` / `CHANGELOG.md` | `tools/vscode-extension/README.md` | এক্সটেনশনের ইংরেজি সারসংক্ষেপ ও রিলিজ চেঞ্জলগ। | স্ট্যান্ডার্ড প্যাকেজ ডক |

---

## 📌 ৫. রিপোর্ট ও কোয়ালিটি অডিট (`docs/reports/` & `docs/quality/`)

| ডকুমেন্টের নাম | ফাইল লোকেশন (File Path) | মূল বিষয়বস্তু ও বিবরণ | সর্বশেষ ও নির্ভুলতা স্থিতি (Status) |
| :--- | :--- | :--- | :--- |
| **`test_coverage_plan.md`** | `docs/quality/test_coverage_plan.md` | ৩৮%+ টেস্ট কভারেজ অর্জনের জন্য বিস্তারিত ব্যাকএন্ড ও ফ্রন্টএন্ড প্ল্যান। | **কোয়ালিটি কভারেজ প্ল্যান** |
| **`SupremeAI_Resource_Sites_Analysis_Bangla.md`** | `docs/reports/SupremeAI_Resource_Sites_Analysis_Bangla.md` | প্রজেক্টে ব্যবহৃত বিভিন্ন AI সার্ভিস ও রিসোর্সের ফ্রি-টিয়ার এনালাইসিস (বাংলা)। | **রিসোর্স এনালাইসিসের জন্য সেরা** |
| **`full_modified_codebase.md`** | `docs/reports/full_modified_codebase.md` | সাম্প্রতিক রিফ্যাক্টরিং ও ফিক্সের কোডবেস অডিট রিপোর্ট। | **অডিট স্ন্যাপশট** |
| `github_pipelines.md` | `docs/reports/github_pipelines.md` | সিআই/সিডি পাইপলাইন বিশ্লেষণের বিস্তারিত স্টেটাস। | পাইপলাইন রিপোর্ট |
| `project_gap_analysis.md` | `docs/reports/project_gap_analysis.md` | প্রজেক্ট গ্যাপ ও ঘাটতি এনালাইসিস। | গ্যাপ এনালাইসিস |
| `LOCAL_SETUP_GUIDE.md` | `docs/reports/LOCAL_SETUP_GUIDE.md` | লোকাল ডেভেলপমেন্ট সেটআপ রিপোর্ট। | `01-PROJECT-SETUP.md` ব্যবহারে পরামর্শ দেওয়া হচ্ছে |

---

## 📌 ৬. অটো-জেনারেটেড ও মডিউলার অডিট রিপোর্টস (`docs/autogen/`)

| ডিরেক্টরি / ক্যাটাগরি | ফাইল লোকেশন (File Path) | মূল বিষয়বস্তু ও বিবরণ |
| :--- | :--- | :--- |
| **মডিউলার অডিট পার্টিশন** | `docs/autogen/modular_audits/PART_01_LLM_GATEWAY_ROUTER.md` থেকে `PART_14_CLOUD_INFRASTRUCTURE.md` | সিস্টেমে বিদ্যমান ১৪টি কোর সাব-সিস্টেমের (যেমন LLM Gateway, P2P Compute, Swarm WebSockets, React Client ইত্যাদি) বিস্তারিত অডিট রিপোর্ট। |
| **কোডবেস অডিটসমূহ** | `docs/autogen/codebase/*` | প্রতিটি সোর্স কোড ফাইলের সবিস্তার টেকনিক্যাল অ্যানোটেশন ডক্স। |
| **পুশ ও ডিপ্লয়মেন্ট সামারি** | `docs/autogen/summaries/PUSH-SUMMARY-*.md` | দূরবর্তী গিটহাব পুশের সময় জেনারেট হওয়া অটোমেটেড পরিবর্তন সংক্রান্ত ইতিহাস। |

---

## 📌 ৭. এপিআই ভি১ নির্দেশিকা (`docs/api/v1/`)

| ডকুমেন্টের নাম | ফাইল লোকেশন (File Path) | মূল বিষয়বস্তু ও বিবরণ | সর্বশেষ ও নির্ভুলতা স্থিতি (Status) |
| :--- | :--- | :--- | :--- |
| **`index.md`** | `docs/api/v1/index.md` | API v1 এন্ডপয়েন্টসমূহের ওভারভিউ এবং মূল ব্যবহারের সূচনা। | **API v1 মাস্টার ডক** |
| **`agents.md`** | `docs/api/v1/agents.md` | AI এজেন্ট এপিআই রাউটিং, এজেন্ট এক্সিকিউশন ও স্টেটাস এন্ডপয়েন্ট। | **এজেন্ট এপিআই ডক** |
| **`authentication.md`** | `docs/api/v1/authentication.md` | JWT টোকেন, JIT OTP এবং সিকিউরিটি অথেন্টিকেশন এপিআই। | **অথেন্টিকেশন এপিআই ডক** |
| **`tools.md`** | `docs/api/v1/tools.md` | AI এজেন্টের টুল এক্সিকিউশন ও ইন্টিগ্রেশন এপিআই। | **টুলস এপিআই ডক** |
| **`webhooks.md`** | `docs/api/v1/webhooks.md` | এক্সটার্নাল ইভেন্ট ও ডিসকর্ড/ক্লাউড সেবার ওয়েবহুক এন্ডপয়েন্ট। | **ওয়েবহুক ডক** |
| **`workflows.md`** | `docs/api/v1/workflows.md` | মাল্টি-স্টেপ ওয়ার্কফ্লো এবং পাইপলাইন এপিআই নির্দেশিকা। | **ওয়ার্কফ্লো ডক** |

---

## 📌 ৮. আর্কাইভ রিপোর্টস ও পুরাতন হিস্ট্রি (`docs/archived_reports/`)

| ক্যাটাগরি | ফাইল লোকেশন (File Path) | মূল বিষয়বস্তু ও বিবরণ | স্থিতি (Status) |
| :--- | :--- | :--- | :--- |
| **আর্কাইভড অডিট ও প্ল্যান** | `docs/archived_reports/PHASE1_AUDIT_REPORT.md` থেকে `PHASE5_AUDIT_REPORT.md` | পূর্ববর্তী পর্যায়ের (Phase 1-5) অডিট রিপোর্ট ও প্ল্যানিং ফাইলসমূহ। | **আর্কাইভড (ঐতিহাসিক তথ্য)** |
| **আর্কাইভড বাংলা ডকস** | `docs/archived_reports/*_BANGLA.md` | ভিএস কোড এক্সটেনশন, টেস্ট রিফ্যাক্টরিং ও পূর্বের কাজের বাংলা রিপোর্ট। | আর্কাইভ করা রিভিশন হিস্ট্রি |

---

## 💡 তুলনামূলক বিশ্লেষণ ও ব্যবহারের নির্দেশাবলী (Latest & Most Accurate Guidance)

১. **AI এজেন্টের নিয়মাবলী ও গভর্ন্যান্স:**  
   - রুট ডিরেক্টরির `AGENTS.md` হলো পুরো প্রজেক্টের **একমাত্র চূড়ান্ত সত্য (Single Source of Truth)**।
২. **ডেভেলপার সেটআপ ও আর্কিটেকচার:**  
   - `docs/developer-guide/` ডিরেক্টরির সংখ্যাযুক্ত ডকগুলো (`01-PROJECT-SETUP.md` থেকে `06-FRONTEND-DEVELOPMENT.md`) সাধারণ জেনেরিক ফাইলগুলো (`getting-started.md`, `setup.md`) অপেক্ষা **সর্বাধিক নিখুঁত ও হালনাগাদ**।
৩. **ভিএস কোড এক্সটেনশন:**  
   - `tools/vscode-extension/README_BANGLA.md` ফাইলটি `README_BN.md`-এর তুলনায় **সর্বশেষ ভার্সন ও পূর্ণাঙ্গ নির্দেশিকা** সম্বলিত।
৪. **সমস্যা সমাধান ও ফিক্সেশন:**  
   - ফুলস্ট্যাক ও রানটাইম ত্রুটির জন্য `docs/operations/FULLSTACK_ERROR_FIX_AND_TROUBLESHOOTING_GUIDE.md` এবং ক্লাউড ডিপ্লয়মেন্টের জন্য `docs/operations/RENDER_DEPLOYMENT_TROUBLESHOOTING_GUIDE.md` অনুসরণ করুন।
