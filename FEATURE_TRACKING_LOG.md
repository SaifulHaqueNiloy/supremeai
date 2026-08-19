# FEATURE_TRACKING_LOG.md

## Feature: Static Import-Graph Auditor (scripts/import_graph_audit.py)

- **Step 1 — পরিকল্পনা (Plan):** backend/ মডিউলগ্রাফের স্ট্যাটিক অডিটর যা broken internal import, orphan module, আর reachable-closure বের করে। baseline JSON রিপোর্ট (backend/_audit_baseline.json) দিয়ে ইন্টারকানেকশন রিমেডিয়েশনের ভিত্তি স্থাপন। CI-তে 30s budget-এর মধ্যে চলতে হবে।
- **Step 2 — কার্যান্বয়ন (Implement):** single-pass `os.walk` + `ast.parse` + `scan_module` (একটি রিকর্সিভ ভিজিটে symbol + import দুটোই ধরে)। সব tree/symbol/line-count মেমোরিতে (`_MODULE_TREES`, `_MODULE_SYMBOLS`, `_MODULE_LINES`, `_MODULE_INDEX`)। resolution `module_to_path`/`module_symbols`/`is_internal` পুরোটা O(1) dict lookup (FS stat নয়)। `--scope {prod,all}` দিয়ে tests/alembic থেকে বাদ, `_SKIP_DIRS` দিয়ে .venv/.kilo/node_modules prune।
- **Step 3 — ভেরিফিকেশন (Verify):** `_t.log` ফেজবাইজ টাইমিং: populate 15.85s, lazy_map 0.01s, audit 0.03s, edges 0.02s, closure 0.01s, report+json 0.04s, মোট ~16s। `backend/_audit_baseline.json` 449,192 bytes, JSON-ভ্যালিডেটেড: 1,734 modules, 143 reachable, 1,594 orphans, 637 broken (51 live, 586 latent)। `py_compile` clean (syntax OK)।
- **Step 4 — পর্যালোচনা (Review/Deploy):** `autoDeploy: false` প্রোটোকল অনুযায়ী baseline JSON জেনারেট করা হয়েছে কিন্তু কোনো code পরিবর্তন প্রোডাকশনে প্রয়োগ হয়নি। রিমেডিয়েশন 51টি live broken import-এর উপর পরবর্তী সেশনে (LESSONS_LEARNED.md-এ গroups করা হয়েছে)।

## সাব-ফিচার: Performance Remediation of Auditor
- পরিকল্পনা: 3টি WSL /mnt stat-ইওয়্যার বাতিল করা।
- কার্যান্বয়ন: (ক) path_to_module resolve()->relative_to, (খ) _count_lines মুছে _MODULE_LINES, (গ) rglob->os.walk prune।
- ভেরিফিকেশন: 30s এড়িয়ে ~16s; log-এ DONE প্রিন্ট হয়।
- রিভিউ: merged — baseline স্থিতিশীল।
