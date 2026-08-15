# SupremeAI Session Checkpoint
> Auto-updated by AI agents after each major session. Next agent must read this first.

## Last Session
- **Date:** 2026-08-15 20:42 UTC
- **Agent:** Auto-updated (checkpoint_update.py)
- **Summary:** Auto-updated via pre-commit hook

## Completed This Session
  - (see git log for details)

## Files Changed
  - `AGENTS.md`
  - `CHECKPOINT.md`

## Pending (Carry Forward)
- **HIGH:** `SupremeAIService.ts` lines 350-424 — OpenRouter fetch fallback রিমুভ করতে হবে (Brand Exclusivity)
- **HIGH:** `LESSONS_LEARNED.md` এখন 64KB — শেষ 30 entry রেখে পুরানো entries `docs/archive/lessons_2026-07.md`-এ rotate করতে হবে (64KB → 12KB target)
- **MED:** Phase C — `sentence-transformers` install করে `memory_write.py` প্রথম real run test করা
- **LOW:** `scripts/checkpoint_update.py` git pre-commit hook হিসেবে setup করা

## Recent Lessons Learned
  - 2026-08-15 — Do NOT hard-fail `alembic upgrade head` on asyncpg in CI (MissingGreenlet regression)
  - 2026-08-15 — CI Deploy-verify 120s Timeout Root Cause Fix (Render slow build)
  - 2026-08-15 — Simple CI Pipeline: Silent-Failure, Lockfile Auto-Push, Dual-Cache & Version Consistency Fix

## Key Architecture Reminders
- Extension = 100% Thin Client. No third-party API keys from user.
- `SupremeAIService.ts` lines 350-424: OpenRouter fetch logic → MUST be removed.
- Only local Ollama permitted as offline fallback.
- Supabase `ai_memory` table setup pending (Phase C).

## Next Agent Start Point
1. Read `AGENTS.md` + this file (done ✅)
2. Check task type → read relevant files per Context Matrix in `AGENTS.md`
3. Continue from Pending list above
