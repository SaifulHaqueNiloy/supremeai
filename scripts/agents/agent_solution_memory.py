#!/usr/bin/env python3
r"""SupremeAI — Collective Agent Memory & Solution Knowledge Base CLI.

Implements the "Search Before Solving · Pave Before Leaving" principle:
1. Search database & LESSONS_LEARNED.md for how previous agents solved the same issue.
2. Record newly validated solutions into database memory and LESSONS_LEARNED.md.
3. Verify MCP Control Tower connection configured via mcp.json.

Usage:
    # 1. Search for existing solutions:
    python scripts/agents/agent_solution_memory.py search --query "UnicodeEncodeError charmap"

    # 2. Record a validated solution:
    python scripts/agents/agent_solution_memory.py record \\
        --task-id "2201" \\
        --problem "PowerShell cp1252 stdout fails on UTF-8 emojis" \\
        --solution "Prefix command with \$env:PYTHONIOENCODING='utf-8'" \\
        --lesson "Always set PYTHONIOENCODING in windows terminal subprocesses" \\
        --tags "windows,encoding,powershell"

    # 3. Verify MCP connection:
    python scripts/agents/agent_solution_memory.py verify-mcp
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

# Ensure repository root is in sys.path
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

BACKEND_DIR = REPO_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

LESSONS_FILE = REPO_ROOT / "LESSONS_LEARNED.md"
MCP_CONFIG_FILE = REPO_ROOT / "mcp.json"
SQLITE_DB_PATH = REPO_ROOT / "data" / "supremeai.db"


def search_local_lessons(query: str) -> list[dict[str, str]]:
    """Search LESSONS_LEARNED.md for relevant entries matching keywords in query."""
    hits = []
    if not LESSONS_FILE.exists():
        return hits

    terms = [t.lower() for t in re.split(r"[\s,:;\-_]+", query) if len(t) > 2]
    if not terms:
        return hits

    try:
        content = LESSONS_FILE.read_text(encoding="utf-8", errors="replace")
    except Exception as err:
        print(f"[WARN] Failed reading LESSONS_LEARNED.md: {err}", file=sys.stderr)
        return hits

    for line in content.splitlines():
        line_clean = line.strip()
        if not line_clean.startswith("|") or "Date" in line_clean or "---" in line_clean:
            continue
        line_lower = line_clean.lower()
        score = sum(1 for term in terms if term in line_lower)
        if score > 0:
            hits.append({"text": line_clean, "score": score, "source": "LESSONS_LEARNED.md"})

    hits.sort(key=lambda x: x["score"], reverse=True)
    return hits[:5]


def search_database_memory(query: str) -> list[dict[str, Any]]:
    """Search episodic memory or SQLite database for similar past task solutions."""
    hits = []
    try:
        from memory.episodic_memory import EpisodicMemory

        ep_mem = EpisodicMemory(db_path=str(SQLITE_DB_PATH))
        results = ep_mem.recall_episodes(query=query)
        for ep in results:
            hits.append({
                "task_id": ep.get("task_id", ep.get("id", "unknown")),
                "problem": ep.get("context", ep.get("input_data", "")),
                "solution": ep.get("outcome", ep.get("output_data", "")),
                "success": ep.get("success", True),
                "source": "EpisodicMemory (Database)",
            })
    except Exception:
        # Fallback to simple scan or graceful degrade if dependencies unavailable
        pass
    return hits


def record_solution(
    task_id: str,
    problem: str,
    solution: str,
    lesson: str,
    tags: list[str] | None = None,
) -> bool:
    """Record solution into database episodic memory and LESSONS_LEARNED.md."""
    now_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    clean_task = task_id.lstrip("#")
    
    # 1. Store in Database Episodic Memory
    try:
        from memory.episodic_memory import EpisodicMemory

        ep_mem = EpisodicMemory(db_path=str(SQLITE_DB_PATH))
        ep_mem.store_episode(
            task_type="solution",
            context=problem,
            outcome=solution,
            importance=1.0,
            success=True,
            tags=tags or [],
            metadata={"lesson": lesson, "task_id": clean_task},
        )
        print(f"✅ Stored solution into Database Episodic Memory for task #{clean_task}.")
    except Exception as err:
        print(f"[INFO] Database storage skipped ({err}), recording to file.")

    # 2. Append to LESSONS_LEARNED.md if not already recorded
    if LESSONS_FILE.exists():
        try:
            content = LESSONS_FILE.read_text(encoding="utf-8", errors="replace")
            new_entry = f"| {now_str} | #{clean_task} | {problem} | {solution} | {lesson} |"
            if clean_task not in content:
                # Insert at top of the markdown table
                lines = content.splitlines()
                table_idx = -1
                for i, l in enumerate(lines):
                    if l.strip().startswith("| :---"):
                        table_idx = i + 1
                        break
                if table_idx != -1:
                    lines.insert(table_idx, new_entry)
                    LESSONS_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
                    print(f"✅ Appended entry to LESSONS_LEARNED.md (# {clean_task}).")
                else:
                    with open(LESSONS_FILE, "a", encoding="utf-8") as f:
                        f.write(f"\n{new_entry}\n")
                    print(f"✅ Appended entry to end of LESSONS_LEARNED.md (# {clean_task}).")
            else:
                print(f"ℹ️ Issue #{clean_task} already present in LESSONS_LEARNED.md.")
        except Exception as err:
            print(f"[ERROR] Failed writing to LESSONS_LEARNED.md: {err}", file=sys.stderr)
            return False

    return True


def verify_mcp() -> bool:
    """Verify MCP Control Tower configuration in mcp.json."""
    print("🔍 Checking SupremeAI MCP Tower configuration...")
    if not MCP_CONFIG_FILE.exists():
        print(f"❌ {MCP_CONFIG_FILE} not found in workspace root!", file=sys.stderr)
        return False

    try:
        cfg = json.loads(MCP_CONFIG_FILE.read_text(encoding="utf-8"))
        servers = cfg.get("mcpServers", {})
        if "supremeai-control-tower" not in servers:
            print("❌ 'supremeai-control-tower' missing from mcp.json mcpServers!", file=sys.stderr)
            return False
        server_def = servers["supremeai-control-tower"]
        print(f"✅ 'supremeai-control-tower' is registered in {MCP_CONFIG_FILE.name}:")
        print(f"   Command: {server_def.get('command')} {' '.join(server_def.get('args', []))}")
        print("✅ MCP Tower is configured and ready for agent connection.")
        return True
    except Exception as err:
        print(f"❌ Failed parsing mcp.json: {err}", file=sys.stderr)
        return False


def main() -> int:
    parser = argparse.ArgumentParser(
        description="SupremeAI Collective Agent Memory & Solution Knowledge Base"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Search Command
    search_parser = subparsers.add_parser("search", help="Search past solutions by problem or error query")
    search_parser.add_argument("--query", "-q", required=True, help="Error message, symptom, or task description")

    # Record Command
    record_parser = subparsers.add_parser("record", help="Record newly validated solution for future agents")
    record_parser.add_argument("--task-id", required=True, help="GitHub Issue ID or task identifier")
    record_parser.add_argument("--problem", required=True, help="Problem summary or error signature")
    record_parser.add_argument("--solution", required=True, help="Exact validated solution recipe")
    record_parser.add_argument("--lesson", required=True, help="Prevention rule / lesson learned")
    record_parser.add_argument("--tags", default="", help="Comma-separated tags")

    # Verify MCP Command
    subparsers.add_parser("verify-mcp", help="Verify MCP Control Tower connection configuration")

    args = parser.parse_args()

    if args.command == "search":
        print(f"🔍 Searching SupremeAI Collective Memory for: '{args.query}'...\n")
        lessons = search_local_lessons(args.query)
        db_hits = search_database_memory(args.query)

        if not lessons and not db_hits:
            print("⚠️ No exact previous solutions found in system memory.")
            print("👉 Recommendation: Solve the issue soundly, then run 'record' to pave the way for future agents!")
            return 0

        print(f"Found {len(lessons) + len(db_hits)} potential solution reference(s):\n")
        if lessons:
            print("📋 Matches from LESSONS_LEARNED.md:")
            for hit in lessons:
                print(f"  • {hit['text']}")
            print()
        if db_hits:
            print("🧠 Matches from Database Episodic Memory:")
            for hit in db_hits:
                print(f"  • [Task {hit['task_id']}] Problem: {hit['problem']} -> Solution: {hit['solution']}")
            print()

        return 0

    elif args.command == "record":
        tags = [t.strip() for t in args.tags.split(",") if t.strip()]
        success = record_solution(
            task_id=args.task_id,
            problem=args.problem,
            solution=args.solution,
            lesson=args.lesson,
            tags=tags,
        )
        return 0 if success else 1

    elif args.command == "verify-mcp":
        return 0 if verify_mcp() else 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
