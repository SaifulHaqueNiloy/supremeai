"""Tests for PLAN-002: Claude Code-style semantic context compaction.

Covers:
* pure helpers in core/prompt_handler.py (build_compaction_messages,
  estimate_messages_tokens) — including prior-summary merging and
  non-string/empty safety;
* api/routes/websocket_agent.py `_compact_history` with a stubbed gateway:
  success path (labeled compacted_context block at deque head, bounded
  deque), gateway-exception fallback (honest dumb eviction, no exception
  escapes), empty-summary fallback, and the summarization task_type contract.

Stubbing note (per plan §2.4 Change 3): the stub lives in TEST tooling only —
production code keeps using the real llm_gateway.
"""

from collections import deque

import api.routes.websocket_agent as ws_agent
from core.prompt_handler import (
    COMPACTION_BLOCK_LABEL,
    COMPACTION_SYSTEM_PROMPT,
    build_compaction_messages,
    estimate_messages_tokens,
)

MAXLEN = 50


class StubGateway:
    """Minimal async gateway stand-in recording calls and returning canned results."""

    def __init__(self, result=None, error=None):
        self.result = result if result is not None else {
            "success": True,
            "text": "User prefers FastAPI; decided to keep the Neon-backed task routes.",
        }
        self.error = error
        self.calls: list[dict] = []

    async def acompletion(self, prompt, task_type=None, **kwargs):
        self.calls.append({"prompt": prompt, "task_type": task_type})
        if self.error is not None:
            raise self.error
        return self.result


def _full_history(n=MAXLEN, maxlen=MAXLEN):
    h = deque(maxlen=maxlen)
    for i in range(n):
        h.append({"role": "user" if i % 2 == 0 else "assistant", "content": f"msg {i}"})
    return h


# ---------------------------------------------------------------------------
# Pure helper tests (prompt_handler.py)
# ---------------------------------------------------------------------------


def test_build_compaction_messages_shape():
    evicted = [
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "hi there"},
    ]
    messages = build_compaction_messages(evicted)
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[0]["content"] == COMPACTION_SYSTEM_PROMPT
    assert messages[1]["role"] == "user"
    assert "user: hello" in messages[1]["content"]
    assert "assistant: hi there" in messages[1]["content"]


def test_build_compaction_messages_merges_prior_summary():
    evicted = [{"role": "user", "content": "more talk"}]
    messages = build_compaction_messages(evicted, prior_summary="Earlier: chose Postgres.")
    user_content = messages[1]["content"]
    assert "Previous summary (merge it):" in user_content
    assert "Earlier: chose Postgres." in user_content
    assert "Conversation:" in user_content


def test_build_compaction_messages_no_prior_block_when_none():
    messages = build_compaction_messages([{"role": "user", "content": "x"}], prior_summary=None)
    assert "Previous summary" not in messages[1]["content"]


def test_estimate_messages_tokens_empty_and_values():
    assert estimate_messages_tokens([]) == 0
    msgs = [{"role": "user", "content": "a" * 40}, {"role": "assistant", "content": "b" * 80}]
    # 4-chars≈1-token heuristic: 10 + 20
    assert estimate_messages_tokens(msgs) == 30


def test_estimate_messages_tokens_non_string_content_safe():
    weird = [
        {"role": "user", "content": None},
        {"role": "assistant", "content": 12345},
        {"role": "user"},  # missing content key entirely
    ]
    assert estimate_messages_tokens(weird) == 0


# ---------------------------------------------------------------------------
# _compact_history behavior tests (websocket_agent.py, stubbed gateway)
# ---------------------------------------------------------------------------


async def test_compact_success_places_labeled_block_and_stays_bounded():
    history = _full_history()
    gateway = StubGateway()
    await ws_agent._compact_history(history, gateway, session_ref="sess-success")
    # Evicted 25 (maxlen//2), 25 remain, summary block appended at the LEFT.
    assert len(history) == MAXLEN - MAXLEN // 2 + 1
    head = history[0]
    assert head["role"] == "system"
    assert head.get("name") == "compacted_context"
    assert COMPACTION_BLOCK_LABEL in head["content"]
    assert "Neon-backed" in head["content"]  # gateway summary text carried through
    # Most recent messages must survive the compaction untouched.
    assert history[-1]["content"] == "msg 49"
    assert len(history) <= history.maxlen


async def test_compact_uses_summarization_task_type_and_passes_prior():
    history = _full_history()
    # Pre-seed an existing compacted_context block so the merge path triggers.
    history[0] = {
        "role": "system",
        "name": "compacted_context",
        "content": f"{COMPACTION_BLOCK_LABEL}\nOlder summary.",
    }
    gateway = StubGateway()
    await ws_agent._compact_history(history, gateway, session_ref="sess-merge")
    assert len(gateway.calls) == 1
    assert gateway.calls[0]["task_type"] == "summarization"
    prompt = gateway.calls[0]["prompt"]
    assert isinstance(prompt, list) and prompt[0]["role"] == "system"
    assert "Older summary." in prompt[1]["content"]  # prior summary merged into prompt


async def test_compact_gateway_failure_falls_back_honestly():
    history = _full_history()
    gateway = StubGateway(error=RuntimeError("all providers down"))
    # Must NOT raise — WS chat loop survival is the contract (Constitution #8).
    await ws_agent._compact_history(history, gateway, session_ref="sess-fail")
    assert all(
        not (isinstance(m, dict) and m.get("name") == "compacted_context") for m in history
    ), "failed compaction must not fabricate a summary block"
    assert len(history) == MAXLEN - MAXLEN // 2  # plain eviction happened
    assert history[-1]["content"] == "msg 49"  # recent messages preserved


async def test_compact_empty_summary_falls_back():
    history = _full_history()
    gateway = StubGateway(result={"success": True, "text": "   "})
    await ws_agent._compact_history(history, gateway, session_ref="sess-empty")
    assert all(
        not (isinstance(m, dict) and m.get("name") == "compacted_context") for m in history
    )
    assert len(history) == MAXLEN - MAXLEN // 2


async def test_compact_truncates_runaway_summary_to_cap():
    history = _full_history()
    gateway = StubGateway(result={"success": True, "text": "x" * 9999})
    await ws_agent._compact_history(history, gateway, session_ref="sess-cap")
    head = history[0]
    block_len = len(head["content"]) - len(COMPACTION_BLOCK_LABEL) - 1
    assert block_len <= 1400  # COMPACTION_SUMMARY_CHAR_CAP
    assert len(history) <= history.maxlen


async def test_history_never_exceeds_maxlen_across_successive_cycles():
    history = _full_history()
    gateway = StubGateway()
    for _ in range(3):
        if len(history) == history.maxlen:
            await ws_agent._compact_history(history, gateway, session_ref="sess-cycle")
        history.append({"role": "user", "content": "turn"})
        history.append({"role": "assistant", "content": "reply"})
        assert len(history) <= history.maxlen
    assert len(gateway.calls) >= 1
