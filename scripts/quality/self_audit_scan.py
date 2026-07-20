#!/usr/bin/env python3
"""বাংলা মন্তব্য: SupremeAI Self-Audit Static Scanner।

উদ্দেশ্য: `ruff`/`mypy`-এর মতো external dependency ছাড়াই (Zero Cost),
শুধু Python stdlib `ast` module ব্যবহার করে পুরো কোডবেসে common bug
pattern খুঁজে বের করা — যাতে CI-তে network/pip install না লাগলেও এই
স্ক্যান চলতে পারে (offline-safe, low-cost runners-এও কাজ করে)।

চেক করা হয়:
  1. Python syntax error (guaranteed real bug)
  2. Mutable default argument (`def f(x: list = [])`)
  3. `except: pass` — silent failure swallow (flag করে, human review-এর জন্য)
  4. Naive `datetime.now()` ব্যবহার (timezone-unaware — multi-region risk)
  5. Byte-identical duplicate ফাইল (Zero-Duplication নীতি)
  6. Hardcoded secret-সদৃশ প্যাটার্ন (basic heuristic, false-positive-prone)

ব্যবহার:
    python3 scripts/quality/self_audit_scan.py [--path .] [--json report.json] [--fail-on-syntax-error]

Self-Healing Engine নীতির সাথে সংযোগ: এই script-টা GitHub Actions-এ
weekly cron হিসেবে চালানো যায় (`.github/workflows/self-audit.yml`)।
Syntax error পেলে non-zero exit code দেয় (CI fail করানোর জন্য); বাকি
findings শুধু রিপোর্ট করে, CI block করে না (যাতে false-positive দিয়ে
deployment block না হয় — Zero Breakage)।
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

SKIP_DIRS = {
    "node_modules", ".git", "venv", "__pycache__", ".venv",
    "archive", "dist", "build", ".turbo",
}
CODE_EXTS = (".py",)
SRC_EXTS = (".py", ".ts", ".tsx", ".js", ".jsx")

SECRET_RE = re.compile(
    r'(api[_-]?key|secret|password|token|private[_-]?key)\s*=\s*[\'"][A-Za-z0-9_\-/+=]{8,}[\'"]',
    re.IGNORECASE,
)


def iter_files(root: Path, exts: tuple[str, ...]):
    for path in root.rglob("*"):
        if path.is_dir():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.suffix in exts:
            yield path


def scan_python(root: Path) -> dict:
    syntax_errors = []
    mutable_defaults = []
    except_pass = []
    naive_datetime = []

    for path in iter_files(root, CODE_EXTS):
        try:
            src = path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue

        rel = str(path.relative_to(root))

        for i, line in enumerate(src.splitlines(), 1):
            if "datetime.now()" in line and "utcnow" not in line:
                naive_datetime.append(f"{rel}:{i}")

        try:
            tree = ast.parse(src, filename=rel)
        except SyntaxError as e:
            syntax_errors.append(f"{rel}: {e}")
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                for default in list(node.args.defaults) + list(node.args.kw_defaults):
                    if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                        mutable_defaults.append(f"{rel}:{node.lineno}: def {node.name}(...)")
            if isinstance(node, ast.ExceptHandler):
                if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                    except_pass.append(f"{rel}:{node.lineno}")

    return {
        "syntax_errors": syntax_errors,
        "mutable_default_args": mutable_defaults,
        "except_pass_blocks": except_pass,
        "naive_datetime_now": naive_datetime,
    }


def scan_duplicates(root: Path) -> list[list[str]]:
    hashes: dict[str, list[str]] = defaultdict(list)
    for path in iter_files(root, SRC_EXTS):
        try:
            data = path.read_bytes()
        except Exception:
            continue
        if len(data) < 50:
            continue
        h = hashlib.md5(data).hexdigest()
        hashes[h].append(str(path.relative_to(root)))
    return [v for v in hashes.values() if len(v) > 1]


def scan_secrets(root: Path) -> list[str]:
    hits = []
    for path in iter_files(root, CODE_EXTS):
        try:
            src = path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        rel = str(path.relative_to(root))
        if "/tests/" in rel or rel.startswith("tests/"):
            continue  # টেস্ট mock value বাদ — false positive কমাতে
        for i, line in enumerate(src.splitlines(), 1):
            if SECRET_RE.search(line) and "os.environ" not in line and "getenv" not in line:
                hits.append(f"{rel}:{i}")
    return hits


def main() -> int:
    parser = argparse.ArgumentParser(description="SupremeAI offline self-audit scanner")
    parser.add_argument("--path", default=".", help="স্ক্যান করার root path")
    parser.add_argument("--json", default=None, help="JSON রিপোর্ট সেভ করার পাথ")
    parser.add_argument(
        "--fail-on-syntax-error",
        action="store_true",
        help="Syntax error পেলে non-zero exit code দিন (CI gate হিসেবে ব্যবহারের জন্য)",
    )
    args = parser.parse_args()

    root = Path(args.path).resolve()
    py_report = scan_python(root)
    dup_report = scan_duplicates(root)
    secret_report = scan_secrets(root)

    report = {
        **py_report,
        "duplicate_file_groups": dup_report,
        "possible_hardcoded_secrets": secret_report,
    }

    print("=== SupremeAI Self-Audit Scan ===")
    print(f"Syntax errors:            {len(report['syntax_errors'])}")
    print(f"Mutable default args:     {len(report['mutable_default_args'])}")
    print(f"except: pass blocks:      {len(report['except_pass_blocks'])}")
    print(f"Naive datetime.now():     {len(report['naive_datetime_now'])}")
    print(f"Duplicate file groups:    {len(report['duplicate_file_groups'])}")
    print(f"Possible hardcoded secret patterns: {len(report['possible_hardcoded_secrets'])}")

    if args.json:
        Path(args.json).write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\nJSON রিপোর্ট সেভ হয়েছে: {args.json}")

    if args.fail_on_syntax_error and report["syntax_errors"]:
        print("\n❌ Syntax error পাওয়া গেছে — CI ব্যর্থ হচ্ছে।")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
