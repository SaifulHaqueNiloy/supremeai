<!-- GENERATED FILE — DO NOT EDIT BY HAND -->
<!-- Source of truth: .github/constitution/rules.yml · Generator: scripts/ci/generate_agents_md.py -->
<!-- CI drift check: pr.yml → agents-md-sync. To change rules, edit rules.yml. -->


# SupremeAI — AGENTS.md v3 (Universal Agent Contract)

> rules_version: `4.0` · যতই ঘুড়ি উড়াও রাতে, নটাই তো আমার হাতে।
> **Agent type নয় → Task type। Task chooses capability; model does not define the task.**
> Rule layering: Admin → AGENTS.md → Security → Task → Group → Issue → Repo → History (৮-স্তর priority)

## Universal Protocols

১. **Universal Agent** — ১টিই agent টাইপ; router (scripts/agents/supremeai_orchestrator.py) DB-driven task policy পড়ে task type অনুযায়ী ১টি কাজ + dynamic instruction দেয়; সফল সমাধান LEARNING mode-এ agent_task_history-তে রেকর্ড হয়।
২. **Group Flow** — একই group:<name>-এর কাজ শেয়ার্ড গ্রুপ ব্রাঞ্চে সিকোয়েনশিয়ালি হয়; সম্পূর্ণ গ্রুপ শেষে ১টি unified PR; predecessor গ্রুপ না মিটলে merge hold; queue-র সব PR সর্বোচ্চ-অগ্রাধিকার অনুযায়ী এক-একটি করে sequential merge।
৩. **Atomic Claim** — claim ছাড়া কোড নয়: atomic_claim.sh + 'Touching files:' ঘোষণা; declared scope-এর বাইরে touch নিষিদ্ধ।
৪. **Verify First (৩-স্তর)** — Reflection (grep) → Boot smoke (python -c 'import main') → Pytest; টেস্ট ম্যানিপুলেশন (delete/skip/fake assertion) সর্বোচ্চ অপরাধ।
৫. **has-pr** — PR খুললেই সাথে সাথে gh issue edit <id> --add-label 'has-pr' — ডুপ্লিকেট PR রুট-ব্লক।
৬. **CI Guard + Heartbeat** — PR নিরাপত্তা/স্কোপ/টেস্ট CI Gates সামলায় — এজেন্ট ১০০% ফোকাসে solve+verify+atomic PR; সেশন শুরুতে Control Tower heartbeat (mcp_tower_client.py heartbeat)।
৭. **Group Closeout** — গ্রুপ শেষে Capability Harvest + 4-Pillar Rubric (Stability / Real Benefit / Zero Regression / Scope); Zero Capability Loss নিশ্চিত হলে তবেই merge।
৮. **Operational Truth** — GitHub Issues = কাজের live state, DB = operational truth; নতুন .md নিষিদ্ধ (allowlist বাদে), দীর্ঘ ডকস TelDrive-এ; নতুন গ্রুপ-ইস্যু স্ট্যান্ডার্ড টেমপ্লেটে (create_group_issue.py)।
৯. **Push-as-PR** — কাজ লোকালে জমা নয়: ব্রাঞ্চে push → (স্বাধীন কাজে সাথে সাথে / গ্রুপ কাজে গ্রুপ শেষে) PR → has-pr; সব অগ্রগতি GitHub-এ দৃশ্যমান ও অডিটেবল।
১০. **3-Pipeline Law** — PR-এ ১ গেট (PR Gate), Merge Train-এ ১ গেট (Train Gate), Main-এ ১ পাইপলাইন (Main CI/CD); ডুপ্লিকেট রান/ওয়ার্কফ্লো স্প্রল নিষিদ্ধ।

## Bootstrap

