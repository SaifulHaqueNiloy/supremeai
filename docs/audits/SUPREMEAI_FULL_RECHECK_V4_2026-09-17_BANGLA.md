# SupremeAI সম্পূর্ণ পুনঃপরীক্ষা (Full Recheck) V4 — ২০২৬-০৯-১৭

**পরিধি:** V3-এর একই প্যাটার্নে root থেকে পুনঃrecheck → নতুন defect বিশ্লেষণ → সম্পূর্ণ তালিকা (বাংলা)।
**ভিত্তি:** V3 পুশ `6ef6550e`-এর পরের main (`fb53ad86`/`c7d5bb8` — Crown Jewel Module Series cycle 3–7 plan-doc + duplicate_detector ২টি CI ফিক্স)।
**পূর্বসূরি:** `SUPREMEAI_FULL_RECHECK_V3_2026-09-17_BANGLA.md`।

---

## পার্ট ১ — ✅ V3-ফিক্স রিগ্রেশন যাচাই (প্যারালাল bot-এর পুশের পরেও অক্ষত)

| V3 ফিক্স | যাচাই |
|---|---|
| Mission gate sqlite-binding (`scheduled-deep-audit.yml`) | ✓ অক্ষত; **নোট:** পরবর্তী nightly রান (ভোরে) পর্যন্ত লাইভ-প্রমাণ বাকি — শেষ nightly (০৮:২৯) ফিক্সের আগের কমিটে চলেছিল |
| Duplicate Detector `EXEMPT_FILE_LEVEL_PAIRS` + ৩ ডিলিট | ✓ অক্ষত; bot-এর `cc561e4a`/`7c01c7cc` (path-normalize + empty-handler অপসারণ) মেনে নিয়েছে; লোকাল re-run **exit 0** |
| `token_budget.py` fail-closed | ✓ অক্ষত (বাংলা কমেন্ট সহ) |
| `plan_registry.json` | bot-এর নতুন ৯ Crown Jewel doc-এর জন্য **আবার পুনঃজেনারেট করা হয়েছে এই সেশনে** (165 → **174 documents**, crown_jewel/module ১০টি নিবন্ধিত) |

**লাইভ CI:** main সবুজ — `fb53ad86` ✓, `c7d5bb8` ✓ (rest সব supersede-cancelled)।

---

## পার্ট ২ — 🚨 এই সেশনের সবচেয়ে বড় আবিষ্কার: MCP SSRF গার্ডে ফুটো (B-V4-01, ঠিক করা হয়েছে)

`tests/security/test_mcp_zero_friction_security.py` — main-এ **৩টি টেস্ট লাল ছিল** (clean HEAD-এও; আমাদের পরিবর্তনের আগে-পরে একই): গার্ড `http://127.0.0.1/mcp`, `http://10.0.0.4/mcp`, `http://192.168.1.10/mcp`-কে **সেফ বলে পাস করিয়ে দিচ্ছিল**।

**রুট-কজ নির্ণয় (in-process instrumentation দিয়ে):**
1. গার্ডের loopback-ছাড় ছিল `settings.env == "local" and ip.is_loopback` — অর্থাৎ **আনুমানিক (inferred)** অবস্থা-নির্ভর;
2. pytest প্রসেসের ভিতরে পরীক্ষা করে দেখা গেল: `os.environ["ENV"]='test'` থাকা সত্ত্বেও **`settings.env == 'local'`** — `core.config` সিঙ্গেলটন test-infra-তে কোথাও এমনভাবে তৈরি/পুনঃলোড হয় যে ENV override কাজ করে না (conftest-এর sys.modules purge অপর্যাপ্ত);
3. ফলে টেস্টে ছাড়টা ভুলভাবে সক্রিয় হয়ে SSRF গার্ড লুপব্যাক/প্রাইভেট টার্গেট পাস করাত। **প্রোডাকশনেও** ENV-ছাড়া settings-reload হলে একইভাবে গার্ড খুলে যাওয়ার কাঠামোগত ঝুঁকি ছিল।

