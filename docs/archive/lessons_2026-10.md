# LESSONS_LEARNED Archive — 2026-10
> Auto-archived by rotate_lessons.py on 2026-10-02
> Original entries: 1

## 2026-09-27 — 🧭 Lane Boundary: Planner Opens PRs (L1 Violation — Rule Gap, Closed) (#1864)


- **সমস্যা:** `agent-1-planner` দুটি PR (#1805, #1851) খুলেছিল — planner lane-এর ম্যান্ডেট হলো audit + GitHub issues only, PR নয়। Root cause ছিল agent-এর স্মৃতিভ্রংশতা নয় বরং **rule gap**: charter-এর planner row-তে `docs/plans/` ownership দেওয়া ছিল কিন্তু "Forbidden" কলামে PR খোলা নিষিদ্ধ ছিল না — "plan-doc ownership" কে "plan-doc PR authority" হিসেবে পড়া সম্ভব ছিল।
- **ফিক্স:** (১) Charter hardening — planner = **issue-output lane**, branch slot নেই, PR খোলা স্পষ্টভাবে forbidden; প্ল্যান ডকুমেন্ট `handoff:coder` issue-এর মাধ্যমে coder lane land করবে (charter §1 planner row + new invariant #23)। (২) **Machine guard** (আলাদা issue): PR gate এখন `planner-*` branch থেকে খোলা PR ব্লক করবে — নিয়ম এখন enforcement-নির্ভর, memory-নির্ভর নয়। (৩) এই ledger entry — ভুল একবার, শিক্ষা স্থায়ী।
- **লেসন:** সীমানা-নিয়ম (lane boundary) চার্টারে "allowed" লেখা যথেষ্ট নয় — যে behavior নিষিদ্ধ, সেটা Forbidden কলামে + machine guard-এ স্পষ্ট থাকতে হবে। **"Allowed scope" ≠ "authority to land"**: discovery/specification authority আর landing authority ভিন্ন জিনিস — ecosystem-এ এক lane খুঁজে দেয়, অন্য lane বানায়, আরেক lane বসায়।