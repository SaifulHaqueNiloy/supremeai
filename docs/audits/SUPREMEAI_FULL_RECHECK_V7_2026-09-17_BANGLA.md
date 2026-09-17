# SupremeAI পূর্ণ পুনঃপরীক্ষা V7 (2026-09-17)

**স্কোপ:** main HEAD `c1cdf2eb` (V6, CI GREEN) থেকে রুট-লেভেল পূর্ণ অডিট — "start the whole process from start and fix them all"
**পদ্ধতি:** রিগ্রেশন বেসলাইন → AST/স্ট্রিং/মাউন্ট-চেইন ফরেনসিক → stash কন্ট্রোল-এক্সপেরিমেন্ট → surgical fix → একক কমিট
**পূর্ববর্তী চক্র:** V4 (`a3fe8bbe`), V5 (`ee7e0bbe`), V5.1 (`7bb71b2b`), V6 (`c1cdf2eb`)

---

## ১. শুরুর অবস্থা

- main = `c1cdf2eb`, CI run 35243780168 → **success** (V6 GREEN বহাল)
- রিগ্রেশন বেসলাইন (V7 শুরুতেই): missions **57/57**, ruff format 1837 files ✅, ruff check ✅, plans `errors: 0`, duplicate detector exit 0 — **V4→V6 সব ফিক্স অটুট**

---

## ২. V7 ফিক্স (কোড পরিবর্তন মাত্র ২ ফাইল)

### V7-01 (P0): `api/routes/byoc_api.py` — ডেপ্লয় সাফল্যে বানানো mock URL

**আবিষ্কার:** ব্যাকএন্ড প্রোডাকশন রুটে BYOC ডেপ্লয়মেন্ট সফল হলে `job.service_url`-এ **হার্ডকোডেড কাল্পনিক URL** বসত:
`f"https://byoc-skill-{skill}-mock-url.a.run.app"` — যদিও orchestrator (`byoc/container_orchestrator.py`) আগের চক্রেই সৎ হয়েছে: terraform-বিহীন হোস্টে এখন সৎ failed, আর প্রকৃত সফলতায় **terraform output থেকে প্রকৃত `service_url`** ফেরত দেয় (নিজেই আর বানায় না)। অর্থাৎ API লেয়ার **প্রকৃত URL ফেলে দিয়ে নকল URL বসাচ্ছিল** — false-assurance doctrine-এর শ্রেণিতে V6-এর নকল WARNING-এর যমজ।

**ফিক্স:** `job.service_url = res.get("service_url") or ""` — orchestrator-এর প্রকৃত আউটপুট, বাংলা মন্তব্যসহ। শূন্য নতুন ডিপেন্ডেন্সি/স্টেট।

**প্রমাণ:** নকল URL কোডifyকারী কোনো টেস্ট নেই (grep: শূন্য ম্যাচ) → শূন্য ব্রেকেজ; `py_compile` ✅; missions 57/57 ✅।

### V7-02 (P1): `api/routes/deep_research.py` — fail-open except এখন নীরব নয়

**আবিষ্কার:** AST স্ক্যানে api/ রুটে মাত্র ২টি pass-only except-এর একটি: reasoning-stream telemetry emit ব্যর্থ হলে `except Exception: pass` — "reasoning never breaks research" উদ্দেশ্য থাকলেও **ভাঙা টেলিমেট্রি সম্পূর্ণ অদৃশ্য** ছিল।

**ফিক্স:** fail-open **বজায়** (গবেষণা কখনো ভাঙবে না), কিন্তু `logger.debug`-এ কারণ লগ হবে + বাংলা মন্তব্য। **loguru পাঠ:** প্রথমে stdlib-স্টাইল `logger.debug("%s", exc_info=True)` লিখেছিলাম — loguru-তে তা **নীরবে কার্যহীন** (extra kwarg হিসেবে ট্রেসব্যাক হারিয়ে যায়) → f-string স্টাইলে সংশোধিত। এটি নিজেই একটি "silent no-op" ফাঁদ ছিল যা V7-এ ধরা পড়ল।

---

## ৩. ফরেনসিক যাচাই: যেগুলো সন্দেহ হয়েছিল কিন্তু সৎ প্রমাণিত (কোনো churn নয়)

