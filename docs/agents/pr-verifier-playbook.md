# PR-Verifier Playbook (agent-8) — PR Bot Helper & Trainer

> **Role:** agent-8 = `pr-verifier` (AGENT_SLOT_REGISTRY.yaml)
> **Charter:** "PR helper bot decision check + code quality. Fixes wrong merges"
> **Position in handoff-orchestration** (docs/agents/handoff-orchestration.md, #1445):
> `planner → solver-a ∥ solver-b → handoff:verify → **pr-verifier** → handoff:browser-test → browser-tester → handoff:done`
> **Established:** 2026-09-26, after fix run #1 (6 mistakes found, all fixed)

---

## 1. আমি কী করি (Role in one line)

solver-a (agent-6) / solver-b (agent-7) PR খোলার **পরে** আমার কাজ শুরু:
১) PR-এর **content verify** (diff vs base), ২) **plumbing verify** (branch name, gate, mergeability),
৩) ভুল পেলে **fix**, ৪) ভুলের কারণ থেকে **training rule** বানানো যাতে PR bot আর repeat না করে।

আমি merge করি না — merge মানুষের সিদ্ধান্ত (pr-helper.yml owner decision 2026-09-24)।
আমি verdict দিই: `PASS / NAMING-FAIL / GATE-FAIL / SUPERSEDED / STALE / UNVERIFIED`।

## 2. Fix Run #1 — যা যা ভুল ধরা পড়ল (2026-09-26)

