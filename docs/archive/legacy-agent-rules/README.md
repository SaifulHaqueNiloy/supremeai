# Archived — Legacy Agent Rule Files (`#2251` Phase-5 Slice-1)

> **ইকোসিস্টেম দর্শন:** কোনো ফাইল মুছে ফেলা হয়নি — এগুলো ইতিহাসের শিক্ষা হিসেবে
> এখানে archive করা হয়েছে (`git mv`, restore করতে চাইলে পাথ ফেরত আনলেই হয়)।

**Archived:** 2026-09-28 · **Issue:** #2251 (`needs:decomposition` → Slice-1) · **Base:** main `5bf27d21`

## কী archive হলো (১২টি ফাইল)

| পুরোনো পাথ | নতুন পাথ | কেন archive |
|---|---|---|
| `.clinerules/master_prompt.md` | `clinerules/master_prompt.md` | Legacy "Sovereign Cognitive Prompt" — এর ভূমিকা এখন `AGENTS.md` + `docs/agents/` পালন করছে |
| `.clinerules/workflows/speckit-*.md` (১০টি) | `clinerules/workflows/` | Spec Kit slash-command prompt-এর Cline কপি — active tool home হলো `.specify/`; ledger `.specify/integrations/cline.manifest.json` এই PR-এ sync করা হয়েছে |
| `.lingma/rules/agents.md` | `lingma/rules/agents.md` | Drifting কপি — লেখা ছিল "Single Source of Truth: `STATUS.md`" (ফাইলটি আর নেই); root `AGENTS.md`-ই একমাত্র SSOT |

## এখন কোথায় জীবন্ত নিয়ম (Live rules now)

- **Machine-readable gates:** `.github/constitution/rules.yml` (+ `baseline.json`, `exceptions.yml`)
- **Agent constitution:** `AGENTS.md` (repo root) + `docs/agents/` (role cards, RULES_INDEX, GOLDEN_RULES)
- **Spec Kit:** `.specify/` (unchanged, active)

## কী sync করা হয়েছে এই PR-এ

- `.specify/integrations/cline.manifest.json` — install ledger `files → {}` + archived নোট (ভবিষ্যৎ spec-kit update যেন root-এ ফাইল নিঃশব্দে resurrect না করে)
- `scripts/ai/change_impact_detector.py`, `scripts/ai/sandboxed_repair.py` — `PROTECTED_PREFIXES`-এ নিষ্ক্রিয় `.clinerules/` সরিয়ে `docs/archive/` যোগ (archive নিজেও auto-edit-protected)
- `scripts/detect_silent_errors.py` — `DEFAULT_EXCLUDE_DIRS` থেকে `.lingma` সরানো
- `docs/DOCUMENTATION_MASTER_INDEX.md` — সরাসরি ১১টি entry নতুন পাথে re-point (generated ফাইল; `.kilo/worktrees` ghost entry আগে থেকেই stale — পরে আলাদা regen pass-এর কাজ)

*Archive ফাইলের কনটেন্ট অপরিবর্তিত — শুধু লোকেশন বদলেছে।*
