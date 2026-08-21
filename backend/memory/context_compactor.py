"""
Context Compactor & Delta Checkpointing Module (DeerFlow 2.0 Pattern).
Provides lossy & lossless context engineering, token reduction, and delta snapshotting
for long-horizon agent execution without exploding token budgets.
"""

from __future__ import annotations

import re
from typing import Any
from loguru import logger


class ContextCompactor:
    """
    Trims verbose tool outputs, compresses redundant chat turns,
    and maintains concise executive state for long-running AI sessions.
    """

    def __init__(self, max_tokens_approx: int = 4000, max_line_output: int = 40):
        self.max_tokens_approx = max_tokens_approx
        self.max_line_output = max_line_output

    def estimate_tokens(self, text: str) -> int:
        """Heuristic character-based token estimator (~4 chars per token)."""
        if not text:
            return 0
        return len(text) // 4

    def compact_tool_output(self, raw_output: str, max_lines: int | None = None) -> str:
        """
        Compacts verbose logs, stdout, or file dumps into a clean head/tail excerpt.
        Preserves critical error lines.
        """
        if not raw_output:
            return ""

        limit = max_lines or self.max_line_output
        lines = raw_output.splitlines()
        if len(lines) <= limit:
            return raw_output

        half = limit // 2
        head = lines[:half]
        tail = lines[-half:]
        omitted = len(lines) - (len(head) + len(tail))

        # Check if there are error patterns in omitted section
        error_lines = [
            ln for ln in lines[half:-half]
            if re.search(r"\b(error|exception|fail|traceback|warning)\b", ln, re.IGNORECASE)
        ][:5]

        middle = [f"\n... [DeerFlow Compacted: {omitted} lines omitted] ...\n"]
        if error_lines:
            middle.append("--- Extracted Highlights from omitted lines ---")
            middle.extend(error_lines)
            middle.append("------------------------------------------------")

        return "\n".join(head + middle + tail)

    def compact_conversation_history(
        self,
        messages: list[dict[str, Any]],
        keep_last_turns: int = 4,
    ) -> list[dict[str, Any]]:
        """
        Compacts older conversation turns into an executive summary block
        while preserving the most recent interactive turns intact.
        """
        if len(messages) <= keep_last_turns:
            return messages

        older_messages = messages[:-keep_last_turns]
        recent_messages = messages[-keep_last_turns:]

        summary_bullets = []
        for msg in older_messages:
            role = msg.get("role", "unknown")
            content = str(msg.get("content", ""))
            # Truncate content for summary bullet
            first_line = content.split("\n")[0][:120]
            summary_bullets.append(f"- **{role.title()}**: {first_line}")

        executive_summary = (
            "### [System Consolidated Context (Compacted History)]\n"
            + "\n".join(summary_bullets)
        )

        compacted = [
            {"role": "system", "content": executive_summary},
            *recent_messages,
        ]
        return compacted

    def create_delta_snapshot(
        self,
        previous_state: dict[str, Any],
        current_state: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Calculates delta changes between two execution checkpoints.
        Avoids storing full duplicates in memory.
        """
        deltas: dict[str, Any] = {}
        for k, v in current_state.items():
            if k not in previous_state or previous_state[k] != v:
                deltas[k] = v
        return {
            "deltas": deltas,
            "modified_keys": list(deltas.keys()),
        }
