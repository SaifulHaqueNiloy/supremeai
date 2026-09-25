# SupremeAI — Plan Archival Log

> **ইকোসিস্টেম দর্শন:** কোনো ফাইল মুছে ফেলা হয় না। প্রতিটা conflicted ফাইল
> `docs/archive/plans/`-এ `archive-dry-branch` হিসেবে থাকে — ইতিহাসের শিক্ষা।

**তৈরি:** 2026-09-25 · **মোট archived:** ৭টা (এই PR-এ) + ২০টা (PR #1210)

---

## এই PR-এ archived ফাইল (৭টা)

প্রতিটা ফাইল একটি কোর প্ল্যানের বিপরীত ছিল। কারণ সহ archive করা হলো:

| ফাইল | কোর | কারণ | পাথ |
|---|---|---|---|
| cloudflare_7node_global_edge_mesh_plan | CP07 | মাল্টি-অ্যাকাউন্ট কোটা ভায়োলেশন (ToS abuse) | features/ |
| kaggle_6node_cluster_compute_plan | CP07 | ফেক Kaggle অ্যাকাউন্ট + headless bots (ToS violation) | features/ |
| production_upgrade_implementation_plan_v2 | CP07 | Istio/Kong/NATS — ৫১২MB Render-এ অসম্ভব (fantasy engineering) | infrastructure/ |
| cloud_ai_multi_provider_deployment_plan | CP02 | কাল্পনিক GCP Cloud Run URL (কোডে নেই) | infrastructure/ |
| Plan_03_Continuous_Learning | CP03 | Qdrant conflict — CP03 canonical = Supabase pgvector | features/ |
| ux_ui_best_practices_and_interaction_guide | CP06 | Dark-mode doctrine conflict (dark-first vs dark-optional) | design/ |
| Plan_22_Simulator_Controller_Perfection | CP05 | Self-contradictory (offline sandbox vs live API calls) | features/ |

প্রতিটা ফাইলের frontmatter-এ যোগ করা হয়েছে:
- `superseded_by: ["CPxx"]` — কোন কোর প্ল্যান এটাকে প্রতিস্থাপন করেছে
- `archive_reason: "..."` — কেন archived
- `disposition: archive-dry-branch` — শুকনো ডাল (মুছবে না)
- `archived_date: "2026-09-25"`

---

## এখনো active conflict (১টা — code fix দরকার, archive নয়)

### customer_onboarding_flow.md
- **স্ট্যাটাস:** প্ল্যান সঠিক, কোড ভুল → **archive নয়, code fix দরকার**
- **কোর:** CP06 (Decoupled 3-Layer Topology)
- **প্ল্যান বলে:** "zero-config, 60s, কোনো API key না"
- **আসল কোড:** `OnboardingWizard.tsx` = `StepApiKey → StepModelSelect → StepFirstChat`
- **সমাধান:** কোড fix করতে হবে প্ল্যান অনুযায়ী (আলাদা Issue, code PR)

---

## পূর্বে archived (PR #1210, ২০টা)

Java-era + stale legacy files আগেই `docs/archive/plans/`-এ সরানো হয়েছে।
বিস্তারিত: PR #1210 commit history।

---

## ইকোসিস্টেম দর্শন

> এই ৭টা ফাইল মুছে ফেলা হয়নি। এগুলো এখন `docs/archive/plans/`-এ
> `archive-dry-branch` হিসেবে আছে — গাছের শুকনো ডাল।
>
> শুকনো ডাল গাছে থাকে কিন্তু নতুন পাতা দেয় না। তবে ইতিহাস বহন করে —
> কীভাবে না করতে হয়, তার শিক্ষা।
>
> `git log` দিয়ে প্রতিটা ফাইলের provenance ট্রেস করা যায়।

---

## রেফারেন্স

- [CONFLICT_ANALYSIS.md](../plan-network/CONFLICT_ANALYSIS.md) — কোন ফাইল কেন conflicted
- [ECOSYSTEM_PHILOSOPHY.md](../plan-network/ECOSYSTEM_PHILOSOPHY.md) — গাছের দর্শন
- [core-plans/](../plan-network/core-plans/README.md) — ৭ কোর প্ল্যান (CP01-CP07)