**ঠিক (এই সেশনে pushed):** ছাড় এখন **শুধুমাত্র স্পষ্ট opt-in** — `SUPREMEAI_ALLOW_LOCAL_MCP=1` — কোনো আনুমানিক অবস্থা নেই; ডিফল্ট **fail-closed**। বাংলা কমেন্টসহ (`core/plugins/mcp_security.py`)।
**প্রমাণ:** ওই ফাইল ৬/৬ ✓; সম্পূর্ণ `tests/security/` + `test_api_new_endpoints` = **২৯৯ passed (আগে ৩ failed)**; খরচকারীদের টেস্ট (mcp_client, security_scanner, mission_suite) ৩৯/৩৯ ✓; ruff ✓।

---

## পার্ট ৩ — ✅ এই সেশনে ঠিক হওয়া বাকি আইটেম (সব লোকাল প্রমাণ-সহ)

| ID | ফিক্স | ফাইল | প্রমাণ |
|---|---|---|---|
| **B-V2-01** (V2 থেকে ঝুলে থাকা P0, **এখন বন্ধ**) | `_router` আর production-এ `MagicMock()` বানায় না — unset = সৎ `None`; `async_generate` শুধু সত্যিই inject করা router-এ MoE শাখায় ঢোকে; `use_moe=True` + router-বিহীন হলে **loud warning**-সহ সৎ acompletion fallback; route-ব্যর্থতা debug→**warning** | `core/llm/llm_gateway/gateway.py` | টেস্ট আপডেট + **নতুন honest-fallback টেস্ট** → expert_router suite ✓ |
| **B-V2-04** (V2 থেকে ঝুলে থাকা P0, **এখন বন্ধ**) | admin JWT revocation **canonical স্টোরে ব্রিজ** — এখন `core.security.is_token_revoked(is_admin=True)` (fail-closed নীতি) ব্যবহার হয়; অনাহরণযোগ্য ভাঙা পাঠ (`jwt_blacklist:` প্রিফিক্স + `app_mod.redis_queue` + কোথাও-না-লেখা `_in_memory_jwt_blacklist`) পুরো বাদ | `api/routes/admin_auth.py` | security suite ✓; route-rbac matrix ✓ |
| B-V4-02 | plans governance: `architecture/README.md`-এ অনুপস্থিত ৫টি required frontmatter ফিল্ড যোগ | `docs/plans/architecture/README.md` | linter: ওই ৫ error নেই |
| B-V4-03 | ৫টি broken `supersedes` লিংক পুনঃস্থাপন — repo-র নিজস্ব **redirect-stub কনভেনশনে** ৫টি archive stub তৈরি (canonical-এ লিংক-সহ) | `docs/archive/plans/architecture/*.md` ×৫ | linter: broken-lineage ০ |
| D-V4-01 | `plan_registry.json` পুনঃজেনারেট (bot-এর নতুন doc সহ) | `docs/plans/plan_registry.json` | 174 docs, Crown Jewel নিবন্ধিত |

**B-V2-01-এর তীব্রতা-আপগ্রেড (নতুন আবিষ্কার):** পুরনো কোডে `(use_moe or getattr(self._router, "route", None) is not None)` — MagicMock-এর `.route` সবসময় non-None, তাই **`use_moe=False` হলেও** প্রতিটি router-বিহীন `async_generate` কল MoE শাখায় ঢুকে **ভুয়া Mock অবজেক্টকেই "text"/"content" হিসেবে ফেরত দিত** — আসল LLM ডাকই হতো না। ভাগ্যক্রমে প্রোডাকশন কোড `acompletion` ব্যবহার করে (async_generate-এর কোনো প্রোডাকশন কলার নেই — শুধু টেস্ট), তাই লাইভ ট্রাফিক নিরাপদ ছিল; কিন্তু API পৃষ্ঠটা ছিল বিষাক্ত।

**B-V2-04-এর তীব্রতা-আপগ্রেড (নতুন আবিষ্কার):** দুটি স্টোর শুধু "আলাদা" ছিল না — **কী-প্রিফিক্সই ভিন্ন** (`jwt:blacklist:` vs `jwt_blacklist:`) **এবং Redis ক্লায়েন্টও ভিন্ন** (`redis_manager` vs `app_mod.redis_queue`)। অর্থাৎ যেকোনো কনফিগারেশনেই admin রিভোকেশন-রিড **১০০% অন্ধ** — `/logout` লিখলেও admin রুট কখনো দেখতই না।