| ID | ভুল | Evidence | Fix | Rule |
|---|---|---|---|---|
| M1 | Branch naming: dash instead of slash (`agent-11-fix-1421-…`) → guard+gate FAIL | #1532, #1535 | valid rename থেকে নতুন PR (#1536/#1537) | R1 |
| M2 | PR খোলার পরে branch rename → stranded PR (dead head ref) | #1532, #1535 | same-sha re-open + close w/ verdict comment | R2 |
| M3 | Artifact-regen PR flood: sibling check নেই → ১১ open PR জমল | #1481–#1531 | ১০টা superseded close (evidence comment), #1531 রাখা | R3 |
| M4 | Guard fail → PR Helper diagnostics skip (review signal হারায়) | #1532, #1535 check-runs | naming ঠিক করলে helper নিজেই আবার চলে | R8 |
| M5 | Stale PR-কে অন্ধ rebase candidate ভাবা — content direction main-এ বদলে গেছে (#1426/#1479), merge করলে doc DOWNGRADE হতো | #1435 | close `not_planned` + salvage pointer (d485218e) | R6 |
| M6 | Same-sha-তে পুরনো FAIL + নতুন PASS check-run — array order ambiguous, ভুল run পড়ার ঝুঁকি | #1536, #1537 | per-check-name **id-desc latest** পড়া | R7 |

## 3. Training Rules — PR bot-এর checklist

### R1 — Push-এর আগে branch name validate
OPS-06 regex (branch-naming-guard.yml):
```
^(agent-[a-zA-Z0-9_-]+/issue-[0-9]+-.+|agent-[0-9]+|feat/.+|fix/.+|hotfix/.+|perf/.+|chore/.+|test/.+|docs/.+|refactor/.+|ci/.+|dependabot/.+|github-actions/.+|renovate/.+|pr-helper/.+|develop|main)$
```
- ✅ `agent-11/issue-1421-registry-persist` · ✅ `agent-11-longrun/issue-1439-…` · ✅ `fix/…` `ci/…`
- ❌ `agent-11-fix-1421-registry-persist` (slash নেই)
- নোট: `agent-11-longrun/…` regex-এ পাস করে কারণ `agent-[a-zA-Z0-9_-]+/` অংশটা `-longrun`-ও নেয়।

### R2 — PR খোলার পরে branch rename কখনো না
rename লাগলে সঠিক অর্ডার: **(১)** নতুন নামে branch push → **(২)** নতুন PR খোলো →
**(৩)** পুরনো PR-এ pointer comment + close। উল্টো করলে PR stranded (head ref 404)।

### R3 — regen/bot PR খোলার আগে open sibling খোঁজো
একই drift-set-এ open sibling থাকলে নতুন না খুলে sibling update/skip।
Queue-তে এক সময়ে **≤২টা** artifact PR।

### R6 — পুরনো PR rebase-এর আগে content-DIRECTION diff
behind/diverged ≠ rebase candidate। main-এ ওই approach replace হয়েছে কিনা আগে দেখো
(#1426 registry rewrite যেমন fixed-slot model বদলে দিয়েছিল)। Replace হলে:
close `not_planned` + salvage pointer (commit sha), **কখনো merge না**।

### R7 — Gate reading: per-check-name LATEST run
একই head sha-তে একাধিক run থাকে (rename+re-open করলে)। প্রতিটি required check-এর
**শেষ run**-ই verdict — check-runs API-র order ভরসাযোগ্য না, **id-desc sort করে নাও**।

### R8 — Guard fail → Helper skip প্রত্যাশিত cascade
Branch guard fail হলে PR Helper Step 1–3 skip হয়। কাজ হলো naming ঠিক করা —
valid PR খুললে helper নিজেই আবার চলবে। Skip দেখে আলাদা করে debug করতে যেও না।

---

## 2b. Fix Run #2 — post-merge স্তরের ভুল (2026-09-26, পরের রাউন্ড)

Fix Run #1 শুধু open PR দেখেছিল; Fix Run #2 দেখাল **merge-এর পরেও ভুল হয়** —
post-merge audit স্তর ছাড়া এগুলো চিরকাল অদৃশ্য থাকত:

| ID | ভুল | Evidence | Fix | Rule |
|---|---|---|---|---|
| M7 | **লাল গেট দিয়ে merge (gate-bypass):** guard+gate দুটোই FAILURE হওয়ার ~২ মিনিট পরে merge | #1530 (03:56 fail → 03:58 merge), helper skipped | engine-এ 48h bypass-audit + #1530-তে evidence comment + R9 | R9 |
| M8 | **"main CI full-green" দাবি, অথচ main HEAD লাল:** PR-green → main-red divergence; ৯০ মিনিটে ৬টা fix(ci) PR whack-a-mole | #1542→#1559; fc158f8b-তে pass^k + Security Aggregate লাল; be0cb34-তে Advanced Pre-Merge + Constitution Audit লাল ([issue #1565](https://github.com/SaifulHaqueNiloy/supremeai/issues/1565)) | engine-এ mainHealth live check + issue ফাইল | R10 |
| M8-obs | PR head ৯/৯ সবুজ, merge commit-এ ২টা লাল — base divergence মিলিত অবস্থায় ভাঙে, PR-এ দেখা যায় না | #1561 (head 752fc5b সবুজ → main be0cb34 লাল) | mainHealth প্রতি HEAD-এ নতুন করে পড়ে | R10 |

### R9 — লাল গেট = merge না, কোনো অজুহাত নেই
guard/gate FAILURE থাকলে merge নিষিদ্ধ। গেট ভুল মনে হলে সঠিক অর্ডার:
**(১)** কেন লাল বের করো → **(২)** গেট-কনফিগ ভুল হলে আলাদা `ci/` fix PR →
**(৩)** সবুজ হলে merge। লাল অবস্থায় merge করলে required check-এর অর্থই শেষ (M7)।

### R10 — PR-green ≠ main-green
"full-green" দাবির আগে **main HEAD-এর aggregate checks** নিজে দেখো (pass^k,
Security Aggregate, Constitution Audit, Advanced Pre-Merge…)। Merge-এর পরেও একবার —
কারণ মিলিত main-অবস্থায় ভাঙা কিছু PR head-এ ভাঙে না। আর CI fix সাইকেল শুরুর আগে
পুরো suite একবার চালিয়ে **সব failure-family এক PR-তে** ঠিক করো — প্রতি symptom-এ
এক PR whack-a-mole নয় (৬ PR/৯০ মিনিট = review-queue noise)।

### Self-caught (agent-8 নিজের ভুলও লেজারে যায়)
Fix Run #2-তে আমার নিজের tooling GitHub **search API-র 422**-কে "issue নেই" ভেবে
**ডুপ্লিকেট issue (#1565, #1566)** বানিয়ে ফেলেছিল — সাথে সাথে ধরা পড়ল, #1566
close (not_planned) + dedupe logic list+scan-এ বদলাল। নিয়ম: **tool নিজে verify
করো তার আউটপুটের আগে** — ত্রুটির মানে "নেই" না, "অজানা"।

## 4. Verdict engine (v2 — post-merge স্তর সহ)

Live engine: Z.ai preview console → **PR Verify tab** (`/api/pr-verify`, 60s cache)।
খোলা PR-গুলোতে উপরের নিয়মগুলো machine-check হয় এবং per-PR verdict + reason দেখায়।
Mistake Ledger + Training Rules সেখানেও live দেখা যায়।

**v2 যোগ (Fix Run #2):**
- `mainHealth` — main HEAD-এর সব check-run লাইভ পড়ে: fail/cancelled/skipped গণনা,
  aggregate/meta gate-এর লাল তালিকা (R10 machine-check)
- `bypassAudit` — শেষ ৪৮ ঘণ্টার merged PR-গুলোর head-sha check-runs ঘেঁটে
  লাল guard/gate দিয়ে merge হওয়া সবাই ধরে (R9 machine-check) — এখন পর্যন্ত ১টা (#1530)

## 5. Heartbeat

agent-8 slot 45s cadence-এ ping করে (status=working, task field-এ বর্তমান verification
কাজ) — ফলে orchestrator (agent-10) জানে PR-verifier জীবিত ও ব্যস্ত।

---

*agent-8 · pr-verifier · "PR bot-এর কাজ সহজ করা, ভুল ধরা, বারবার না করানো"*

## 2c. Fix Run #3 — root-cause গভীরে: lint gate flip-flop (2026-09-26, এই রাউন্ড)

Fix Run #3-এর প্রশ্ন ছিল: **কেন main এতবার লাল?** উত্তর পাওয়া গেল job log ঘেঁটে —

- **instance-3 নিশ্চিত**: #1561/#1562/#1567 — তিনটাই merge-এর মুহূর্তে PR-head **9/9 সবুজ**;
  merge-commit f8daa8c-এ 6 fail + 13 skipped (M8 এখন ×3)
- **root-cause (Backend Prepare)**: `poetry run ruff check . --select E,W,F,I,N,UP,B,SIM --ignore …`
  → I001 ×2 (`backend/core/mcp_client.py:139`, `backend/tools/mcp/mcp_server.py:2`)
- **নতুন ধরনের শিক্ষা — gate-এর রায় environment-dependent**: একই pinned ruff
  (0.16.4) + একই args লোকাল pip-ruff-এ ঐ ২ ফাইল **pass**, বরং ৩টা **ভিন্ন** I001
  ধরে (`api/routes/admin_routes.py:982`, `admin_v1.py:184`, `living_brain.py:28`)।
  এমনকি CI-র log প্রিন্ট করা reorder `ruff check --fix` লোকালে apply-ই করে না।
  অর্থাৎ **blind fix PR এখানে flip-flop বানাবে** — নিষিদ্ধ।
- **প্রতিকার (upstream #1565-এ প্রস্তাব)**: (১) canonical lint invocation
  (`--config backend/pyproject.toml` / make target) যাতে local == CI; (২) repo-র
  নিজস্ব `alembic_migrations` precedent অনুযায়ী per-file-ignores; (৩) post-merge
  gate verify workflow
- **agent-8 engine fix (নিজের ভুল)**: mainHealth failures-এ `url` ফাঁকা থাকত —
  `latestPerName` এখন `html_url` বহন করে; dashboard-এর প্রতিটা failing job এখন
  clickable + `meta-gate` badge + M8-live chip (#1565 লিংক, instance count সহ)

### R10 সমৃদ্ধ (আপডেট) — "green" দাবির আগে runner-ও মিলাও
শুধু main HEAD দেখো না — **gate যে runner/entrypoint-এ চলে সেটাও নিজের সাথে মিলাও।
একই version-এর লিন্টার ভিন্ন venv-এ ভিন্ন রায় দিতে পারে; fix PR খোলার আগে fix-টা
প্রমাণ করো যে context-এই যেখানে gate চলে।** পার না হলে সেটাই রিপোর্ট — flip-flop
fix নয়, reproducibility issue।


## 2d. Fix Run #4 — cron-যুগের প্রথম সাইকেল: policy sync + ৩৪-merge audit (2026-09-27)

প্রথম ৩০-মিনিট cron run (boss-authorized autonomous cadence)। ১৫ ঘণ্টার উইন্ডো অডিট করা হলো।

### পলিসি sync (প্রতিটি run-এ বাধ্যতামূলক)
- AGENTS.md এখন Rule #12–#23 (#2009): NO SELF-MERGE, ONE ACTIVE CLAIM, BRANCH FROM MAIN ONLY, NO FORCE-PUSH, PR TITLE/DESCRIPTION ENFORCED, NO CROSS-BRANCH PUSH, MANDATORY MCP TOWER CONNECT (45s heartbeat), FILE DECLARATION ON CLAIM, NO TEST MANIPULATION, POST-MERGE REGRESSION CHECK (15min-এ main লাল = auto-revert), RULES RE-READ ON CHANGE।
- GOLDEN_RULES 8→10 (#9 no-self-merge/force-push/test-cheating, #10 tower-connect + file-declare)। Charter invariants #11–#22।
- Workflow-স্থাপত্য: merge-train-rollup.yml → integration-gate.yml, pr-pipeline.yml → pr-gate.yml (Branch Naming Guard এখন pr-gate-এ absorbed, #1857); 45→19 consolidation।

### নতুন ভুল যা ধরা পড়ল (ledger M9/M10 + M7 count 1→4)
- **M9 — duplicate check-run names**: BNG ×2 প্রতি PR-এ, batch-এ ×3 (#2154 ফাইল করা)। ইঞ্জিন id-desc latest-per-name নেয় — duplicate-safe; তবু duplicate-count আলাদা দেখাও।
- **M10 — chronic-red PR-level চেক**: "Record merge learning report" ৩৪/৩৪ merged head-এ লাল, তবুও ৩৪ mergeই landed (#2155 ফাইল করা)। R12: চিরকাল-লাল চেক হয় ঠিক হবে নয় স্পষ্টভাবে তালিকামুক্ত হবে।
- **M7 instances 2–4**: #2086 (founder Tier-3 ঘোষিত override — `tier-3-override` label convention প্রস্তাব), #2054 (bot-merge + collision red — সম্ভবত #2115 self-collision বাগ), #2043 (batch + Cascade Land red)।
- **M8 RESOLVED**: CI consolidation ভাঙা ruff invocation সরিয়েছে; main 444a5242 = 22ok/0fail; #1565 RESOLVED। Rule #22 এখন এই ক্লাস machine-enforce করে।

### ইঞ্জিন sync
- OPS06_BRANCH_REGEX এখন live pr-gate.yml pattern-এর mirror (slot-pool naming সহ) — হাতে এডিট করার আগে pr-gate.yml দেখো।

### cron-নীতি (নতুন)
- প্রতিটি run: (১) worklog handoff, (২) policy sync (fetch + AGENTS.md/RULES_INDEX/GOLDEN_RULES diff), (৩) watch-diff + re-anchor, (৪) list+scan dedupe-সহ issue (নীরব ডুপ্লিকেট নয়), (৫) নিজের lane-এ fix, lane-এর বাইরে শুধু issue, (৬) worklog + Bangla রিপোর্ট।
- নীরবতা-নীতি: ট্রানজিয়েন্ট (মিনিট-খানেক পুরোনো) লাল ক্লাস্টারে সাথে সাথে issue নয় — পরের run-এও টিকে থাকলে তবেই issue; systemic (সব PR-এ একই প্যাটার্ন) হলে সাথে সাথেই।

### Task 21 addendum (cron run #2, 2026-09-27 15:36Z)
- **M11/R13 নতুন**: coder-1-bot-এর PR wrapper title/body-এর জায়গায় temp-file PATH পাঠায় (#2156 = "/tmp/wire_title.txt") — Rule #16 ভায়োলেট। ইঞ্জিনে titleValid (lenient Rule #16) + dashboard ✗ title chip যোগ হলো। শিক্ষা: script থেকে metadata এলে render-যাচাই বাধ্যতামূলক।
- **#2157 ফাইল করা (root-cause সহ)**: Security Aggregate Gate প্রতিটা নতুন PR-এ লাল — কারণ upstream security-scan job **skipped**, আর gate `test "$SECURITY_RESULT" = "success"` করে। skipped ≠ failure — #1565-এর সেইম ক্লাস এবার PR-লেভেলে।
- **bypassAudit cap 20→50** — ৩৪ merge/15h velocity-তে পুরোনো cap bypass instance miss করছিল।
- cron-নীতি প্রমাণিত: transient-cluster wait-1-cycle নীতিতে Security Aggregate ধরা পড়ল ২য় snapshot-এই → systemic হিসেবে file হলো।

### Task 22 addendum (cron run #3, 2026-09-27 16:04Z)
- **M12/R14 নতুন — stale-state race**: batch #2151 (2149+2150) merged 15:46:44Z → মাত্র ২৮ সেকেন্ড পরে অটোমেশন merged #2150-এর জন্য `type:blocker` conflict issue (#2159) খুলে বসাল — stale-on-arrival, তবুও priority-queue-তে blocker slot দখল করে। #2161 ফাইল করা (timeline evidence সহ)। **R14: অটোমেশন-আউটপুট ফাইল করার আগে target-এর CURRENT state re-fetch বাধ্যতামূলক** — snapshot সেকেন্ডেই পুরনো হয়; আমার নিজের issue-creation script-এও এই guard যোগ হবে।
- **bypassAudit সংশোধন + সত্য-নেগেটিভ যাচাই**: per_page 40→100 (churn-heavy repo-তে updated-sort sample-এ 48h merge হারাত); flag শর্ত এখন BNG/UPG ছাড়াও সব aggregate gate (gate|pre-merge|aggregate|security|reliability|audit) — তবে chronic "Record merge learning report" (M10) ইচ্ছাকৃতভাবে বাদ। Debug প্রমাণ: 38 merged-48h head-এ latest-red শুধুই M10 chronic চেক → **bypassCount=0 এখন যাচাইকৃত সত্য-নেগেটিভ** (পুরনো M7 red গুলো merge-এর পরে re-run হয়ে success — R7 অনুযায়ী latest-ই verdict)। Task 21-র open thread বন্ধ।
- **M9 count 7→8**: #2156 head-এ BNG ×7 + ১০ নাম ×6, #2153 ×5/×6, #2109/#2015 ×2 — ডুপ্লিকেট এখন প্রতিটা fresh head-এর স্থায়ী বাস্তবতা; #2154-এ upstream pickup এখনো নেই।
- **পর্যবেক্ষণ**: ৪টা tracker issue (#2154/#2155/#2157/#2158) সব still 0 comments — পরের run-এও pickup না হলে কোনোটায় ১টা follow-up comment (নতুন evidence থাকলেই) বিবেচনা করব। #2153/#2156 founder নিজে bisect করে queue:hold ফ্রিজ করেছেন (#2160 batch fail → bisect halves) — ওদের নিয়ে আমার আলাদা issue দরকার নেই।
- **নতুন শিক্ষা (dedupe script)**: নিজের collision-heuristic-এ খালি "merged" keyword false-positive দিয়েছিল (#2155-এর টাইটেল) — collision rule combo-based হতে হবে (scanner-word AND state-word), নইলে নিজের নীরবতা-নীতিই নিজেকে আটকে দেয়।

### Task 23 addendum (cron run #4, 2026-09-27 16:30Z)
- **M12 ভ্যালিডেট হলো**: প্রতিষ্ঠাতা নিজেই #2159 বন্ধ করেছেন (16:24Z) — কারণ হিসেবে লিখেছেন "PR #2150 landed in main via rollup batch PR #2151" — অর্থাৎ stale-on-arrival ডায়াগনোসিস (#2161) সরাসরি কনফার্ম; তবে #2161-এ এখনো কোনো রেসপন্স নেই, scanner-এ state-guard এখনো আসেনি → M12 fixed:false থাকছে।
- **BIG POSITIVE — branch protection এখন LIVE (#1993 P0 closed)**: main-এ required_status_checks = Branch Naming Guard + Unified PR Gate, allow_force_pushes=false, allow_deletions=false, dismiss_stale_reviews=true — Task 19-এর "single merge door কাগজে-কাগজ" গ্যাপ এখন GitHub-লেভেলে machine-enforced। R9 আর শুধু নীতি নয়, enforcement।
- **#1992/#2029 reopened** (founder triage wave — সাথে #1991/#2004/#2006/#2019-এ কমেন্ট): #1992 মানে learning_guards exit-0 swallow = M10-এর chronic-red-এর ঠিক মূল সংযোগ — fix এখন ঘুরছে।
- **Tracker-ধৈর্য নীতি কাজ করছে**: ৫টা tracker (#2154/#2155/#2157/#2158/#2161) silent — কোনো স্প্যাম-কমেন্ট করিনি; নতুন ইভিডেন্স এলে তবেই ১টা কমেন্ট।
- এই চক্রে নতুন issue নেই (সব পর্যবেক্ষণ existing tracker/পজিটিভ সিগন্যালে ম্যাপ করে) — restraint নিজেই একটা সিদ্ধান্ত।

### Task 24 addendum (cron run #5, 2026-09-27 17:01Z)
- **M12 instance-2 ধরা পড়ল — নতুন variant**: #2164 (ci-2, #2029-fix) superseded হয়ে closed-NOT-merged হলো 17:00:48Z (একই fix ব্যাচ #2163-এ আগেই ল্যান্ড করেছিল) — মাত্র ৬ সেকেন্ড পরে scanner **#2168** খুলে দিলো "PR #2164 has merge conflict"। অর্থাৎ stale-window শুধু merge-ল্যান্ডিংয়ের সময় নয় — **যেকোনো close (merge বা reject)-এর পরেই** snapshot পুরনো হয়। #2161-এ ১টা evidence comment দিলাম (নীতি মেনে: নতুন evidence থাকলেই কেবল ১টা); নতুন issue ফাইল করিনি — একই root। M12 count 2→3।
- **পলিসি sync**: main e7807103→6a64510c→2ebcb92d (দ্রুত ব্যাচ-ল্যান্ডিং চলছে); নতুন workflow slot-registry-drift.yml (+40) = reopened **#2029-এর fix ল্যান্ডেড** → #2029 closed। AGENTS.md/rules অপরিবর্তিত।
- **#2153/#2162 closed-NOT-merged** (founder) — bisect-frozen সদস্য বাদ, superseded নতুন PR-এ। বৈধ পদক্ষেপ, issue নেই।
- **Security Aggregate Gate এখনো প্রতিটা fresh PR-এ লাল** (#2167 fail, #2156-র নতুন head-এও fail) — #2157 এখনো silent; tracker-ধৈর্য চলছে।
- **Ops**: :3000 মৃত পাওয়া গেল → nohup restart, 200। আর fetch timeout ১বার → retry সফল (UNKNOWN ≠ not-exists প্রয়োগ)। agent-8 branch-এ ৩টা কমিটই আমার (১৬:৩৩Z-এর 7e4fb41f = Task 23 push) — foreign push নেই।

### Task 25 addendum (cron run #6, 2026-09-27 17:30Z)
- **পলিসি পরিবর্তন (ছোট, গুরুত্বপূর্ণ)**: planner lane-এর branch slot সম্পূর্ণ বাদ — "(none — issue-output lane)"; plan docs এখন `handoff:coder` issue-তে (#1864)। Charter-এ planner এখন PR/branch/push তিনটাই ❌। agent-8/pr-helper lane-এ প্রভাব নেই।
- **#2158 → PR #2171 in-flight**: আমার temp-file-title issue coder-1-bot নিয়েছে (labeled 17:09Z → branch 17:14Z → PR 17:15Z — ৬ মিনিটে পুরো চেইন)। #2171 merge হলে M11 fixed:true। ফ্লিট-লুপ কাজ করছে প্রমাণ।
- **SAG re-verify (নীরব)**: #2173-এর fresh failing log টেনে দেখলাম — mechanism অপরিবর্তিত (`SECURITY_RESULT: skipped` + `test = success`)। নতুন evidence নেই → #2157-এ কমেন্ট নয়; ধৈর্য ৪র্থ চক্রেও।
- **#2168 (M12 instance-2) এখনো open** — scanner state-guard আসেনি; ২ চক্র ধরে stale blocker issue ঝুলছে।
- **নতুন check-name নোট**: "Single CI Execution Gate" (#2171 head) — suite বদলাচ্ছে; engine-এর gate-name list generic regex-এ আছে বলে code change দরকার নেই।

### Task 26 addendum (cron run #7, 2026-09-27 18:03Z)
- **Ops**: session-এর মাঝে /home/z/supremeai clone ও tower deps মুছে গিয়েছিল → re-clone + `bun install` (mcp-control-plane) + tower/:3000 restart — ৪ পোর্ট সবুজ। Policy sync: main 06d67fc1 অপরিবর্তিত → এই চক্রে zero diff।
- **coder-1 backlog sweep শুরু**: পুরনো issue #1619/#1743/#1748 (মাস-পুরনো) ৩০ মিনিটে claim→branch→PR (#2176/#2175/#2174) — #2019 priority-queue-ledger-ই চালিকাড়া। ফ্লিটের issue→fix পাইপলাইন এখন backlog পর্যন্ত পৌঁছাচ্ছে।
- **SAG census (নতুন পদ্ধতি — evidence-এর মান উন্নত)**: শেষ ~৯টা merge-eligible head-এ ৫/৯ SAG-red; কিন্তু **counter-example পাওয়া গেল** — #2170 (merged) SAG=success, #2169 SAG=absent → গেটটা "প্রতিটা PR-এ লাল" নয়, **অনির্দিষ্ট/inconsistent**। পার্থক্যটা মূল ফাইন্ডিং: run-vs-skip deterministic না। Task 25-এর প্রি-অথরাইজড ট্রিগার পূরণ (৩০ মিনিটে ৩টা নতুন PR লাল) → #2157-এ ১টা census comment (issuecomment-5858404714) — শুধু নতুন তথ্য, নয়-দোষারোপ টোন।
- **M12 VALIDATION-2**: coder-1 lane নিজেই #2168-এ triage দিলো — "stale-on-arrival — recommend close" (API-verified #2164 closed+unmerged) = scanner-family-র স্ব-স্বীকারোক্তি। তবু issue open → blocker slot দখল চালু। Ledger-এ গেল, #2161-এ আর কমেন্ট নয় (validation ≠ নতুন problem-evidence)।
- **Founder-এর #2177 (critical)**: vault-doctor — Upstash Redis REST token invalid, manual action দরকার। agent-8 lane নয়; cache-fallout পর্যবেক্ষণে রাখো।
- **Merge watch**: #2171 (আমার #2158-এর fix) ও #2173 — দুটোই `pr-gate:passed` + `queue:pending-rollup`; merge হলে M11 fixed:true বিবেচনা।
- **এই চক্রে নতুন issue শূন্য, কমেন্ট ১ (#2157)** — census ছিল genuinely নতুন: inconsistency + operational-impact (SAG-red head বহনকারী PR-এ `pr-gate:passed` label, train উপেক্ষা করছে)।

### Task 27 addendum (cron run #8, 2026-09-27 18:31Z)
- **মার্জ-ট্রেন সার্কিট-ব্রেকার লাইভ দেখা গেল**: pr-helper lane ২টা ব্যাচ চেষ্টা করলো — #2178 (2173+2176), #2179 (2174+2175); UPG PASS করেও **Batch CI fail** → প্রতিষ্ঠাতা blind-retry না করে **bisect + queue:hold ফ্রিজ** (ডিজাইন-মতোই) → উভয় ব্যাচ closed-NOT-merged। ফল: #2171/#2173/#2174/#2175 সব queue:hold — M11-এর merge watch আরও দূরে সরল।
- **Epistemics লেসন (নিজের সম্পর্কেই)**: Task 26-র census-এ "train SAG-কে উপেক্ষা করছে" বলেছিলাম — ৩০ মিনিটের মাথায় #2178/#2179 প্রমাণ করলো operational picture বদলায় (SAG-red member বহনকারী ব্যাচ fail+freeze হলো)। **Operational-impact দাবির শেলফ-লাইফ ছোট** — এক window-এর প্যাটার্ন পরের window-এ মিথ্যা হতে পারে; দাবির সাথে window উল্লেখ করো।
- **Token-identity ফাঁদ**: ইভেন্ট-ফিডে "#2157 comment by SaifulHaqueNiloy" দেখে ভাবলাম প্রতিষ্ঠাতা সাড়া দিয়েছেন — আসলে **আমারই census comment** (vault GITHUB_TOKEN প্রতিষ্ঠাতার অ্যাকাউন্টে post করে)। pickup আসলে নেই; verify করো comments লিস্ট টেনে, actor-name দেখে সিদ্ধান্ত নয়।
- **#2180** (StepApiKey removal, #1744 fix) জন্মেই SAG-red কিন্তু pr-gate:passed + pending-rollup — census-এর সাথে সামঞ্জস্যপূর্ণ।
- **Cross-PR File Collisions** এখন ৪টা frozen member-এই লাল — ব্যাচ-fail-এর সন্দেহভাজন ড্রাইভার, কিন্তু bisect মেশিনারি মালিকানা নিয়েছে; পরের চক্রে bisect-resume-এর পরেও লাল থাকলে তবেই job-log খুঁড়ব। আগে issue নয় (premature)।
- **এই চক্রে: 0 নতুন issue, 0 কমেন্ট** — ব্যাচ-ব্যর্থতা = ডিজাইনড সার্কিট-ব্রেকার (issue নয়), সব পর্যবেক্ষণ tracker-এ ম্যাপ করে। #2168 stale-blocker ৩য় চক্র ধরে খোলা (coder-1-এর নিজের "recommend close"-এর পরেও)।

### Task 28 addendum (cron run #9, 2026-09-27 19:03Z)
- **ENV ROLLBACK INCIDENT (২য়বার)**: session-এর মাঝে /home/z স্ন্যাপশট ~17:32Z-এ ফিরে গেছে — worklog-এর Task 26/27 এন্ট্রি, playbook-এর দুই addendum, ledger M12-লাইন, r26/r27 স্ক্রিপ্ট, repo clone, tower deps সব মুছে গিয়েছিল। **সেলফ-হিলিং প্যাটারন কাজ করলো**: playbook origin/agent-8 থেকে ফেরানো হলো (remote = authoritative backup!), ledger লাইন conversation-record থেকে re-edit, worklog verbatim পুনর্লিখন (RECOVERED ট্যাগ সহ)। **শিক্ষা: প্রতি addendum push করা শুধু রিপোর্টিং নয় — এটা ডিজাস্টার-রিকভারি; remote agent-8 branch-ই আমার একমাত্র durable storage।**
- **Cross-PR File Collisions = ডিজাইনড strict mode**: annotation পড়েই রহস্য ভাঙলো — "Direct file collision detected with another open PR. PR is BLOCKED (Rule: cross-pr-collision strict mode, #2002)"। এটা false-positive bug নয় — #2002-এর নিয়ম কাজ করছে; rebased সদস্যরা পরস্পর/অন্য open PR-এর সাথে ফাইল শেয়ার করে। **Check-name-এর গভীরে যেতে হলে annotations endpoint সবচেয়ে সস্তা পথ** (job-log 404 হলেও annotations আসে)। ব্যাচ-বডির "file-disjoint PRs" বাক্যটা boilerplate — বিশ্বাস কোরো না, check-এ বিশ্বাস করো।
- **Squash-train display nuance**: #2180 batch #2190 (একমাত্র member) দিয়ে ল্যান্ড করেছে কিন্তু PR নিজে closed+unmerged দেখায় — rollup squash-এ স্বাভাবিক; "closed-NOT-merged" দেখলেই সমস্যা ভাবো না, batch member list cross-check করো।
- **Founder issue-flood #2181–#2188** (payments/Gmail OAuth/CVE bump/schema-drift/TS errors...) — বৈশিষ্ট্য+সংশোধন ঢেউ; আমার tracker-গুলোর সাথে কোনো ওভারল্যাপ নেই (dedupe scan করা হয়েছে)।
- **এই চক্রে: 0 নতুন issue, 0 কমেন্ট** — collision-red ডিজাইনড, SAG-red census-এ ঢাকা, সব পর্যবেক্ষণ mapped। #2168 ৪র্থ চক্রেও open; #2157 census অবাসন্তর; #2177 silent।

### Task 29 addendum (cron run #10, 2026-09-27 19:31Z)
- **M10 RETIRED — প্রথম filed-issue যাচাই-বন্ধ পর্যন্ত গেল**: root-cause (#1992 exit-0 swallow) fix #2015 main-এ ল্যান্ড করেছে (8291cd94, 19:04:29Z); যাচাই পদ্ধতি — fix-এর পরে তৈরি ৩টা rebased head-এর FULL suite টেনে chronic check-এর verdict দেখা: ৩/৩ই **skipped** (৪৩-৪৪/৪৪ completed), failure শূন্য। Ledger M10 fixed:true; #2155-এ verification-close চাওয়া হলো (একটাই কমেন্ট, প্রি-অথরাইজড)। **শিক্ষা: chronic-red-এর মৃত্যু যাচাই করতে হয় post-fix fresh head-এ, suite-completion % সহ — আংশিক suite-এ 'absent' আর 'skipped' গুলিয়ে ফেলা যাবে না।**
- **Rebase-চক্রের Collisions-নিঃশেষণ**: ২য় rebase-ঢেউয়ে #2173/#2174-এর Collisions লাল হারিয়ে গেছে (ওভারল্যাপিং PR ল্যান্ড করায় সেট ছোট হয়েছে) — strict-mode টেম্পোরাল; যাচাইয়ের সময় head-এর বয়স মাথায় রাখো।
- **ব্যাচ-ছন্দ ফিরেছে**: #2192 (member #2189) 19:10Z, #2198 (member #2197) 19:29Z ল্যান্ডেড; **#2194 (2156+2176) আবার Batch-CI-fail → bisect+freeze** — একই সার্কিট-ব্রেকার, তৃতীয়বার দেখা গেল, প্যাটার্ন স্থিতিশীল। #2109 closed-unmerged (dead-code refactor বাদ) — লিজিট।
- **#1096 (P1 প্রোডাকশন-সার্টিফিকেশন গেট) REOPENED** — coder-1 lane-skip করেছিল (capability mismatch: runtime evidence দরকার); founder ফিরিয়ে এনেছেন — পর্যবেক্ষণে থাক, agent-8 lane নয়।
- **এই চক্রে: 0 নতুন issue, ১ কমেন্ট (#2155, যাচাই-প্রমাণ)**; M10 fixed:true — এজেন্টের প্রথম পূর্ণ-চক্র মিস্টেক-অবসান (ফাইল → ট্র্যাক → root-fix ল্যান্ড → যাচাই → ক্লোজ-অনুরোধ)।

### Task 30 addendum (cron run #11, 2026-09-27 20:03Z)
- **ENV ROLLBACK (৩য়বার) — recovery এখন routine**: snapshot ~19:03Z-এ ফিরেছিল; worklog 28/29, ledger M10-edit, playbook addenda, সব স্ক্রিপ্ট, clone, tower আবার মৃত। স্ট্যান্ডার্ড ড্রিল (~৫ মিনিট): re-clone → tower bun install+restart → playbook origin/agent-8 থেকে (৪৭7d2103-এ Task 29 addendum সহ নীরবে সংরক্ষিত ছিল) → ledger/worklog conversation-record থেকে verbatim re-apply। **পুনরাবৃত্তি-সহনশীল নিয়ম: প্রতিটা চক্রের নতুন knowledge-এর অন্তত একটা কপি সেই চক্রেই remote-এ যেতে হবে।**
- **R14 সাইকেলের hero**: scanner-এর ৪টা নতুন conflict-issue (#2232/#2233/#2234/#2236 — #2200/#2176/#2175/#2171 টার্গেট, batch #2231 merge-এর ২৩-৫২ সেকেন্ডের মধ্যে) প্রথম দৃষ্টিতে M12 race-এর মতো লাগছিল; কিন্তু **CURRENT mergeable_state টানলাম → চারটাই dirty = সত্যিকারের conflict** (batch-ল্যান্ডিংয়ে main এগোনোর ফল)। Scanner এবার সঠিক — false-positive নয়, M12 count বাড়েনি। **সন্দেহ থাকলেই state re-fetch; সিদ্ধান্ত snapshot-এ নয়।**
- **#2154-এর নতুন অস্ত্র — divergent-verdict duplicates**: "Check Cross-PR File Collisions" **×৬** এক head-এ (#2200: failure×2, cancelled×3, success×1!) + "Record merge learning report" ×৩ (batch #2231 head: failure/skipped/skipped) ও ×৪ (পরের head)। একই নামের N-instance race করলে required-check-এর কার্যকর verdict শেষ-completing instance-এর হাতে — branch protection live হওয়ায় এটা এখন gate-integrity সমস্যা। #2154-এ ১টা census কমেন্ট (issuecomment-5859379929)।
- **M10 merge-context আংশিক নিশ্চিত**: #2235-এর ৪ instance সব skipped ✅ কিন্তু #2231-এর ৩-এর মধ্যে ১টা failure — duplicate-instance-এর একটা এখনো লাল; আমার #2155-কমেন্টের hedge ("পরের merged head-গুলো দেখব") এই পর্যবেক্ষণ ঢেকে দিয়েছে — আর কমেন্ট নয়, ডেটা জমতে দাও।
- **#2156 landed via batch #2231 squash** (PR display closed-unmerged — স্বাভাবিক); **#2174 dropped** (openapi.json untrack — follow-on সমস্যা #2203-তে ইতিমধ্যে ফাইলড)। **#2235 (batch 2230) এখনো চলছে, FAIL: Advanced Pre-Merge Checks** — পরের চক্রে দেখা।
- **এই চক্রে: 0 নতুন issue, ১ কমেন্ট (#2154)**; মনে রাখো: খারাপ template-literal-এ অনাকৃত backtick = script parse-error → কমেন্টই যায় না (lint-ও ভাঙে); ফিক্স করে re-run — কোনো duplicate-কমেন্ট ঝুঁকি নেই কারণ parse-fail = POST-ই হয়নি।

### Task 31 addendum (cron run #12, 2026-09-27 20:30Z)
- **POLICY EPOCH-CHANGE (Task 31-এর মাথাব্যথা)**: PR #2238 (collective memory + mandatory MCP connect, #2237) ল্যান্ডেড — AGENTS.md নতুন দর্শনে পুনর্লিখিত ("ঘুড়ি ও নাটাই" — agent পদ্ধতিতে স্বাধীন, বাউন্ডারি কন্ট্রোল-প্লেনের), GOLDEN_RULES 8→10, **Rule 19 এখন Collective Memory বাধ্যতামূলক করেছে**: সমস্যায় আগে `agent_solution_memory.py search` দিয়ে অতীতের প্রমাণিত সমাধান খোঁজো, নতুন সমাধান পেলে DB + LESSONS_LEARNED.md-এ পথ পাকা করো। **মনে রাখো: আমার playbook-addendum push-চক্র এই মতবাদেরই বাস্তবায়ন — remote agent-8 branch = আমার paved pathway।**
- **M10 RESIDUAL এখন 4/4 সিস্টেম্যাটিক — hedge-এর ডেটা-থ্রেশহোল্ড পার হলো**: post-fix প্রতিটা merged **member** head-এ (#2231, #2173, #2238, #2200) ≥১টা "Record merge learning report" instance **সত্যিই চলে exit 1** (annotations: সব একই "Process completed with exit code 1", merge-এর *পরে* start) — অথচ rollup head (#2239/#2240) ও open-PR head-এ সব skipped। Task 29-এর যাচাই open-head-প্রসঙ্গে সঠিক ছিল; merge-context-এ রেসিডুয়াল আলাদা রোগ (duplicates-race নয় — বাস্তব ব্যর্থতা যা #2015-এর exit-$RC প্রচার এখন বের করে আনছে)। **কখন আর কমেন্ট করব: যখন জমা ডেটা আমার আগের দাবির hedge পাল্টায় বা মান-বাড়ায় — তখন ১টা কমেন্ট pre-authorized (#2155-এ issuecomment-5859607669); নইলে ডেটা জমতে দাও।**
- **ব্যাচ-মেশিনারি নতুন রূপ**: এবার rollup-শাখা নয় — **member PR-গুলো direct merge** (#2238/#2173/#2200 নিজেরা merged=true) আর তাদের rollup (#2239→#2240) উভয়ই closed-NOT-merged (Constitution Audit fail)। পুরনো "member ল্যান্ড = rollup squash" মডেল বদলেছে বা founder ম্যানুয়ালি merge করছেন — squash-train display nuance এখন উভয় মোড cover করুক।
- **#2241 = CI Doctor-এর auto-tracker** (মূল CI ব্যর্থতা বাংলায় auto-file) — CI-failure পরিবারের নিজস্ব lane; আমার main-HEAD যাচাই (d77237d 2ok/4skip/0fail) বলছে main সবুজ, তাই tracker-টা workflow-level ব্যর্থতার; ওভারল্যাপ নেই, কমেন্ট নয়।
- **Tooling নিট শেষ**: push-playbook commit-label স্থায়ী "fix-run #4" দেখাচ্ছিল — regex stale; এখন সর্বশেষ `### Task N addendum` থেকে লেবেল আসে।
- **এই চক্রে: 0 নতুন issue, ১ কমেন্ট (#2155, merge-context রেসিডুয়াল টেবিল)**; #2168 ৬ষ্ঠ চক্র, #2177 ৪র্থ চক্র silent — ক্লান্তিহীন পর্যবেক্ষণই ভূমিকা।

### Task 32 addendum (cron run #13, 2026-09-27 21:05Z)
- **MAIN-RED ঢেউ + founder-দাবি (M8-ক্লাস লাইভ অডিট)**: #2242 মার্জের পরপরই main faf96bc4-এ ৩ ব্যর্থতা — (১) Backend Tests (fast) exit 1, (২) Advanced Pre-Merge (ডাউনস্ট্রিম: release-evidence.json অনুপস্থিত, `if-no-files-found: error` ইচ্ছাকৃত কঠোর), (৩) Regen drift self-heal rc=1। **Founder ২১:০০Z-এ #2241 claim করেন** — root-cause তিনিই চিহ্নিত: "#2173-এর Pydantic contracts-এর সাথে ৪টা test payload ভাঙা" — অর্থাৎ নিরাপত্তা-ফিক্সের post-merge regression, CI Doctor tracker-এ দাবীকৃত। **আমার সিদ্ধান্ত: 0 issue / 0 কমেন্ট** — ট্র্যাকড+দাবীকৃত ঢেউয়ে নয়েজ যোগ নয়; শুধু "Regen self-heal রেসিডুয়াল" পর্যবেক্ষণে (#2230-এর নিজের স্ক্রিপ্টের জব; founder-এর ফিক্স ল্যান্ডের পরেও লাল থাকলে তবেই আলাদা প্রমাণ-কমেন্ট)।
- **M10 রেসিডুয়াল ৫/৫ — কিন্তু ৩য় কমেন্ট নয়**: #2242 head-এও 1 failure + 5 skipped; Task 31-এর নোট অনুযায়ী ৫/৫ হলো, তবু ডায়াগনোসিস বদলায়নি → কমেন্ট-স্প্যাম শৃঙ্খলা > ডেটা-পুনরাবৃত্তি। কমেন্টের শর্ত: প্যাটার্ন বদলাবে (rollup/open-head-এও ছড়াবে, error-বার্তা বদলাবে) বা founder সাড়া দেবে।
- **#2230 stale-on-arrival**: তার openapi-ফিক্স #2242 squash-এ ল্যান্ড করেছে (commit message-এ স্পষ্ট) কিন্তু PR নিজে এখনো open — ট্রেন বন্ধ করবে; "ল্যান্ডেড কিন্তু open" দেখলে commit-message-এ member-তালিকা চেক করো (squash-train নিউয়ান্সের নতুন মুখ)।
- **#1748 অবশেষে বন্ধ** (openapi উৎস-অফ-ট্রুথ সম্পূর্ণ); **#2234 (scanner conflict-issue) founder বন্ধ করেছেন** — Task 30-এর ৪-ফায়ার ধীরে পরিষ্কার হচ্ছে।
- **Env-key ওয়ার্নিং ক্রস-লিংক**: Advanced Pre-Merge-এর annotation-এ `UPSTASH_REDIS_QUINARY/QUATERNARY_REST_TOKEN` "not yet classified" — #2177-এর Redis-token পরিবারেরই সম্প্রসারণ; ওয়ার্নিং-স্তরেই আছে, ব্যর্থতা নয়।
- **এই চক্রে: 0 নতুন issue, 0 কমেন্ট** — সবকিছু ট্র্যাকড (#2241 founder-claimed) বা ডেটা-সঞ্চয়ী (M10 ৫/৫); বেসলাইন @21:03Z; main-red = M8-ওয়াচ সক্রিয় (Rule #22-এর ১৫-মিনিট auto-revert এবার ট্রিগার হয়নি — founder direct-squash করেছেন)।

### Task 70 addendum (verifier cron #418870 resumed, 2026-09-28 16:06–16:40Z)
- **M13/R15 জন্ম — আমার নিজের false-green**: main HEAD (9710b763) check-runs-এর প্রথম পাতা (per_page=100) পড়ে failure=0 দেখে 'main fully green' প্রায়-সিদ্ধান্ত; পূর্ণ pagination (171 runs) ৯টা failure বের করে আনল (services, Playwright E2E, QA Contract ×2, Advanced Pre-Merge, Op Tooling, Security Aggregate, Security Scan, Constitution Audit, Regen-drift)। ইঞ্জিনের mainHealth-ও দুভাবে মিথ্যা সবুজ ছিল: (১) single-page fetch, (২) in-flight re-run (conclusion=null) latestPerName-এ জিতে আগের completed failure ঢেকে দিচ্ছিল। **নিয়ম R15: full pagination (short-page পর্যন্ত) + completed-only resolution + API-blip = UNKNOWN → re-fetch; 'empty = green' কখনো না।** ইঞ্জিন প্যাচ (agent-8 lane): getCheckRuns() ৩-পাতা helper + mainHealth-এ completed-filter + MainHealth.pending ফিল্ড — যাচাইকৃত: failures=9 নিখুঁত, pr-verify.tsx রেন্ডার OK (M13+R15 UI-তে দৃশ্যমান)।
- **Re-run settle করে attribution আরও মজবুত**: owner আমার #2358 attribution (5872759816)-এর পর ১৪৭টা re-run চালিয়েছিল; সব completed হওয়ার পরেও services লাল — deterministic bug-ই (মানে re-run-transient নয়), #2366 (planner-এর safe-import fix) প্রাসঙ্গিক থাকল।
- **নতুন policy-tension, issue #2374**: supremeai-planner[bot] এক রাতে ৭টি fix-PR (#2362–#2373) — কিন্তু #1864 চার্টার + RULES_INDEX Layer-2 বলছে planner = issue-output only। ৭/৭-ই 🎯 Scope Gate (claim declaration) + Security Aggregate fail, ৩/৭ 🔐 Verification Gate (test logs) fail — বট-PR জন্মগতভাবে gate-চুক্তি পূরণ করতে পারে না; gate summary গুলো খালি (self-correct অসম্ভব)। Founder-এর দুই-পথ সিদ্ধান্ত প্রস্তাব (A: চার্টার সংশোধন + বট PR-জেনারেটরে gate-artifact; B: issue-output-এ ফেরা)। 121 open issue স্ক্যান করে dedupe — আগে ট্র্যাকড ছিল না।
- **Policy-sync পদ্ধতি-নোট**: contents API-র sha = **blob-sha**, কিন্তু worklog-এ সবাই **commit-sha** লগ করে (AGENTS.md b8cabe29 …) — blob-sha মিলিয়ে 'পলিসি বদলেছে!' সিদ্ধান্তে যেও না (আমি নিজেই প্রথম প্রোবে গোলমাল করেছিলাম)। নির্ভরযোগ্য পথ: `/commits?path=<file>&since=<last-run>` — last-touched commit সরাসরি। এই চক্রে policy drift = শূন্য (AGENTS.md b8cabe29, RULES_INDEX ded4d7a3, GOLDEN_RULES a850efa9 — Task 68-এর সমান)।
- **ENV নোট**: /home/z/supremeai clone আবার নিখোঁষ (env-rollback পরিবার) — push-playbook-এর জন্য agent-8 single-branch re-clone; ড্রিল এখন ~২ মিনিট। আর /api/pr-verify-এ refresh-এর সঠিক ক্রিয়া **GET** (?refresh=1) — POST 405 দেয়; কোল্ড compute ~৫৫s নেয়, timeout তাই রাখো।
- **এই চক্রে: ১ নতুন issue (#2374), 0 কমেন্ট** — প্ল্যানার-প্রতি-PR সমস্যাগুলোর নিজস্ব tracker আছে (#2361–#2371), main-red-ও ট্র্যাকড (#2358/#2365/#1565); কমেন্ট-স্প্যাম শৃঙ্খলা বজায়।
