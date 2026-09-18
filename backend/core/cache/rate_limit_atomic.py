"""Atomic single-op rate limiting for billable serverless Redis providers.

Issue #460 (Upstash quota burn): Upstash bills EVERY command inside a
pipeline as an individual request against the monthly free-tier quota. The
pre-fix production stack spent up to 12 billable ops per HTTP request
(3 middleware layers × 4-command ZSET / two-phase pipelines), which let
~3,000 background bot requests/day burn the 500k monthly quota in ~14 days.

একটি EVAL (Lua script) কল = ১টি billable op — script-এর ভেতরের redis.call()
গুলো আলাদাভাবে বিল হয় না। তাই ৪-কমান্ড pipeline → ১টি atomic EVAL (75%+ সাশ্রয়)।
"""

from __future__ import annotations

from typing import Any

# Fixed-window counter, single billable op:
#   INCR key                      → attempt count (rejected attempts counted
#                                   too, so retry storms cannot pass through
#                                   by flooding)
#   EXPIRE key window (on first)  → the window can never be extended by
#                                   retries — preserves the P2
#                                   no-self-amplification fix from
#                                   core/rate_limit.py (2026-09-12)
#   TTL<0 safety net              → keys that lost their TTL (crash between
#                                   INCR/EXPIRE in exotic providers) get one
#                                   re-applied instead of living forever
ATOMIC_WINDOW_LUA = """
local current = redis.call('INCR', KEYS[1])
if current == 1 then
    redis.call('EXPIRE', KEYS[1], ARGV[1])
else
    if redis.call('TTL', KEYS[1]) < 0 then
        redis.call('EXPIRE', KEYS[1], ARGV[1])
    end
end
return current
"""


async def atomic_window_incr(client: Any, key: str, window: int) -> int:
    """INCR ``key`` and enforce a ``window``-second TTL in ONE billable Redis op.

    বাংলা: ১টি মাত্র EVAL-এ counter বাড়ায় ও TTL সেট করে — Upstash-এ এটি
    ১টি মাত্র op হিসেবে বিল হয়। Returns the current window count (1-based).
    Raises on Redis errors so each caller can engage its own documented
    in-memory fallback.
    """
    try:
        return int(await client.eval(ATOMIC_WINDOW_LUA, 1, key, int(window)))
    except Exception as exc:
        # WRONGTYPE guard: a legacy ZSET (or other-typed) key under the same
        # name from the pre-#460 algorithm would make INCR fail forever.
        # Replace it once with a clean counter, then retry.
        if "WRONGTYPE" in str(exc):
            await client.delete(key)
            return int(await client.eval(ATOMIC_WINDOW_LUA, 1, key, int(window)))
        raise
