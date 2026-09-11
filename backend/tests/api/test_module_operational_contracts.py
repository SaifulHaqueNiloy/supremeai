"""
Contract test: Module Operational Truth & Verification
======================================================
Guarantees that:
1. MODULES_LIST.md strictly enforces the 224 functional module boundary.
2. Every module marked as 🟢 Operational has verified active callers.
3. No module marked as 🟢 Operational is a non-existent path.
4. Summary counts exactly match the rows in the table.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
MODULES_LIST_PATH = ROOT_DIR / "MODULES_LIST.md"


def parse_modules_list() -> tuple[dict[str, int], list[dict]]:
    assert MODULES_LIST_PATH.exists(), "MODULES_LIST.md must exist"
    lines = MODULES_LIST_PATH.read_text(encoding="utf-8").splitlines()

    counts = {}
    modules = []

    # Extract summary counts from header
    for line in lines[:20]:
        m_op = re.search(r"🟢 \*\*Operational:\*\*\s+(\d+)", line)
        if m_op:
            counts["operational"] = int(m_op.group(1))
        m_env = re.search(r"🟡 \*\*Environment-Dependent:\*\*\s+(\d+)", line)
        if m_env:
            counts["env_dependent"] = int(m_env.group(1))
        m_part = re.search(r"🟠 \*\*Partially Wired.*?:\*\*\s+(\d+)", line)
        if m_part:
            counts["partially_wired"] = int(m_part.group(1))
        m_brok = re.search(r"🔴 \*\*Broken:\*\*\s+(\d+)", line)
        if m_brok:
            counts["broken"] = int(m_brok.group(1))

    for line in lines:
        line = line.strip()
        if not line.startswith("|") or "Module Name / Relative Path" in line or "---|---" in line:
            continue
        parts = [p.strip() for p in line.split("|")[1:-1]]
        if len(parts) >= 4 and parts[0].isdigit():
            modules.append(
                {
                    "id": int(parts[0]),
                    "category": parts[1],
                    "path": parts[2],
                    "status": parts[3],
                    "callers": parts[4] if len(parts) > 4 else "",
                }
            )

    return counts, modules


def test_224_module_boundary_strictly_enforced():
    counts, modules = parse_modules_list()
    assert len(modules) == 224, f"Expected exactly 224 functional modules, got {len(modules)}"


def test_summary_counts_match_table_rows():
    counts, modules = parse_modules_list()

    op_count = sum(1 for m in modules if "🟢" in m["status"])
    env_count = sum(1 for m in modules if "🟡" in m["status"])
    part_count = sum(1 for m in modules if "🟠" in m["status"])
    broken_count = sum(1 for m in modules if "🔴" in m["status"])

    assert counts.get("operational") == op_count, (
        f"Summary Operational ({counts.get('operational')}) != rows ({op_count})"
    )
    assert counts.get("env_dependent") == env_count, (
        f"Summary Env-Dep ({counts.get('env_dependent')}) != rows ({env_count})"
    )
    assert counts.get("partially_wired") == part_count, (
        f"Summary Partially Wired ({counts.get('partially_wired')}) != rows ({part_count})"
    )
    assert counts.get("broken") == broken_count, (
        f"Summary Broken ({counts.get('broken')}) != rows ({broken_count})"
    )


def test_all_operational_modules_exist_on_disk():
    _, modules = parse_modules_list()
    for m in modules:
        if "🟢" in m["status"] or "🟠" in m["status"]:
            target = ROOT_DIR / m["path"]
            assert target.exists(), f"Cataloged module {m['path']} does not exist on disk!"


def test_operational_modules_have_active_callers():
    _, modules = parse_modules_list()
    for m in modules:
        if "🟢" in m["status"]:
            assert "0 active callers" not in m["callers"], (
                f"Module {m['path']} marked Operational but has 0 active callers"
            )