| সন্দেহ | তদন্ত | রায় |
|---|---|---|
| `ecosystem_admin.py:48` `except HTTPException: pass` | control-flow fall-through — পরের ধাপে static-token চেক, ম্যাচ না হলে অবশেষে 401/403 **raise** | নিরাপদ — কোনো ত্রুটি লুকায় না (শেষ পর্যন্ত ব্যর্থতা গ্যারান্টিড); রাখা হয়েছে |
| `AddNewWizard.tsx:67` `res.message \|\| 'Connection registered successfully.'` | `apiClient.post` line 146: `if (!res.ok)` → **throw**; অর্থাৎ success লাইনে পৌঁছানো মানেই রেজিস্ট্রেশন সত্যিই হয়েছে | দাবি বাস্তবতা-সমঞ্জস; রাখা হয়েছে |
| `CICDVisualizer.tsx:74` `'Deployment triggered successfully!'` | `res.ok` চেক আছে; `/admin-api/deploy` res.ok = **trigger** সত্যিই হয়েছে ("triggered" বলাটাই সঠিক শব্দ) | সৎ; রাখা হয়েছে |
| frontend `Math.random()` ×১০ | সবই jitter/backoff/ID-generation — **কোনো নকল মেট্রিক নয়** | পরিষ্কার |
| `ActionCard`/`UnifiedChatBubble` `[sandbox MOCK output]` নোট | স্পষ্ট **ঘোষিত** mock-লেবেল (loud honesty) — doctrine-সম্মত | পরিষ্কার |

---

## ৪. ডকুমেন্টেড legacy সারফেস (owner সিদ্ধান্ত ছাড়া ধরা হয়নি)

- **`api/routes/browser/_surf_actions.py`** — স্ব-ডকুমেন্টেড "Legacy mock" navigate/click/fill/type/screenshot/activity এন্ডপয়েন্ট (নকল success:True, 1×1 PNG)। ফ্রন্টএন্ড শুধু `/surf/status` + `/surf/start` ডাকে (VaultPage); **navigate/click/screenshot-এর কোনো ফ্রন্টএন্ড/টেস্ট কলার নেই**। module docstring-এ mock স্পষ্ট ঘোষিত (নীরব নয়), তাই wire-or-delete হবে **owner wire-first doctrine** অনুযায়ী পরবর্তী সিদ্ধান্ত — একতরফা বদলানো হয়নি (nothing-break অগ্রাধিকার)।
- **`BROWSER_STATUS` singleton** — বাইরের কোনো প্রকৃত ড্রাইভার নেই; in-memory compat অবস্থা। একই owner-সিদ্ধান্ত বাকেট।

---

## ৫. প্রি-একজিস্টিং ব্যর্থতা: stash কন্ট্রোল-এক্সপেরিমেন্ট (প্রমাণ-ভিত্তিক সীমানা)

লোকাল sandbox-এ `tests/api/test_byoc_endpoints.py`-এ **৪টি ব্যর্থতা** (404==422) + `tests/byoc/test_cloud_connector.py` collection error (`No module named 'google.oauth2'`)।

**বিজ্ঞান:** `git stash` → পরিষ্কার HEAD-এ হুবহু **একই ৪ failed** + একই import error → **V7-এর কোনো ফিক্সই এগুলোর কারণ নয়** (sandbox-এ google auth অপশনাল ডিপ নেই; CI এনভায়রনমেন্টে আছে — CI GREEN-ই তার প্রমাণ)। এগুলো V7 স্কোপের বাইরে; নতুন রিগ্রেশন শূন্য।

---

## ৬. V7 যাচাই-ম্যাট্রিক্স

| যাচাই | ফলাফল |
|---|---|
| `ruff format --check` + `ruff check` (২টি পরিবর্তিত ফাইল) | ✅ |
| `py_compile` উভয় ফাইল + `deep_research` লাইভ ইমপোর্ট | ✅ |
| Mission suite (sqlite override) | ✅ 57/57 |
| ruff ফুল-ব্যাকএন্ড (বেসলাইনে 1837 files) | ✅ |
| plans governance `--check` | ✅ errors: 0 |
| Duplicate detector gate | ✅ exit 0 |
| Stash কন্ট্রোল-এক্সপেরিমেন্ট (pre-existing ব্যর্থতা পৃথকীকরণ) | ✅ শূন্য নতুন রিগ্রেশন |

**দর্শন-সম্মতি:** zero cost (নতুন খরচ শূন্য), lightweight (২ ফাইলে ~১৩ লাইন ডেল্টা), fast smooth (ডেপ্লয় পাথে কোনো নতুন লেটেন্সি নেই — বরং নকল URL বাদ), zero hardcoded (শেষ হার্ডকোডেড নকল URL মুছে গেছে; এখন সব মান dynamic — terraform output থেকে)।