---

## পার্ট ৪ — 🔴/🟠 এখনও খোলা (হালনাগাদ তালিকা)

### P0/P1
1. **Settings-sিঙ্গেলটন পোলিউশন রহস্য (নতুন, test-infra)** — pytest প্রসেসে `ENV=test` থাকা সত্ত্বেও `settings.env='local'` (instrument-প্রমাণিত, আইডি-স্টেবল ইনস্ট্যান্স)। conftest-এর `sys.modules` purge যথেষ্ট নয়; **আলাদা সেশনে রুট-কজ বের করা দরকার** (সন্দেহ: কোনো module/fixture `importlib.reload(core.config)` বা Settings পুনর্নির্মাণ করে)। B-V4-01 এর কারণেই ধরা পড়েছে — এই পোলিউশন অন্য যেকোনো env-নির্ভর সিকিউরিটি-চেককেও বিভ্রান্ত করতে পারে।
2. **plans governance: ৫৮৬টি missing-field error** — ১৭৩ doc-এর ~১১৭-তে আংশিক frontmatter (`id`/`subject`/`document_role`/`planning_authority`/`status` অনুপস্থিত)। **এটি এখন সবচেয়ে বড় doc-debt**। প্রস্তাবিত ব্যাচ-পদ্ধতি: স্ক্রিপ্টে `id`/`subject` filename/heading থেকে, `status: proposed` (সৎ ডিফল্ট), `document_role` ডিরেক্টরি-ভিত্তিক ম্যাপিং (reviewable PR), `planning_authority` canonical ডিফল্ট — এক ব্যাচে নয়, ৩–৪ ব্যাচে।
3. **Nightly mission-gate লাইভ-যাচাই** — ফিক্স V3-এ পুশ হয়েছে; আগামী nightly-তে pass^3=1.0 আসছে কিনা দেখতে হবে; সাথে **লাল-গেট নোটিফিকেশন** যোগ করা এখনও ঝুলে আছে (B-V3-01 শিক্ষা)।
4. **Frontend ভুয়া-ডেটা জোন** — `DynamicPanel.tsx:51` `|| 42` অপরিবর্তিত; অন্যান্য F-V2 জোনও; ~৮৫+ dead file।
5. **Frontend `: any` = ৬৫**।
6. **MCP package**: `@supabase/supabase-js` এখনও অঘোষিত (dynamic import-নির্ভর registry নীরবে `[]` হতে পারে); F-14 drift (typescript 7.0.2 / zod 4.5.4 / ioredis 6.0.0)।

### P2
7. MCP Control Tower টেস্ট কভারেজ ~৭%; mutation/authority tool ১০টি অটেস্টেড; ৬ print-only suite।
8. Unbounded in-memory store (byoc vault, jobs_db, RECENT_ACTIVITIES, frontend alerts)।
9. CI evidence JSON লেখা হয় কিন্তু কেউ পড়ে না (feedback loop নেই)।
10. secrets_registry ড্রিফট (৩২ ব্যবহৃত-অনিবন্ধিত / ১৮ অব্যবহৃত); `load_exemptions()` মৃত।
11. `workspace_feature_routes.py ↔ tier_s_routes.py` আন্তঃ-re-export চক্র — ক্যানোনিক্যালে সরাসরি সংজ্ঞা নিয়ে এক bridge বাদ।

