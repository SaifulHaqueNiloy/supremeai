# SupremeAI V8 চক্র (2026-09-17): পূর্ণ অটোমেশন বাস্তবায়ন — ১২টি সুযোগ, এক কমিট

**স্কোপ:** "complete them all" — অটোমেশন-অডিটের ১২টি সুযোগের বাস্তবায়ন (backend + frontend + CI)
**দর্শন:** প্রতিটি আইটেম zero cost (GitHub-native/বিদ্যমান স্ক্রিপ্ট), lightweight, mostly-dynamic (baseline/ডেটা ফাইল-চালিত, কোনো লজিক-হার্ডকোড নয়)
**পূর্ববর্তী চক্র:** V7 (`f2311d92` + evidence-fix `3b318c4f`/`fc3df7a7`)

---

## ১. বাস্তবায়িত অটোমেশন (৯টি ফাইল-লেভেল পরিবর্তন + লোকাল ইনস্টল)

| # | অটোমেশন | বাস্তবায়ন | ধরন |
|---|---|---|---|
| ১ | Local hooks ইনস্টল | `setup-git-hooks.sh` চালানো হয়েছে + `pre-commit install` — **`.git/hooks/pre-push` ও `pre-commit` এখন সক্রিয়** (আগে config ছিল, ইনস্টল ছিল না!) | one-command |
| ২ | Pre-push CI-Parity Matrix | `scripts/git/pre-push` সম্প্রসারিত: গেট ১ ruff format, গেট ২ ৫×generator drift (auto-regen + auto-commit + push-again), গেট ৩ mission suite (শুধু protected push)। `SKIP_CI_PARITY=1` bypass — এখন সত্যিই কাজ করে | hook |
| ৩ | Generator auto-regen | গেট ২-এর অংশ — backend/scripts বদলালে তবেই চলে (dynamic skip), drift হলে commit তৈরি করে আবার push বলে | hook |
| ৪gap | CI ব্যর্থতার সৎ tracking | nightly-র নিজস্ব issue লজিক আগেই ছিল; নতুন **CI Doctor** workflow সেই ফাঁক বন্ধ করে: job-level crash-এও live jobs API থেকে ব্যর্থ job-তালিকাসহ issue | workflow |
| ৫ | Evidence drift auto-fix bot | CI Doctor-এর অংশ: drift শুধু `docs/generated/`-এ হলে auto-regen + `[skip ci]` commit + push — লুপ-নিরাপদ; অন্য ফাইল জড়িত হলে সৎভাবে বিরত | workflow |
| ৬ | Evidence artifact guard | `ci-advanced-checks.yml`: নীরব "No files found"-এর বদলে দিকনির্দেশক বার্তা (if-no-files-found: error বহাল — কঠোরতা কমেনি) | ১ ধাপ |
| ৭ | Pydantic→TS/Dart টাইপ অটো-সিঙ্ক | `maintenance.yml`: `generate_types.py` (বিদ্যমান স্ক্রিপ্ট) এখন DocBot-এর nightly-তে, shared-types auto-commit | nightly |
| ৮ | লাইভ Status Proof | নতুন `scripts/ci/build_status_proof.py` + daily job: প্রকৃত mission suite চালিয়ে `docs/generated/STATUS_PROOF.md` auto-commit; STATUS.md-তে দাবি নয়, শুধু লিংক | daily job |
| ৯ | Changelog auto-gen | নতুন `scripts/ci/generate_changelog.py` (conventional commits → বাংলা-গ্রুপড bounded রিপোর্ট) + সাপ্তাহিক job | weekly |
| ১০ | `: any` burn-down ratchet | নতুন `scripts/ci/check_any_budget.py` + `frontend/any_budget.json` (ডেটা ফাইল, বর্তমান প্রকৃত সংখ্যা **৫৭**) + ci.yml গেট: বাড়লেই লাল, কমলে baseline-টাইটেন পরামর্শ | per-PR gate |
| ১১ | knip সাপ্তাহিক dead-file রিপোর্ট | নতুন `scripts/ci/knip_summarize.py` (defensive parser) + weekly job → rolling issue (report-only — owner doctrine: bot মোছে না) | weekly |
| ১২ | i18n key-gap | নতুন `scripts/ci/check_i18n_keys.py` (warn-only): কোডে ব্যবহৃত কিন্তু translations.ts-এ অনুপস্থিত key-এর দৃশ্যমানতা — কিছুই ভাঙে না | weekly |

**প্রমাণিত কাজকৃত:** ৫টি নতুন স্ক্রিপ্ট লোকালে চালিয়ে আউটপুট যাচাই (any=57, i18n missing=0, changelog 670 commits grouped, knip=86 unused files, proof exit 0)।

---

