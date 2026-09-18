# Round 14 — Feature Reality Fixes (2026-09-18)

**বাংলা:** Round 13 অডিটে যে সব ভাঙা/ফাঁকি ফিচার ধরা পড়েছিল, এই রাউন্ডে সেগুলোর মূল ফিক্স পুশ করা হয়েছে। ডকট্রিন: **আসল কাজ অথবা সৎ ব্যর্থতা — কখনো বানানো সাকসেস নয়।**

**English:** This round fixes the core defects from the Round 13 feature-reality audit (#437–#452). Doctrine: **real work or loud failure — never fabricated success.**

| Issue | Commit | What was fixed |
|---|---|---|
| #437 (P0 live incident) | `7feb0700` | Redis quota circuit breaker + fallback log-storm dampener |
| #438 (P1 live incident) | `7f0dfa82` | 401/403 = definitive auth rejection in both LLM stacks |
| #444 (P0 fabricated) | `dd40ed9e` | Vision = real Gemini call or honest `VISION_NOT_CONFIGURED` |
| #445 (P0 fabricated) | `dd40ed9e` | Voice = real Groq Whisper STT / edge-tts / ElevenLabs or honest `*_NOT_CONFIGURED`; SSE never streams fake RIFF bytes |
| #448 (P0 broken) | `dd40ed9e` | `/api/v1/sandbox/*` returns honest 503 `SANDBOX_UNAVAILABLE` instead of per-request ValueError→500 |
| #446 (P1 fabricated) | `dd40ed9e` | Forge blueprints really persist (`data/swarm_blueprints/*.json`); execute = honest 501; frontend posts to the real path and surfaces honest errors |
| #442 (P0 memory) | `c204db97` | Module 01 embedder chain: CF Workers AI real embeddings + stopword/TF/multi-probe hash fallback + loud DEGRADED banner |

## Verification evidence

- **#437:** 6-assertion functional smoke (no-trip on generic errors; trip + 15min→1h escalating cooldown; `get_client_async()`→None while open (same fail-closed contract as `memory://`); half-open recovery; escalation on re-trip; no false positives from digits in key names). Per-request fallback warnings damped to once/5min (were 42–51% of all log lines).
- **#438:** `dynamic_ai` health-check 401/403 → `DISABLED_PERMANENT` (refresh loop already skips those — probe storm ends); request-time 401/403 → immediate permanent disable; `llm_gateway` key-pool: flat 300s auth cooldown → escalating 5min→1h→24h per key, reset on success (`mark_success` wired into the completion success path).
- **#442:** founder's recall-inversion test reproduced with the OLD algorithm (relevant 0.2309 < irrelevant 0.2697 — inversion); NEW algorithm: relevant 0.3592 vs irrelevant 0.0000 — inversion eliminated. Deterministic across processes (blake2b preserved), 384-dim contract holds, `vector_search` ranks the relevant doc first.
- **#444/#445/#446/#448:** py_compile + `ruff check`/`format` clean on all changed files; honest-status payloads include actionable remediation (which env var/key to configure).

## Owner actions that remain (cannot be done from code)

1. **#437:** Upstash plan upgrade বা monthly reset-এর অপেক্ষা — breaker waste বন্ধ করে, কিন্তু aggregate-safe rate limiting ফিরতে Redis দরকার।
2. **#438:** OpenRouter key rotate করে vault-এ বসান — এখন থেকে invalid key নিজে নিজে বন্ধ হয়ে যাবে, কিন্তু provider ফিরে পেতে হলে বৈধ কী লাগবে।
3. **#442:** আসল semantic embeddings চালু করতে Render-এ `CLOUDFLARE_API_TOKEN` + `CLOUDFLARE_ACCOUNT_ID` (Workers AI, দিনে ~১০k ফ্রি) দিন, অথবা পর্যাপ্ত RAM এলে `LOW_MEMORY_MODE=false` + `sentence-transformers`। **প্রোভাইডার বদলালে পুরনো hash ভেক্টর reindex করতে হবে।** (CLOUDFLARE_API_TOKEN/ACCOUNT_ID GitHub repo secrets-এ আগে থেকেই আছে — শুধু Render env-এ যোগ করতে হবে।)
4. **#446:** swarm execution engine এখনো ইমপ্লিমেন্ট হয়নি — execute endpoint সৎভাবে 501 দেয় (আগে বানানো success ছিল)।
5. **Token permission gap (নতুন):** বর্তমান fine-grained PAT দিয়ে issue comment/close ও Actions variables/secrets write করা যায় না (403)। #430-এর `PRODUCTION_URL` variable সেট করতে হলে মালিককে Actions:write + Issues:write সহ টোকেন দিতে হবে। (Smoke তবু সবুজ — `57b48055`-এর fallback path-এর কারণে, run 35364005319।)

## Notes for future rounds

- Stale embedding space: প্রোভাইডার বদলালে `ai_memory`-র পুরনো ভেক্টর নতুন প্রোভাইডারের ভেক্টরের সাথে তুলনীয় নয় — reindex/refresh আবশ্যক।
- #446-এর বাকি অংশ: `/api/v1/swarm/stream` live router-এ অনুপস্থিত; simulated swarm graph — পরবর্তী রাউন্ডে।
- CI concurrency-supersede ডিজাইনের কারণে প্রতিটি push আগের run cancel করে — শুধু সর্বশেষ commit-এর run সম্পূর্ণ হয়।
