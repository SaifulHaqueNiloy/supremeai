"""mem0-inspired self-learning memory adapter for SupremeAI.

mem0 (Universal memory layer for AI agents) থেকে নেওয়া মূল ধারণা: এজেন্ট/ব্যবহারকারীর
কথোপকথন থেকে স্থায়ী, অনুসন্ধানযোগ্য মেমোরি তৈরি করা, যা পরবর্তী কলে রিকল করা যায়।
এখানে mem0-কে **optional dependency** হিসেবে ব্যবহার করা হয়; ইনস্টল + flag on হলে আসল
mem0 দিয়ে কাজ করে, নাহলে একটি dependency-free zero-cost fallback (keyword-cosine +
consolidation) ব্যবহার হয়। ফলে সবসময় 'Eternal Brain'-এর ভ্যালু পাওয়া যায়।
"""

from __future__ import annotations

import math
import re
from typing import Any

from loguru import logger

from integrations._flags import flag, import_available

_ENABLED_FLAG = "SUPREMEAI_MEM0_ENABLED"


def _tokens(text: str) -> list[str]:
    """Bag-of-words tokenization (bangla + english alphanumerics)."""
    return [w.lower() for w in re.findall(r"[a-z0-9\u0980-\u09FF]+", text) if len(w) > 1]


class Mem0MemoryAdapter:
    """Self-learning memory layer bridging optional mem0 with zero-cost fallback."""

    def __init__(self, persist_path: str | None = None) -> None:
        self.enabled_flag = _ENABLED_FLAG
        self._memory = None
        self._persist_path = persist_path
        self._entries: list[dict[str, Any]] = []
        self._load_fallback()
        # flag + dependency দুটোই লাগবে আসল mem0 ব্যবহার কর�ে
        if flag(_ENABLED_FLAG) and import_available("mem0"):
            try:
                from mem0 import Memory  # type: ignore[import-not-found]

                self._memory = Memory()
                logger.info("Mem0MemoryAdapter: using upstream memory layer.")
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning(f"Mem0MemoryAdapter: upstream init failed, using fallback: {exc}")
                self._memory = None
        else:
            logger.info(
                "Mem0MemoryAdapter: upstream disabled/absent, using zero-cost fallback "
                f"(flag={flag(_ENABLED_FLAG)}, dep={import_available('mem0')})."
            )

    @property
    def active(self) -> bool:
        """True when the real upstream memory layer is in use."""
        return self._memory is not None

    def record(self, messages: list[dict[str, str]], user_id: str = "default") -> None:
        """Persist a conversation turn into long-term memory."""
        if self.active:
            try:
                self._memory.add(messages, user_id=user_id)  # type: ignore[union-attr]
                return
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning(f"Mem0MemoryAdapter: add failed, falling back: {exc}")

        # zero-cost fallback: atomic snippet caching
        text = " ".join(m.get("content", "") for m in messages).strip()
        if text:
            entry = {"text": text, "tokens": _tokens(text)}
            self._entries.append(entry)
            self._save_fallback()

    def _load_fallback(self) -> None:
        """Load persisted fallback entries from disk (JSONL)."""
        if not self._persist_path:
            return
        try:
            import json as _json
            from pathlib import Path

            p = Path(self._persist_path)
            if p.exists():
                self._entries = []
                for line in p.read_text(encoding="utf-8").splitlines():
                    if line.strip():
                        self._entries.append(_json.loads(line))
                logger.info(f"Mem0MemoryAdapter: loaded {len(self._entries)} fallback entries.")
        except Exception as exc:
            logger.debug(f"Mem0MemoryAdapter: fallback load failed: {exc}")

    def _save_fallback(self) -> None:
        """Persist fallback entries to disk (JSONL) for survival across restarts."""
        if not self._persist_path:
            return
        try:
            import json as _json
            from pathlib import Path

            p = Path(self._persist_path)
            p.parent.mkdir(parents=True, exist_ok=True)
            with p.open("w", encoding="utf-8") as f:
                for entry in self._entries[-1000:]:
                    f.write(_json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception as exc:
            logger.debug(f"Mem0MemoryAdapter: fallback save failed: {exc}")

    def search(self, query: str, user_id: str = "default", top_k: int = 3) -> list[str]:
        """Return the most relevant past memories by hybrid (semantic/keyword) ranking."""
        if self.active:
            try:
                out = self._memory.search(query, user_id=user_id, top_k=top_k)  # type: ignore[union-attr]
                results = out.get("results", []) if isinstance(out, dict) else []
                scored: list[tuple[float, str]] = []
                for r in results:
                    text = r.get("memory", "") if isinstance(r, dict) else str(r)
                    score = float(r.get("score", 0.0)) if isinstance(r, dict) else 0.0
                    scored.append((score, text))
                scored.sort(key=lambda t: t[0], reverse=True)
                return [s for _, s in scored[:top_k]]
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning(f"Mem0MemoryAdapter: search failed, using fallback: {exc}")

        # zero-cost fallback: query-vector vs stored-vector cosine similarity
        q = _tokens(query)
        qset = set(q)
        ranked: list[tuple[float, str]] = []
        for entry in self._entries:
            sim = self._similarity(q, entry["tokens"])
            overlap = len(qset & set(entry["tokens"]))
            ranked.append((sim + 0.2 * overlap, entry["text"]))
        ranked.sort(key=lambda t: t[0], reverse=True)
        return [text for score, text in ranked[:top_k] if score > 0.0]

    @staticmethod
    def _similarity(a: list[str], b: list[str]) -> float:
        """Cosine similarity between two token bags (bag-of-words)."""
        if not a or not b:
            return 0.0
        va: dict[str, int] = {}
        vb: dict[str, int] = {}
        for t in a:
            va[t] = va.get(t, 0) + 1
        for t in b:
            vb[t] = vb.get(t, 0) + 1

        dot = sum(cnt * vb.get(t, 0) for t, cnt in va.items())
        norm_a = math.sqrt(sum(c * c for c in va.values()))
        norm_b = math.sqrt(sum(c * c for c in vb.values()))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)
