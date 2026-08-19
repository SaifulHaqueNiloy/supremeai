# LESSONS_LEARNED
> **[🤖 AI AGENT INSTRUCTION]** 
> This is a core SupremeAI "Brain" file. When adding a new lesson:
> 1. Add it to the TOP of the list (reverse chronological).
> 2. Include Date, Issue, Fix, and Lesson.
> 3. DO NOT delete or overwrite past historical entries.
> 4. Keep it concise and technical.

## 2026-08-19 — 🌐 Full-Stack AI Browser Automation Studio & HITL Integration
- **সমস্যা:** অ্যাডমিন প্যানেলে ব্রাউজার অটোমেশন ব্যাকএন্ড রুট ও প্রক্সি থাকলেও কোনো ফার্স্ট-ক্লাস ইন্টারঅ্যাক্টিভ লাইভ স্টুডিও ছিল না যা দিয়ে অ্যাডমিন ব্রাউজিং দেখতে, অটোনোমাস গোল এক্সিকিউট করতে বা CAPTCHA আসলে টেকওভার নিতে পারত।
- **ফিক্স:** `LiveBrowserStudio.tsx` তৈরি করে অ্যাডমিন সাইডবারে যুক্ত করা হয়েছে। এতে রেসপন্সিভ ভিউপোর্ট (Desktop/Tablet/Mobile), প্রক্সাইড রেন্ডারিং, স্টেপ-বাই-স্টেপ অ্যাকশন লগ, আর্টফ্যাক্টস/ফাইন্ডিংস এক্সপোর্ট এবং One-Click Human Takeover (HITL) সম্পূর্ণ কার্যকর করা হয়েছে।
- **লেসন:** ব্রাউজার অটোমেশন সিস্টেমে সর্বদা Human-in-the-Loop (HITL) ইন্টারসেপশন ও সিকিউর প্রক্সি মেকানিজম যুক্ত রাখতে হবে যাতে কোনো আইফ্রেম পলিসি (X-Frame-Options) বা বটের বাধা ছাড়াই লাইভ মনিটরিং ও কন্ট্রোল বজায় থাকে।

## 2026-08-19 — ⚡ Supreme-Kaggle 6-Node (180h GPU/Week) Zero-Cost Compute Supercomputer Matrix
- **সমস্যা:** এক্সটার্নাল এআই এপিআই কলের ওপর সার্বক্ষণিক নির্ভরশীলতা এবং লোকাল পিসিতে হেভি কমপিউটের অভাবের কারণে ডিপ ভেক্টর এম্বেডিং, কন্টিনিউয়াস কোডবেস ইন্ডেক্সিং ও অটোমেটেড টেস্ট সিন্থেসিস চালানো ব্যয়বহুল ও ধীরগতির ছিল।
- **ফিক্স:** ৬টি Kaggle অ্যাকাউন্টকে একটি ক্লাস্টার পুলে অর্কেস্ট্রেট করে সাপ্তাহিক ১৮০ ঘণ্টার Nvidia Dual T4 GPU কমপিউট পাওয়ার ($0 কস্টে) চালু করা হয়েছে। `scripts/kaggle/account_pool_rotator.py`, `pipeline_orchestrator.py` এবং ৩টি GPU নোটবুক (`vector_fabric.ipynb`, `brain_distillation.ipynb`, `weekend_self_healer.ipynb`) তৈরি করা হয়েছে। `scripts/check_env_health.py`-তে ৬/৬ নোড হেলথ চেক যুক্ত ও ভেরিফাই করা হয়েছে।
- **লেসন:** লাইভ ক্লাউড হোস্টিংয়ের বদলে হেভি কমপিউটকে ব্যাকগ্রাউন্ড ব্যাচ পাইপলাইনে অফলোড করলে ক্লাউড বা এপিআই খরচ ১০০% শূন্য রেখেই এন্টারপ্রাইজ-গ্রেড হাই-স্পিড মেমোরি ও কোড কোয়ালিটি নিশ্চিত করা সম্ভব।

## 2026-08-19 — 🛠️ CI/CD Full Pipeline Stabilization & Alembic Package Shadowing Resolution
- **সমস্যা:** (1) VS Code Extension-এ `SwarmPipelineProvider.ts:144` ESLint singlequote violation এবং `turbo.json` মিসিং `out/**` আউটপুট বিল্ড ফেইল করছিল; (2) `backend/alembic/__init__.py` ও `versions/__init__.py` থাকার কারণে Python-এর মডিউল রেজোলিউশনে রিয়েল সাইট-প্যাকেজ `alembic` শ্যাডো হয়ে `test_perf_indexes.py` ফেইল করছিল; (3) `scripts/audit_observability.py` সাইলেন্ট পাস ও আনসেফ প্রিন্ট স্টেটমেন্ট ফ্ল্যাগ করছিল; (4) `Type Sync Check`-এ `SecretHunter` ইমপোর্টে অপ্রয়োজনীয় হেভি `llm_gateway` ডিপেন্ডেন্সি থাকায় সিআই জবে ইমপোর্ট এরর হচ্ছিল।
- **ফিক্স:** (1) `SwarmPipelineProvider.ts` কোট ফিক্স ও `turbo.json` বিল্ড আউটপুট আপডেট করা হয়েছে; (2) `backend/alembic` প্যাকেজ ইনিট ফাইলগুলো মুছে দিয়ে `StaticPool` ও ফ্রেশ ইনস্পেক্টরে `tests/test_perf_indexes.py` ৭/৭ পাস করানো হয়েছে; (3) স্যান্ডবক্সে `stdout_buf` ক্রাফট ও লগিং এনহ্যান্স করে `audit_observability.py` ০ ভায়োলেশনে পাস করানো হয়েছে; (4) `SecretHunter`-এ লেজি গেটওয়ে লোডিং যুক্ত করে `Type Sync Check` সম্পূর্ণ সফল করা হয়েছে। GitHub Actions CI কারেন্ট রান `32198523572` **১০০% SUCCESS / GREEN** হয়েছে।
- **লেসন:** মাইগ্রেশন ডিরেক্টরিগুলোতে কখনোই `__init__.py` রাখা যাবে না যা টপ-লেভেল প্যাকেজকে শ্যাডো করতে পারে, এবং সিআই সিকিউরিটি ও টাইপ সিঙ্ক ইউটিলিটিগুলোকে সবসময় হেভি রানটাইম ডিপেন্ডেন্সি থেকে মুক্ত (লাইটওয়েট ও রেসিলিয়েন্ট) রাখতে হবে।

