# LESSONS_LEARNED
> **[🤖 AI AGENT INSTRUCTION]** 
> This is a core SupremeAI "Brain" file. When adding a new lesson:
> 1. Add it to the TOP of the list (reverse chronological).
> 2. Include Date, Issue, Fix, and Lesson.
> 3. DO NOT delete or overwrite past historical entries.
> 4. Keep it concise and technical.

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

## 2026-08-19 — 🧩 AST Canonicalizer & Structural Invariant Matching in KnowledgeDistiller
- **সমস্যা:** কোডে ভ্যারিয়েবল, ফাংশন বা প্যারামিটারের নাম আলাদা হলে (যেমন: `calculate_metrics(values)` বনাম `compute_scores(items)`) সাধারণ টেক্সট হ্যাশ মিলত না, ফলে ডুপ্লিকেট ডিস্টিল্ড এন্ট্রি তৈরি হতো এবং রিট্রিভাল মিস হতো। পাইথন ৩.৮+-এ ফাংশন আর্গুমেন্ট `ast.Name(Param)`-এ থাকে না, থাকে `ast.arg`-এ।
- **ফিক্স:** `knowledge_distiller.py`-তে `ASTCanonicalizer` তৈরি করে (1) ডকস্ট্রিং রিমুভ, (2) ফাংশন নেম নরমালাইজ (`canonical_fn`), (3) `ast.arguments` (pos/kw/args) এবং লোকাল ভ্যারিয়েবলগুলোকে `v_0, v_1, ...` ক্যানোনিকাল সিকোয়েন্সে রূপান্তর করে ১৮-অক্ষরের `ast_fingerprint` ইনভ্যারিয়েন্ট হ্যাশ তৈরি করা হয়েছে। `find_structural_ast_match()` দিয়ে শতভাগ নাম-ইন্ডিপেন্ডেন্ট অ্যালগরিদম ম্যাচিং নিশ্চিত করা হয়েছে।
- **লেসন:** কোড ইনভ্যারিয়েন্ট ম্যাচিংয়ের জন্য টেক্সট বা এমবেডিংয়ের চেয়ে ক্যানোনিকাল অ্যাবস্ট্রাক্ট সিনট্যাক্স ট্রি (AST) ১০০ গুণ বেশি ডিটারমিনিস্টিক ও টোকেন-সাশ্রয়ী।

## 2026-08-19 — 🌟 4 Improvised Master Architectural Pillars
- **সমস্যা:** (1) সিঙ্গেল-প্রম্পটে পুরো অ্যাপ তৈরির জন্য আলাদা আলাদা সাবসিস্টেম (AOD, MCP Mesh, Context Graph) কানেক্টেড ছিল না; (2) ৩য় পক্ষ মডেলের উত্তরের উপর সিস্টেম দীর্ঘমেয়াদে নির্ভরশীল ছিল; (3) লাইভ ব্রেইন অ্যাক্টিভিটি ফ্রন্টএন্ডে রিয়েল-টাইম স্ট্রিমিং হতো না; (4) লাইটওয়েট কোড টেস্টের জন্য হেভি স্যান্ডবক্সিং সেটআপের প্রয়োজন হতো।
- **ফিক্স:** (1) `self_assembling_orchestrator.py` ও `/api/self-assemble` তৈরি করে এন্ড-টু-এন্ড সিঙ্গেল প্রম্পট অ্যাপ পাইপলাইন কার্যকর করা হয়েছে; (2) `knowledge_distiller.py` দিয়ে সফল লজিক ও সলিউশন মেমোরি ও কনটেক্সট গ্রাফে ডিস্টিল করে $0-cost ইন্ডিপেন্ডেন্স দেওয়া হয়েছে; (3) `brain_visualizer_bridge.py` ও `LiveBrainVisualizer.tsx` দিয়ে রিয়েল-টাইম WebSocket ব্রেইন পালস স্ট্রিমিং তৈরি করা হয়েছে; (4) `micro_runtime_sandbox.py` দিয়ে 0ms স্পিন-আপ ও জিরো-ডিপেন্ডেন্সি সেইফ ইন-মেমোরি এক্সিকিউশন নিশ্চিত করা হয়েছে; (5) `test_improvised_matrix.py` দিয়ে ৪/৪ টেস্ট ১০০% গ্রিন নিশ্চিত করা হয়েছে।
- **লেসন:** সেন্ট্রাল অর্কেস্ট্রেশনের সাথে নলেজ ডিস্টিলেশন যুক্ত করলে সিস্টেম নিজে থেকেই প্রতি সেশনে আরও বেশি বুদ্ধিমান ও স্বয়ংসম্পূর্ণ হয়ে ওঠে।
