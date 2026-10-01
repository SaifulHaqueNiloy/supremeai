# LESSONS_LEARNED Archive — 2026-10
> Auto-archived by rotate_lessons.py on 2026-10-02
> Original entries: 1

## 2026-09-27 — 🧭 Lane Boundary: Planner Opens PRs (L1 Violation — Rule Gap, Closed) (#1864)


- **সমস্যা:** `agent-1-planner` দুটি PR (#1805, #1851) খুলেছিল — planner lane-এর ম্যান্ডেট হলো audit + GitHub issues only, PR নয়। Root cause ছিল agent-এর স্মৃতিভ্রংশতা নয় বরং **rule gap**: charter-এর planner row-তে `docs/plans/` ownership দেওয়া ছিল কিন্তু "Forbidden" কলামে PR খোলা নিষিদ্ধ ছিল না — "plan-doc ownership" কে "plan-doc PR authority" হিসেবে পড়া সম্ভব ছিল।
- **ফিক্স:** (১) Charter hardening — planner = **issue-output lane**, branch slot নেই, PR খোলা স্পষ্টভাবে forbidden; প্ল্যান ডকুমেন্ট `handoff:coder` issue-এর মাধ্যমে coder lane land করবে (charter §1 planner row + new invariant #23)। (২) **Machine guard** (আলাদা issue): PR gate এখন `planner-*` branch থেকে খোলা PR ব্লক করবে — নিয়ম এখন enforcement-নির্ভর, memory-নির্ভর নয়। (৩) এই ledger entry — ভুল একবার, শিক্ষা স্থায়ী।
- **লেসন:** সীমানা-নিয়ম (lane boundary) চার্টারে "allowed" লেখা যথেষ্ট নয় — যে behavior নিষিদ্ধ, সেটা Forbidden কলামে + machine guard-এ স্পষ্ট থাকতে হবে। **"Allowed scope" ≠ "authority to land"**: discovery/specification authority আর landing authority ভিন্ন জিনিস — ecosystem-এ এক lane খুঁজে দেয়, অন্য lane বানায়, আরেক lane বসায়।

---

## 2026-09-27 — 🏷️ Missing-Cat Metadata Class: Bot Wrapper-ই File Path-কে Title/Body বানিয়ে দেয় (#2158)

- **Issue:** #2158 — PR #2156 `supremeai-coder-1-bot` খুলেছিল যার title = `/tmp/wire_title.txt`, body = `/tmp/wire_body.md` (literal path strings)। Wrapper চেয়েছিল `--title "$(cat "$F")"`, পাঠিয়েছে path। Rule #16/#17 violation; triage/labeler/pr-verifier pipeline poisoned।
- **Fix:** repo-side pre-create assert — `scripts/agents/validate_pr_metadata.py` (path-like title/body BLOCK — absolute, dotted-relative, এবং no-whitespace+known-extension heuristic; conventional `type(scope): description` title BLOCK (Rule #16); stub body BLOCK (Rule #17); গেট contract WARNING — body-তে exactly-one keyword ref (`Refs #N`) না থাকলে/১-এর বেশি হলে, title-এ `(#N)` না থাকলে; `--strict` warning-কে abort বানায়; `--format json` wrapper-দের জন্য)। Tests: `backend/tests/scripts/test_validate_pr_metadata.py` — literal #2156 evidence strings সহ 19 tests। Per-agent sandbox wrapper-ও এই validator-কে pre-POST এ call করে (fix যেখানে বাগ, সেখানেই)।
- **লেসন:** (১) shell-এ `"$F"` আর `"$(cat "$F")"`-এর পার্থক্য হলো path-vs-contents — bot wrapper-এ এই class-এর বাগ metadata-কে silently garbage করে কারণ আজকের CI title check warning-level; (২) "যা CI asynchronously ধরে তা pre-create এ fail-fast করাও" — gate contract (exactly-one `Refs #N`) validator-এ mirror করা হয়েছে; (৩) per-agent tooling repo-তে না থাকলেও, তার contract repo-visible হওয়া উচিত — shared validator + tests সব slot একসাথে রক্ষা করে।