## 2026-08-19 — 🛡️ Long-Term Autonomous Governance & Self-Tracking Matrix
- **সমস্যা:** দীর্ঘমেয়াদে কোডবেস বড় হলে আনডকুমেন্টেড "Ghost" এনভায়রনমেন্ট ভ্যারিয়েবল, Pydantic ও TypeScript টাইপ ডিসিঙ্ক, এবং আনমনিটরড মেমোরি ব্লোটের কারণে সিস্টেম আনপ্রেডিক্টেবল হয়ে পড়ত।
- **ফিক্স:** ৪টি প্রোঅ্যাক্টিভ ইঞ্জিন তৈরি ও ভেরিফাই করা হয়েছে: (1) `scripts/audit_env_drift.py` ও `docs/ENV_AND_SECRET_REGISTRY.md` (০% Ghost Env), (2) `scripts/sync_contracts.py` (FastAPI to TypeScript টাইপ সিঙ্ক), (3) `scripts/ai/compact_brain_memory.py` (লগারিদমিক ডিকে ও AST ডুপ্লিকেট মার্জিং), এবং (4) `scripts/canary_health_probe.py` ($0 কস্ট ক্যানারি মনিটরিং)।
- **লেসন:** দীর্ঘমেয়াদী আর্কিটেকচারকে স্কেলেবল ও সেলফ-হিলিং রাখতে শুধু কোড লিখলে হবে না; ব্যাকগ্রাউন্ডে কাজ করার জন্য সেলফ-অডিটিং ও কন্ট্রাক্ট-এনফোর্সিং টুলস কোডবেসের অংশ হিসেবে রাখতে হবে।

## 2026-08-19 — 🗺️ Central Topology Registry & Automated URL Auditor
- **সমস্যা:** কোডবেসের বিভিন্ন মডিউল বা প্যাকেজে স্ট্যাটিক ফলব্যাক URL ছড়িয়ে থাকলে ক্লাউড মাইগ্রেশনের সময় ব্রোকেন রেফারেন্স তৈরি হতো।
- **ফিক্স:** `docs/SYSTEM_TOPOLOGY_AND_URL_REGISTRY.md` (SSOT) তৈরি করা হয়েছে এবং `scripts/audit_topology_urls.py` স্বয়ংক্রিয় অডিটর তৈরি করে ৩৯৬টি সোর্স ফাইল স্ক্যান ও ভ্যালিডেট করা হয়েছে। `AGENTS.md`-এ রুল অন্তর্ভুক্ত করা হয়েছে।
- **লেসন:** সেন্ট্রাল রেজিস্ট্রি ও সিআই ভ্যালিডেটর স্ক্রিপ্ট নিশ্চিত করে যে ভবিষ্যতে কোনো ডেভেলপার বা AI ভুল করে কোনো হার্ডকোডেড বা আউটডেটেড অ্যান্ডপয়েন্ট লিখলে তা সাথে সাথে ধরা পড়বে।

## 2026-08-19 — 🌐 VS Code Extension Production Gateway Alignment
- **সমস্যা:** (1) VS Code Extension-এর `package.json` ও `SwarmPipelineProvider.ts`-এ `supremeai.swarmBackendUrl` ডিফল্ট `http://localhost:8080` ছিল, যা ক্লাউড ব্যাকএন্ডের সাথে যুক্ত ছিল না; (2) `CrossAiObserverService.ts`, `SupremeWebviewProvider.ts`, এবং `TelemetryTracker.ts`-এ পুরনো হার্ডকোডেড Cloud Run URL ছিল।
- **ফিক্স:** (1) `package.json` ও `SwarmPipelineProvider.ts`-এ ডিফল্ট ব্যাকএন্ড URL হিসেবে প্রোডাকশন গেটওয়ে `https://supremeai-worker.paykaribazaronline.workers.dev` সেট করা হয়েছে; (2) `CrossAiObserverService`, `SupremeWebviewProvider` ও `TelemetryTracker`-এ কনফিগারেশন থেকে ডায়নামিক `backendUrl` রেজোলিউশন চালু করা হয়েছে।
- **লেসন:** ক্লায়েন্ট বা এক্সটেনশন মডিউলে কখনোই স্ট্যাটিক বা হার্ডকোডেড ক্লাউড URL বা লোকালহোস্ট ফলব্যাক রাখা যাবে না; সবসময় কনফিগারেশন ও সিঙ্গেল গেটওয়ে থেকে ডায়নামিক্যালি রেজলভ করতে হবে।