1. `git fetch origin --prune && cat AGENTS.md` — main sync + universal contract পড়ো — rules বদলেছে কিনা দেখো
2. `./scripts/agents/start agent-<N>` — Universal bootstrap: router audit + ১টি task assignment + dynamic instruction (#2504)
3. `./scripts/ci/atomic_claim.sh <issue#> <agent>` — claim না থাকলে — 'Touching files:' ঘোষণা সহ (GH_TOKEN অটো-fallback)
4. `3-Tier Verification (Reflection → Boot Smoke → Pytest)` — কোনো টেস্ট ভাঙা বা ডিলিট করা নিষিদ্ধ
5. `gh pr create ... && gh issue edit <issue#> --add-label 'has-pr'` — স্বাধীন কাজে সাথে সাথে PR; গ্রুপ কাজে সম্পূর্ণ গ্রুপ শেষে ১টি unified PR

## System Gates (CI-enforced — মনে রাখার দরকার নেই)

| Gate | কখন আটকাবে |
| :--- | :--- |
| Lease Gate | PR head branch লেখকের leased slot-এর বাইরে (bot slot-mismatch), বা mesh lease মেয়াদ শেষ |
| Verification Gate | PR description-এ Test Evidence সেকশন নেই (টেস্ট লগ/কমান্ড আউটপুট ছাড়া PR BLOCK) |
| Scope Gate | claim-এ declare করা 'Touching files:'-এর বাইরের ফাইল PR-এ বদলালে BLOCK |
| Collision Gate | অন্য open PR-এর ফাইলের সাথে direct overlap হলে BLOCK |
| Self-Merge Gate | নিজের PR নিজে approve/merge করলে BLOCK |
| Test Guard | test delete/skip/threshold-নামানো হলে BLOCK |
| Post-Merge Watch | merge-এর ১৫ মিনিটের মধ্যে main লাল হলে (watchdog admin-alert — কোনো অন্ধ auto-revert নয়, revert সিদ্ধান্ত অ্যাডমিনের নাটাইয়ে) |
| Predecessor Group Merge Hold Gate | পূর্ববর্তী গ্রুপ (Predecessor Group) সম্পূর্ণ না হলে পরবর্তী গ্রুপের PR queue:hold ছাড়া মার্জ করা নিষিদ্ধ |

## একমাত্র কঠিন নিয়ম (মোট ৭টা, বাকি সব system-এর ভার)

১. সততা ও নির্ভরযোগ্যতা: কোড ও টেস্ট ১০০% খাঁটি হতে হবে; টেস্ট ম্যানিপুলেশন (delete/skip/fake assertion) সর্বোচ্চ অপরাধ।
২. সম্পূর্ণ গ্রুপের একক PR (Full Group = 1 Unified PR): গ্রুপের প্রতিটি ইস্যুর জন্য পৃথক পৃথক PR খোলার প্রয়োজন নেই। ১ম ইস্যু শেষ হলে সরাসরি গ্রুপ ব্রাঞ্চে পুশ হবে, ২য় এজেন্ট সেই ব্রাঞ্চ থেকেই ২য় ইস্যুর কাজ করবে, এবং সম্পূর্ণ গ্রুপের সমস্ত কাজ শেষ হলে পুরো গ্রুপের জন্য মাত্র ১টি একক ও সমন্বিত PR তৈরি হবে।
৩. অবিরাম সক্রিয়তা: কিউ থেকে ক্রমানুসারে পরবর্তী কাজ তুলে নাও, কোনো কাজে ব্লকার পেলে সাথে সাথে ব্লকার ইস্যু ফাইল করে এগিয়ে যাও।
৪. বাংলা/বাংলিশ ব্যবহারের বাধ্যবাধকতা: আমাদের পুরো টেক টিম বাংলাদেশি — তাই যেখানেই সম্ভব বাংলা (বা প্রাঞ্জল বাংলিশ) ব্যবহার করতে হবে। (১) কোডের ভেতরের সমস্ত মন্তব্য ও সিদ্ধান্তের ব্যাখ্যা (code comments — e.g. '# বাংলা মন্তব্য:'), (২) অ্যাডমিনের যেকোনো প্রশ্নের উত্তর, বার্তা ও স্ট্যাটাস রিপোর্ট, এবং (৩) PR সামারি, ডেসক্রিপশন ও ইস্যু ডিসকাশনে বাংলা বা বাংলিশ ১০০% বাধ্যতামূলক (Mandatory Bengali/Banglish)। কেবল কোড সিনট্যাক্স, ভ্যারিয়েবল নেম ও শেল কমান্ড ব্যতীত সমস্ত যোগাযোগ ও ব্যাখ্যা বাংলায় হতে হবে।
৫. আর্কিটেকচার স্থায়িত্ব ও ৩-পাইপলাইন নীতি (Architecture Preservation & DRY 3-Pipeline Law): আর্কিটেকচার যেমন আছে হুবহু তেমন অক্ষত থাকবে যদি না কোনো পরিবর্তন একান্তই অপরিহার্য (until it is must)। সিআই/সিডি-তে কোনো ওয়ার্কফ্লো স্প্রল বা ডুপ্লিকেট রান থাকবে না — প্রতিটি অ্যাকশনে মাত্র ৩টি একক, DRY ও Reusable পাইপলাইন কাজ করবে: (১) PR-এ ১টি গেট (PR Gate), (২) Merge Train-এ ১টি (Train Gate), এবং (৩) Main-এ ১টি (Main CI/CD)।
৬. অগ্রাধিকার অনুযায়ী এক-একটি করে ফিক্স ও মার্জ নীতি (Fast & Effective Sequential Law): সিআই এবং ডেভেলপার সময়ের অপচয় রোধে সর্বদা সর্বোচ্চ অগ্রাধিকার (Rank 1 / P0) PR-টি আগে শতভাগ গ্রিন ও মার্জ করতে হবে, তারপর ক্রমানুসারে পরবর্তী PR-এ যেতে হবে। সমান্তরালভাবে একাধিক ইন্টার-ডিপেন্ডেন্ট PR নিয়ে টানাটানি নিষিদ্ধ।
৭. ডকুমেন্টেশন Issues-এ সংরক্ষণ ও TelDrive ব্যাকআপ নীতি (Issues as Operational Truth & TelDrive Backup): রিপোতে অপ্রয়োজনীয় .md তৈরি সম্পূর্ণ নিষিদ্ধ। সমস্ত নতুন স্থাপত্য সিদ্ধান্ত, গাইড ও প্ল্যান সরাসরি GitHub Issue-তে নথিভুক্ত হবে এবং দীর্ঘস্থায়ী ডক্স TelDrive-এ ব্যাকআপ রাখা হবে।

> স্বাধীনতা: সমাধানের বাস্তবসম্মত অ্যাপ্রোচ ও ডিজাইন প্যাটার্ন নিজে বেছে নাও। সক্রিয় গ্রুপ সিকোয়েন্সের পরবর্তী উন্মুক্ত ইস্যুটি গ্রহণ করো। কোনো ব্লকার পেলে তাৎক্ষণিক ব্লকার ইস্যু তৈরি করে পরবর্তী আনক্লেইমড কাজে এগিয়ে যাও।
> সম্পূর্ণ machine-readable rule registry: `.github/constitution/rules.yml` · task-type policy DB: `task_policies` (#2504)।
> **এই file-টি registry থেকে GENERATED — হাতে এডিট করবে না।**