### P3 (হাইজিন/পর্যবেক্ষণ)
12. **Meta-doc মৃত দাবি অপরিবর্তিত**: `STATUS.md:77` (মুছে-ফেলা মডিউল "implemented"), `STATUS.md:110` ("Pending Tasks — None!"), `README.md:68` (অস্তিত্বহীন `MASTER_PLAN.md` লিংক)।
13. **Log-less except ~১,১৬৫/৩,৩৯৬** (heuristic; V2-এর কঠোর ক্রাইটেরিয়ায় ৬৭৬) — উচ্চ-ব্লাস্ট নমুনা V2-তে; production সাইলেন্ট pass = ২ (ডকুমেন্টেড-ইচ্ছাকৃত)।
14. পর্যবেক্ষণ: `api/routes/payments.py:62` `SUPREMEAI_ENV` সেকেন্ডারি চেক — প্রাইমারি `settings.env` চেক উপস্থিত, তাই ত্রুটি নয়, তবে env-var নামের দ্বৈততা সংহত করা ভালো।
15. `scripts/advanced_analysis/duplicate_detector.py`-এ ১৫টি pre-existing ruff নোট (F401/F541/S112/BLE001…) — এই সেশনের এডিট নয়; `scripts/` ruff-স্কোপে না থাকায় নীরব।

---

## পার্ট ৫ — ✅ রিগ্রেশন যাচাই (সব ইনভেস্টমেন্ট)

| ইনভেস্টমেন্ট | অবস্থা |
|---|---|
| V3-এর ৩টি ফিক্স | পার্ট ১ — অক্ষত |
| B-12/False-Assurance doctrine | ✓ আজকের ৪টি ফিক্সেই প্রয়োগ (বাংলা কমেন্ট + honest logging + fail-closed); নতুন AST স্ক্যানে নতুন সাইলেন্ট pass নেই |
| M3 archive guard | ✓ (V3-এ যাচাইকৃত, এই সেশনে memory কোড অপরিবর্তিত) |
| CI Pipeline main | ✓ green (fb53ad86, c7d5bb8) |

---

## পার্ট ৬ — অগ্রাধিকার-ক্রম (পরের সেশনের জন্য)

1. ~~SSRF গার্ড ফুটো~~ ✅ · ~~B-V2-01~~ ✅ · ~~B-V2-04~~ ✅ (সব আজ বন্ধ)
2. **Settings-পোলিউশন রুট-কজ** — একটি টেস্ট-ইনফ্রা সেশন; সমাধান হলে ভবিষ্যৎ env-নির্ভর ফ্লেক অনেক কমবে।
3. **Frontend batch**: `|| 42`-জাতীয় ৫ জোন + dead-file disposition + `: any` কমানো।
4. **MCP critical-১০ assert test** + supabase-js ঘোষণা + F-14 সংকোচন।
5. **Frontmatter ব্যাচ-পাস** (৫৮৬ error) — উপরের প্রস্তাবিত পদ্ধতিতে ৩–৪ PR।
6. Nightly gate লাইভ-যাচাই + লাল-গেট নোটিফিকেশন।
7. Unbounded cap-পাস + workspace-bridge চক্র সংহতি।
8. Meta-doc সততা পাস (STATUS/README)।

**যা করা উচিত নয় (বহমান):** নতুন plan doc (বাস্তবায়ন ছাড়া); dead কোড জমিয়ে রাখা; নতুন `continue-on-error`; লাল nightly উপেক্ষা; inferred env-state-নির্ভর সিকিউরিটি চেক (আজকের B-V4-01 শিক্ষা — স্পষ্ট opt-in নীতি)।

---

## পার্ট ৭ — সততার স্বীকারোক্তি

- যাচাই = static analysis + নির্বাচিত pytest সাবসেট (security ২৯৯, guard-consumers ৩৯, gateway/mission/contract ৬০+) + লাইভ CI API + in-process instrumentation; সম্পূর্ণ suite বা staging runtime-প্রমাণ নেই।
- Settings-পোলিউশনের সঠিক মূল বিন্দু (কোন মডিউল/fixture reload করে) এই সেশনে শনাক্ত হয়নি — শুধু অস্তিত্ব ও প্রভাব প্রমাণিত; রুট-কজ পরের সেশনের কাজ।
- Mission-gate ফিক্সের লাইভ-প্রমাণ আগামী nightly পর্যন্ত অমীমাংসিত (লোকালে ৫৭/৫৭ প্রমাণিত V3-এ)।
- P2/P3-এর কিছু আইটেম V2/V3 থেকে বহনকৃত (চিহ্নিত)।
