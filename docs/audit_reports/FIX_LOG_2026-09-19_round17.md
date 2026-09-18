# Round 17 Fix Log — Vault Recheck + Open-Issue Triage + #460 (2026-09-19)

## 🇧🇩 সারসংক্ষেপ

ওনারের নির্দেশ: *"we added few more key in infisical vault now, recheck and fix any remaining issue need to fix, and there is 13 issue yet"* — Infisical vault পুনঃপরীক্ষা (৪০+ নতুন key), ১৩টি open issue-র পূর্ণ ট্রায়াজ, এবং যা ফিক্সযোগ্য তার ফিক্স।

## Vault Recheck (প্রমাণসহ)

- Universal-auth login → 200 (সঠিক রুট `/api/v1/auth/universal-auth/login`)।
- **prod: 141 → 179 secrets** (Round 15-এর স্ন্যাপশটের সাথে ডিফ করে ৪০টি নতুন key চিহ্নিত, সবগুলোর value যাচাই):
  - ৫× Cloudflare অ্যাকাউন্ট: `CLOUDFLARE_{SECONDARY,TERTIARY,QUATERNARY,QUINARY}_{EMAIL,GLOBAL_API_KEY,ACCOUNT_ID}` + `CLOUDFLARE_GLOBAL_API_KEY`
  - ৫× Upstash অ্যাকাউন্ট: `UPSTASH_{SECONDARY,TERTIARY,QUATERNARY,QUINARY}_{EMAIL,API_KEY}` + `UPSTASH_API_KEY/EMAIL`
  - ৪× ফেডারেশন Redis: `REDIS_{SECONDARY,TERTIARY,QUATERNARY,QUINARY}_URL` (rediss://, non-empty যাচাই) + `UPSTASH_REDIS_{SECONDARY,TERTIARY,QUATERNARY,QUINARY}_REST_{URL,TOKEN}`
  - `E2B_API_KEY` (e2b_…, 44 অক্ষর), `GH_TOKEN`, `TELEGRAM_CHAT_ID`+`TELEGRAM_BOT_TOKEN`+`ADMIN_TELEGRAM_CHAT_ID`
- এনক্রিপ্টেড `/api/v3/secrets` view আবার প্রোব → এখনো count 0 (#434 vendor defect স্থায়ী)।

## ১৩টি Open Issue-র ট্রায়াজ

| Issue | বিভাগ | সিদ্ধান্ত |
|---|---|---|
| #459 | ডুপ্লিকেট "Test" | CLOSED (not planned) |
| #460 | Upstash কোটা বার্ন | **ফিক্স + CLOSED (completed)** — নিচে বিস্তারিত |
| #434 | Infisical encrypted-view | OPEN — vendor; Round-17 প্রোব-প্রমাণ কমেন্ট |
| #430/#431/#432 | Owner config | OPEN — Actions:write প্রয়োজন (vault-এর নতুন GH_TOKEN-ও Issues/Actions পারমিশন ছাড়া — 403 প্রোব করা হয়েছে; ওনারকে fine-grained PAT-এ **Repository access + Permissions → Issues: Read & Write, Actions: Read & Write** টগল করতে হবে) |
| #433 | CI meta | OPEN — ট্র্যাকিং |
| #441 | Learning flags | OPEN — ওনার-সিদ্ধান্ত (RAM বিশ্লেষণ সহ) |
| #449/#451 | আর্কিটেকচারাল | OPEN — বড় ইঞ্জিনিয়ারিং আইটেম |
| #453/#457/#458 | রোডম্যাপ | OPEN |

## #460 ফিক্স — Upstash Quota Burn (Pillar 1 + Pillar 2)

**Root cause (live-stack audit, ইস্যুর ৮-ops অনুমানের চেয়ে খারাপ):**
প্রতি HTTP রিকোয়েস্টে **১২টি billable Upstash op** — `RequestValidationMiddleware` (দুই-ফেজ ২+২), `APIKeyAuthMiddleware` (ZSET pipeline ৪), `core/rate_limit.py RateLimiter` (দুই-ফেজ ২+২)। ~৩,০০০ বট রিকোয়েস্ট/দিন → ~৩৬,০০০ ops/দিন → ৫০০k কোটা ~১৪ দিনে শেষ।

**Pillar 1 — atomic single-op (১২ → ৩ ops/req):**
- NEW `core/cache/rate_limit_atomic.py`: একক EVAL (INCR + first-INCR EXPIRE + TTL<0 net) = ১ billable op
- ৪টি কনজিউমার কনভার্ট: `core/rate_limit.py` (P2 গ্যারান্টি অক্ষত), `core/middleware/security.py`, `middleware/tenant_rate_limiter.py` + `core/security/api_key_limiter.py` (২→১); `middleware/rate_limiter.py`-তে প্যারালাল এজেন্টের sliding-window Lua (`eb2fdbf3`) রাখা হয়েছে (pipeline fallback সহ)
- **IP-eval dedup:** `rate_limit_ip_verdict` request.state-এ শেয়ার — এক রিকোয়েস্টে ১টি IP evaluation (critical-path override সম্মানিত)
- **Namespace fix:** `tenant_rl:` — counter/ZSET সংঘর্ষ দূর
- WRONGTYPE guard: legacy ZSET key একবার replace

**Pillar 2 — 5-account federation failover (কোটা ×৫ = 2.5M ops/মাস):**
- `SecureRedisManager`: পুল failover (quota-exhaust → পরের পুল), সব পুল শেষে #437 breaker, half-open probe pool ১-এ রিসেট
- **Vault-aware resolution:** `os.getenv` → `settings._get_cached_secret` (boot bulk-load থেকে, অতিরিক্ত নেটওয়ার্ক শূন্য)
- `memory://` fail-closed চুক্তি অক্ষত

**প্রমাণ:**
- Live Upstash: EVAL ×3 → 1,2,3; TTL=60s; প্রাইমারি + সেকেন্ডারি পুল `PING=True`
- Failover state machine: trip1→pool2, trip2→pool3, trip3→all→breaker; non-quota এরর উপেক্ষিত; memory:// exclusion; dedup/CSV order
- Render: primary 21→25, worker 16→20 env vars (৪টি ফেডারেশন URL), PUT 200, read-back যাচাই
- Commits: `6c39df6f`, `b39df3a9`, `f8e56470` (+ format fix); rebase-merged with `eb2fdbf3`/`8f71e97a` (pull-before-push প্রতিটি পুশে)

## পরবর্তী প্রায়োরিটি

1. CI green নিশ্চিত → Render auto-deploy → `/health` 200 + লগে federation pool মেসেজ যাচাই
2. E2B_API_KEY ভার্চুয়াল-মেশিন স্যান্ডবক্স (package install প্রয়োজন — LOW_MEMORY_MODE সীমাবদ্ধতা মাথায় রেখে)
3. #430/#432: ওনার PAT পারমিশন টগল (উপরে সঠিক টগলের নাম দেওয়া আছে)
4. #442 tail: Supabase ai_memory re-index (পুরনো hash ভেক্টর)
