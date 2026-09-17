"""Token accounting + budget resolution for the Context Engine (M2).

বাংলা: provider-ভিত্তিক input budget নির্ধারণ ও নিরীহ (dependency-free)
token অনুমান। বাজেট অজানা provider-এর জন্য conservative default —
free-tier worst-common-case যাতে কোনো provider-এর TPM ভাঙে না।
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------

#: Conservative default input budget (tokens) when the target provider is
#: unknown. The tightest free-tier ceiling in PROVIDER_TOKEN_BUDGETS is
#: huggingface (1 500) — too tight as a universal default; cloudflare (3 000)
#: is the worst-common-case the gateway actually routes to.
DEFAULT_INPUT_BUDGET = 3_000

#: Fraction of the budget each non-user section may occupy at most.
#: user gets an implicit hard-reserve (see engine); system is capped so a
#: runaway system prompt can never crowd out the user's actual question.
SECTION_CAPS: dict[str, float] = {
    "system": 0.25,
    "memory": 0.40,
    "knowledge": 0.60,
    "history": 0.75,
}


def resolve_input_budget(provider: str | None = None) -> int:
    """Resolve the per-request input token budget.

    বাংলা: provider জানা থাকলে ``core.llm.token_budget.PROVIDER_TOKEN_BUDGETS``
    থেকে তার ``max_input_tokens``; না হলে :data:`DEFAULT_INPUT_BUDGET`।
    """
    if provider:
        from core.llm.token_budget import PROVIDER_TOKEN_BUDGETS

        entry = PROVIDER_TOKEN_BUDGETS.get(str(provider).lower())
        if entry and entry.get("max_input_tokens"):
            return int(entry["max_input_tokens"])
    return DEFAULT_INPUT_BUDGET


def estimate_tokens(text: str) -> int:
    """Estimate the token count of ``text`` (chars ÷ 4 heuristic).

    বাংলা: tiktoken-মুক্ত হিউরিস্টিক — ইংরেজিতে ~4 chars/token; বাংলা/CJK-তে
    প্রতি অক্ষরের ওজন বেশি হওয়ায় এটি সাধারণত under-estimate করে, তাই
    multilingual টেক্সটে 1.3 গুণ সেফটি ফ্যাক্টর প্রয়োগ করা হয়।
    """
    if not text:
        return 0
    base = len(text) / 4
    # Bengali/CJK-heavy text carries more tokens per character.
    non_ascii = sum(1 for ch in text if ord(ch) > 0x7F)
    if non_ascii > len(text) * 0.3:
        base *= 1.3
    return max(1, int(base) + 1)
