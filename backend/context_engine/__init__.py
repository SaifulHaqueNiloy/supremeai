"""Context Engine (M2) — smallest-sufficient-context assembly.

বাংলা: ERR-F03 অনুযায়ী prompt assembly আগে অসংগঠিত ছিল — memory/RAG ফ্যাক্ট
এবং user prompt অবাধ্যভাবে জোড়া হতো (`f"{memory_ctx}{prompt}"`), কোনো token
budget ছিল না; ফলে context bloat হতো এবং free-tier provider-দের TPM/rate
limit নষ্ট হতো। এই প্যাকেজ deterministic, pure-stdlib context assembly দেয়:

- প্রতিটি অংশ (system/memory/knowledge/history/user) একটি :class:`ContextBlock`
- প্রদত্ত বাজেটের ভেতরে priority-ভিত্তিক greedy fill — ছোট ব্লক পরে এলেও
  জায়গা হলে রাখা হয় (best-fit), যা সবচেয়ে কম তথ্য-ক্ষতি করে
- user message সবসময় থাকে (অপরিহার্য), system সীমিত cap-এ থাকে
- প্রতিটি assemble একটি :class:`~context_engine.engine.AssembledContext`
  রিটার্ন করে — per-section token ব্যবহার, dropped block-দের তালিকা ও
  truncation flag সহ (পর্যবেক্ষণযোগ্য, পরীক্ষাযোগ্য)

Integration: ``api/routes/chat.py`` এর দুটি call site (`get_completion`,
`stream_chat`) এখন এই ইঞ্জিন দিয়ে enriched prompt তৈরি করে।
"""

from context_engine.budget import (
    DEFAULT_INPUT_BUDGET,
    SECTION_CAPS,
    estimate_tokens,
    resolve_input_budget,
)
from context_engine.engine import AssembledContext, ContextBlock, ContextEngine, Section

__all__ = [
    "AssembledContext",
    "ContextBlock",
    "ContextEngine",
    "DEFAULT_INPUT_BUDGET",
    "Section",
    "SECTION_CAPS",
    "estimate_tokens",
    "resolve_input_budget",
]