## ২. সচেতন সিদ্ধান্ত (যা করা হয়নি, কেন)

- **auto-lint-fix-এর weekly schedule যোগ করা হয়নি** — এটি PR-তৈরি করে; pre-push hook-ই formatter drift এখন মূলেই আটকায়, দৈনিক PR-spam ঝুঁকির দরকার নেই (manual dispatch বহাল)।
- **৬৫→৫৭ `any` ম্যানুয়ালি ঠিক করা হয়নি** — ratchet গেটই এই চক্রের অটোমেশন; বাল্ক টাইপ-চেঞ্জ = ভাঙার ঝুঁকি। সংখ্যা এখন দৃশ্যমান ও বাউন্ডেড।
- **knip/i18n কে CI-ফেইলিং করা হয়নি** — report-only; owner wire-or-delete ও অনুবাদ-সিদ্ধান্ত মানুষের।

## ২-খ. হুক ফরেনসিক: ৩টি প্রি-একজিস্টিং ভাঙা গেট প্রমাণসহ ঠিক (V8-এর সবচেয়ে বড় পাওয়া)

প্রথম লাইভ push-টেস্টই ৩টি লুকানো ব্যর্থতা ধরল — **এটাই pre-commit/pre-push কেউ ইনস্টল না করার কারণ ছিল**:

| # | ভাঙা গেট | প্রমাণ | সৎ ফিক্স |
|---|---|---|---|
| F-1 | **SyncGuard pre-push invocation doubly-fake** | `backend.src.agents...` মডিউল পাথ নেই → প্রতিটি push ব্লক (লাইভে প্রমাণিত); সঠিক পাথেও `__main__` নেই → `-m` নীরব exit 0 (fake gate); এবং Redis+network চায় (প্রতি-push স্তরে ভঙ্গুর) | push লেয়ার থেকে বাদ; এজেন্ট কোড repo-তে অটুট — nightly-CI ক্যান্ডিডেট হিসেবে নথিভুক্ত |
| F-2 | **.pre-commit-config.yaml-এ gitleaks ভুল রিপোতে** | `pre-commit/pre-commit-hooks` রিপোতে gitleaks হুক নেই → env init সবসময় fail → সবার first commit-ই abort (লাইভে প্রমাণিত) | ভাঙা এন্ট্রি বাদ; সিক্রেট-কভারেজ অটুট (detect-private-key + secret-hunter + CI gitleaks) |
| F-3 | **Observability gate always-red** | ৫০টি ঐতিহাসিক violation → প্রতিটি commit ব্লক = গেটটি কার্যত ডিসেবলড | `--baseline` ratchet (নতুন `scripts/observability_baseline.json`, ৫০টি exact-string); নতুন violation-ই শুধু ব্লক; লাইভ টেস্ট: exit 0, "50 tolerated, 0 new" |

**পাঠ:** "গেট সবসময় লাল" = গেট নেই। Ratchet (নতুন-ব্লক/পুরনো-সহন) এই ভাঙা গেটগুলোকে সৎ ও টেকসই করে — কিছু ভাঙে না, নতুন সমস্যা ঢুকতে পারে না।

---

## ৩. CI-নিরাপত্তা প্রটোকল মেনে চলা হয়েছে (V7-পাঠ)

- নতুন ৫টি `scripts/ci/*.py` যোগে **capability matrix drift প্রত্যাশিত ছিল** — স্ক্রিপ্টগুলো git-add করার **পরে** generator চালানো হয়েছে; drift = ঠিক ৫টি নতুন এন্ট্রি (2795→**2800**), assertion পাস।
- সব workflow YAML `yaml.safe_load` দিয়ে যাচাই।
- নতুন স্ক্রিপ্টগুলো `ruff check` + `ruff format --check` পরিষ্কার (chmod +x সহ)।

---

## ৪. যাচাই-ম্যাট্রিক্স

| যাচাই | ফলাফল |
|---|---|
| ৫ workflow YAML parse | ✅ |
| ৫ নতুন স্ক্রিপ্ট ruff (check+format) | ✅ |
| ৫ নতুন স্ক্রিপ্ট লাইভ আউটপুট | ✅ (উপরে) |
| Mission suite | ✅ 57/57 |
| Matrix assertion | ✅ 2800 modules |
| Local hooks ইনস্টল | ✅ pre-push + pre-commit সক্রিয় — **এই push-ই hook-এর প্রথম লাইভ টেস্ট** |

---

## ৫. প্রত্যাশিত CI-প্রভাব

- পরের লাল CI-তে (যদি হয়): CI Doctor issue খুলবে + drift হলে নিজেই ঠিক করবে।
- পরের রাত ২টায় (UTC): status-proof কমিট হবে।
- আগামী সোমবার: প্রথম weekly hygiene issue।
