#!/usr/bin/env python3
"""AGENTS.md v3 generator — renders the Universal Agent contract from rules.yml.

বাংলা: AGENTS.md এখন GENERATED document — হাতে এডিট করা যাবে না।
Single source of truth: `.github/constitution/rules.yml` (`constitution`,
`living_protocols`, `bootstrap`, `gates`, `hard_rules`, `freedoms` sections)।
v3 (#2504): Universal Agent Contract — compact (<60 লাইন), task-type rules
DB-তে (task_policies) থাকে, এই file শুধু universal contract।

Usage:
    python scripts/ci/generate_agents_md.py             # write AGENTS.md
    python scripts/ci/generate_agents_md.py --check     # drift check (CI): exit 1 if drifted
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RULES_PATH = REPO_ROOT / ".github" / "constitution" / "rules.yml"
AGENTS_PATH = REPO_ROOT / "AGENTS.md"

HEADER = "<!-- GENERATED FILE — DO NOT EDIT BY HAND -->\n<!-- Source of truth: .github/constitution/rules.yml · Generator: scripts/ci/generate_agents_md.py -->\n<!-- CI drift check: pr.yml → agents-md-sync. To change rules, edit rules.yml. -->\n"


def render(rules: dict) -> str:
    """Render AGENTS.md v3 (Universal Agent Contract) from the registry — compact।"""
    constitution = rules.get("constitution") or {}
    living_protocols = rules.get("living_protocols") or {}
    bootstrap = rules.get("bootstrap") or []
    gates = rules.get("gates") or {}
    hard_rules = rules.get("hard_rules") or {}
    freedoms = rules.get("freedoms") or []
    version = constitution.get("rules_version", "4.0")

    bn_digits = str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯")

    lines: list[str] = []
    lines.append(HEADER)
    lines.append("")
    lines.append(
        f"# {constitution.get('name', 'SupremeAI — AGENTS.md v3 (Universal Agent Contract)')}"
    )
    lines.append("")
    lines.append(f"> rules_version: `{version}` · {constitution.get('philosophy_quote', '')}")
    lines.append(f"> **{constitution.get('core_principle', '')}**")
    lines.append(f"> Rule layering: {constitution.get('rule_layering', '')}")
    lines.append("")

    # Universal Protocols — v3 compact (১ লাইন/প্রোটোকল)
    if living_protocols:
        lines.append("## Universal Protocols")
        lines.append("")
        for idx, (pid, proto) in enumerate(living_protocols.items(), start=1):
            idx_bn = str(idx).translate(bn_digits)
            lines.append(f"{idx_bn}. **{proto.get('title', pid)}** — {proto.get('rule', '')}")
        lines.append("")

    lines.append("## Bootstrap")
    lines.append("")
    for idx, entry in enumerate(bootstrap, start=1):
        # Support both old-style {slot:..., claim:...} and new-style {step:...}
        if "step" in entry:
            command = entry["step"]
        else:
            _, command = next(iter(entry.items()))
        note = entry.get("note", "")
        line = f"{idx}. `{command}`"
        if note:
            line += f" — {note}"
        lines.append(line)
    lines.append("")

    # System Gates — compact টেবিল
    lines.append("## System Gates (CI-enforced — মনে রাখার দরকার নেই)")
    lines.append("")
    lines.append("| Gate | কখন আটকাবে |")
    lines.append("| :--- | :--- |")
    for gid, gate in gates.items():
        title = gate.get("title", gid)
        blocks = (gate.get("blocks_when", "") or "").replace("|", "\\|")
        lines.append(f"| {title} | {blocks} |")
    lines.append("")

    # Review protocol (4-Pillar Rubric) সচেতনভাবে আলাদা সেকশনে নেই —
    # Universal Protocol 'Group Closeout' + rules.yml review_protocol-এ পূর্ণ টেবিল
    # (v3 লাইন-বাজেট: <60 লাইন; ডুপ্লিকেশন নয়, একই তথ্যের এক রেফারেন্স)।

    # Hard rules — মূল কঠিন নিয়ম
    count_bn = str(len(hard_rules)).translate(bn_digits)
    lines.append(f"## একমাত্র কঠিন নিয়ম (মোট {count_bn}টা, বাকি সব system-এর ভার)")
    lines.append("")
    for idx, (_, text) in enumerate(hard_rules.items(), start=1):
        idx_bn = str(idx).translate(bn_digits)
        lines.append(f"{idx_bn}. {text}")
    lines.append("")

    # Freedoms + footer
    if freedoms:
        lines.append("> স্বাধীনতা: " + " ".join(freedoms))
    lines.append(
        "> সম্পূর্ণ machine-readable rule registry: `.github/constitution/rules.yml` · "
        "task-type policy DB: `task_policies` (#2504)।"
    )
    lines.append("> **এই file-টি registry থেকে GENERATED — হাতে এডিট করবে না।**")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate AGENTS.md from rules.yml")
    parser.add_argument("--check", action="store_true",
                        help="drift check: exit 1 if AGENTS.md differs from generated output")
    parser.add_argument("--rules", default=str(RULES_PATH))
    parser.add_argument("--out", default=str(AGENTS_PATH))
    args = parser.parse_args()

    try:
        import yaml
    except ImportError:
        print("PyYAML required: pip install pyyaml", file=sys.stderr)
        return 2

    rules = yaml.safe_load(Path(args.rules).read_text(encoding="utf-8")) or {}
    rendered = render(rules)

    if args.check:
        current = Path(args.out).read_text(encoding="utf-8")
        if current == rendered:
            print("[PASSED] AGENTS.md is in sync with rules.yml")
            return 0
        print("[FAILED] AGENTS.md drifted from rules.yml — "
              "run `python scripts/ci/generate_agents_md.py` and commit")
        return 1

    Path(args.out).write_text(rendered, encoding="utf-8")
    print(f"[OK] AGENTS.md generated from {args.rules} ({len(rendered.splitlines())} lines)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
