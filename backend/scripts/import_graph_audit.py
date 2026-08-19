"""SupremeAI Backend Import-Graph Audit (Static, stdlib-only).

বাংলা মন্তব্য:
এই টুলটি AST-ভিত্তিক স্ট্যাটিক অডিট করে — কোন internal module import ভাঙা,
কোন module entrypoint graph থেকে orphan, ইত্যাদি। কোনো Python package execute
করে না, তাই heavy/optional dependencies (supabase, torch, loguru...) লাগে না।

Detection rules:
  1. Internal module = প্রথম সেগমেন্ট যেটি `backend_root`-এর নিচে একটি package/file
     (যেমন core, api, tools, skills, agents, database, scripts, utils...).
  2. `from X import Y` — X অবশ্যই resolve হতে হবে আর Y হয় সাব-মডিউল, নয়তো X-এর
     module-level symbol হতে হবে। `tools.*` LazyModule proxy-গুলো
     `tools/__init__.py`-এর `_SUBMODULE_MAP` থেকে resolve করা হয়।
  3. Reachability BFS: entrypoints (`api/routers.py`, `core/lifespan.py`,
     `main.py`) থেকে শুধু internal edges ধরে ঢাকা module-গুলো।
  4. Broken imports কে দুই ভাগে ভাগ করা হয়: live (reachable closure-এ) এবং
     latent (non-reachable)। live ভাঙা ইম্পোর্ট = অ্যাপ স্টার্ট-গ্রাফের ঝুঁকি।

Usage:
    python scripts/import_graph_audit.py [--entrypoints api/routers.py core/lifespan.py main.py]
                                         [--json backend/_audit_baseline.json]
                                         [--root backend]
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ─── Paths / skip rules ──────────────────────────────────────────────────────
_SKIP_DIRS = {
    "__pycache__",
    ".venv",
    ".venv_ci",
    ".kilo",
    "node_modules",
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".secrets",
    "_archive",
}
# production-স্কোপে ঐচ্ছিক (ভারী) ফোল্ডার — `--scope prod` হলে skip করা হয়।
_PROD_SKIP = frozenset({"tests", "alembic"})

_DEFAULT_ENTRYPOINTS = [
    "api/routers.py",
    "core/lifespan.py",
    "main.py",
]


# ─── Module resolution helpers ───────────────────────────────────────────────
# একবার rglob দিয়ে module index বানানো হয়; প্রতিটি ফাইল একবার পড়ে (single-pass)
# tree ও symbols মেমোরিতে রাখা হয়, তারপর সব রেজোলিউশন pure in-memory চলে
# (WSL /mnt-এ বারবার stat/read = ধীর)।
_MODULE_INDEX: dict[str, Path] = {}
_MODULE_TREES: dict[str, ast.Module | None] = {}
_MODULE_SYMBOLS: dict[str, frozenset[str] | None] = {}
_MODULE_IMPORTS: dict[str, list[dict[str, Any]]] = {}
_MODULE_LINES: dict[str, int] = {}
_TOP_LEVEL: frozenset[str] = frozenset()


def _populate_index(root: Path, extra_skip: frozenset[str] = frozenset()) -> None:
    """backend root-এর সব internal .py module parse করে index-এ ভরে রাখে।"""
    global _MODULE_INDEX, _MODULE_TREES, _MODULE_SYMBOLS, _MODULE_IMPORTS, _MODULE_LINES, _TOP_LEVEL
    _MODULE_INDEX = {}
    _MODULE_TREES = {}
    _MODULE_SYMBOLS = {}
    _MODULE_IMPORTS = {}
    _MODULE_LINES = {}
    skip = _SKIP_DIRS | set(extra_skip)
    # rglob skip-dir গুলোর ভেতরেও নেমে যায় (node_modules/.venv = লাখো ফাইল)।
    # তাই os.walk(topdown) দিয়ে traversal-এর সময়ই skip-dir prune করা হয়।
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in skip]
        for filename in filenames:
            if not filename.endswith(".py"):
                continue
            py = Path(dirpath) / filename
            mod = path_to_module(root, py)
            _MODULE_INDEX[mod] = py
            try:
                source = py.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                source = ""
            _MODULE_LINES[mod] = source.count("\n") + 1
            try:
                tree = ast.parse(source)
            except (SyntaxError, OSError):
                tree = None
            _MODULE_TREES[mod] = tree
            if tree is not None:
                symbols, imports = scan_module(tree)
                _MODULE_SYMBOLS[mod] = symbols
                _MODULE_IMPORTS[mod] = imports
            else:
                _MODULE_SYMBOLS[mod] = None
                _MODULE_IMPORTS[mod] = []
    _TOP_LEVEL = frozenset(m.split(".")[0] for m in _MODULE_INDEX)


def module_to_path(root: Path, module_name: str) -> Path | None:
    """Map a dotted module name to its defining file under root."""
    if not _MODULE_INDEX:
        _populate_index(root)
    return _MODULE_INDEX.get(module_name)


def module_symbols(module_name: str) -> frozenset[str] | None:
    """Module-level symbol set (parse ব্যর্থ হলে None)।"""
    return _MODULE_SYMBOLS.get(module_name)


def path_to_module(root: Path, path: Path) -> str:
    """Map an absolute/relative file path to a dotted module name."""
    # `.resolve()` WSL /mnt-এ ধীর (প্রতি call-এ stat) — দুটোই absolute হলে
    # `relative_to` pure-string অপারেশন, কোনো FS access নেই।
    try:
        rel = path.relative_to(root)
    except ValueError:
        rel = path.resolve().relative_to(root.resolve())
    parts = list(rel.parts)
    if parts[-1] == "__init__.py":
        parts = parts[:-1]
    else:
        parts[-1] = parts[-1][: -len(".py")]
    return ".".join(parts)


def is_internal(root: Path, first_segment: str) -> bool:
    """True if first dotted segment corresponds to a backend-internal package/file."""
    if _TOP_LEVEL:
        return first_segment in _TOP_LEVEL
    cand = root / f"{first_segment}.py"
    candpkg = root / first_segment
    return cand.exists() or (candpkg.is_dir() and (candpkg / "__init__.py").exists())


def load_lazy_tools_map(root: Path) -> dict[str, str]:
    """Parse tools/__init__.py `_SUBMODULE_MAP` so `tools.X` proxies resolve to real paths."""
    tools_init = root / "tools" / "__init__.py"
    result: dict[str, str] = {}
    if not tools_init.exists():
        return result
    try:
        tree = ast.parse(tools_init.read_text(encoding="utf-8", errors="ignore"))
    except SyntaxError:
        return result
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "_SUBMODULE_MAP":
                    value = node.value
                    if isinstance(value, ast.Dict):
                        for k, v in zip(value.keys, value.values):
                            if isinstance(k, ast.Constant) and isinstance(v, ast.Constant):
                                result[str(k.value)] = str(v.value)
    return result


def _target_names(node: ast.AST) -> list[str]:
    if isinstance(node, ast.Name):
        return [node.id]
    if isinstance(node, (ast.Tuple, ast.List)):
        out: list[str] = []
        for elt in node.elts:
            out.extend(_target_names(elt))
        return out
    if isinstance(node, ast.Attribute):
        return _target_names(node.value)
    return []


# একক recursive pass-এ module-level symbol + import statement দুটোই বের করা হয়,
# যাতে প্রতি ফাইলে ast.walk বারবার না চালাতে হয় (WSL /mnt-এ পারফরম্যান্স)।
# import record: {"node": stmt, "module": str|None, "level": int, "names": [ast.alias]}
def scan_module(tree: ast.Module) -> tuple[frozenset[str], list[dict[str, Any]]]:
    """Return (module-level symbols, import records) — এক পাসে।"""
    symbols: set[str] = set()
    imports: list[dict[str, Any]] = []

    def visit(stmt: ast.stmt) -> None:
        if isinstance(stmt, ast.Assign):
            for t in stmt.targets:
                symbols.update(_target_names(t))
        elif isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
            symbols.add(stmt.target.id)
        elif isinstance(stmt, ast.Import):
            for alias in stmt.names:
                symbols.add(alias.asname or alias.name.split(".")[0])
            imports.append({"node": stmt, "module": None, "level": 0, "names": list(stmt.names)})
        elif isinstance(stmt, ast.ImportFrom):
            for alias in stmt.names:
                symbols.add(alias.asname or alias.name)
            imports.append(
                {"node": stmt, "module": stmt.module, "level": stmt.level, "names": list(stmt.names)}
            )
        elif isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            symbols.add(stmt.name)
        # module-level compound statements-এ (if/try/for/with) recurse
        for child in ast.iter_child_nodes(stmt):
            if isinstance(child, ast.stmt) and not isinstance(
                child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)
            ):
                visit(child)

    for top in tree.body:
        visit(top)
    return frozenset(symbols), imports



def resolve_from_symbol(
    root: Path, importer_pkg: str, module_name: str, sym: str, lazy_map: dict[str, str]
) -> tuple[bool, str]:
    """Check `from module_name import sym` resolves. Returns (ok, detail)."""
    # 1) tools.* lazy proxy
    if module_name.startswith("tools.") and module_name in lazy_map:
        real = lazy_map[module_name]
        if module_to_path(root, real) is None:
            return False, f"lazy proxy '{module_name}' -> missing real module '{real}'"
        syms = module_symbols(real)
        if syms is not None and sym not in syms:
            return False, f"symbol '{sym}' not in '{real}'"
        return True, f"lazy proxy -> {real}"

    # 2) module exists?
    if module_to_path(root, module_name) is None:
        return False, f"module '{module_name}' missing"

    # 3) sym as submodule?
    if module_to_path(root, f"{module_name}.{sym}") is not None:
        return True, f"submodule '{module_name}.{sym}'"

    # 4) sym as module-level symbol
    syms = module_symbols(module_name)
    if syms is None:
        return True, f"unparsable '{module_name}', assume ok"
    if sym not in syms:
        return False, f"symbol '{sym}' not found in '{module_name}'"
    return True, f"symbol '{sym}' in '{module_name}'"


def audit_module(
    root: Path,
    module_name: str,
    lazy_map: dict[str, str],
) -> list[dict[str, Any]]:
    """Return broken-import records for a single module (index-প্রি-পার্সড tree ব্যবহার করে)।"""
    tree = _MODULE_TREES.get(module_name)
    file = _MODULE_INDEX.get(module_name)
    if tree is None:
        return [{
            "importer": module_name,
            "file": str(file),
            "reason": "parse error",
        }]

    pkg_parts = module_name.split(".")[:-1]  # relative import base
    broken: list[dict[str, Any]] = []

    for record in _MODULE_IMPORTS.get(module_name, []):
        node = record["node"]
        imp_mod = record["module"]
        level = record["level"]
        names = record["names"]

        if imp_mod is None:  # `import a.b.c` style
            for alias in names:
                _check_import(root, module_name, alias.name, node, file, broken, lazy_map)
            continue

        if level:  # relative import
            base = pkg_parts[: max(0, len(pkg_parts) - level + 1)]
            rel_mod = ".".join([*base, imp_mod] if imp_mod else base)
            if not rel_mod or not is_internal(root, rel_mod.split(".")[0]):
                continue
            if module_to_path(root, rel_mod) is None:
                broken.append({
                    "importer": module_name,
                    "file": str(file),
                    "line": node.lineno,
                    "import_stmt": f"from . import {imp_mod or ''}",
                    "target": rel_mod,
                    "reason": f"module '{rel_mod}' missing",
                })
                continue
            for alias in names:
                if alias.name == "*":
                    continue
                ok, detail = resolve_from_symbol(root, module_name, rel_mod, alias.name, lazy_map)
                if not ok:
                    broken.append({
                        "importer": module_name,
                        "file": str(file),
                        "line": node.lineno,
                        "import_stmt": f"from {rel_mod} import {alias.name}",
                        "target": f"{rel_mod}.{alias.name}",
                        "reason": detail,
                    })
        else:
            _check_import(root, module_name, imp_mod, node, file, broken, lazy_map, names)
    return broken


def _check_import(
    root: Path,
    importer: str,
    module_name: str,
    node: ast.AST | None,
    file: Path,
    broken: list[dict[str, Any]],
    lazy_map: dict[str, str],
    names: list[ast.alias] | None = None,
) -> None:
    first = module_name.split(".")[0]
    if not is_internal(root, first):
        return  # stdlib / third-party

    stmt = (
        f"import {module_name}"
        if names is None
        else f"from {module_name} import {', '.join(a.name for a in names)}"
    )

    # tools.* lazy proxy — resolvable through the map (symbol checked below)
    if module_name.startswith("tools.") and module_name in lazy_map:
        if names:
            for alias in names:
                if alias.name == "*":
                    continue
                ok, detail = resolve_from_symbol(root, importer, module_name, alias.name, lazy_map)
                if not ok:
                    broken.append({
                        "importer": importer,
                        "file": str(file),
                        "line": getattr(node, "lineno", 0),
                        "import_stmt": f"from {module_name} import {alias.name}",
                        "target": f"{module_name}.{alias.name}",
                        "reason": detail,
                    })
        return

    if module_to_path(root, module_name) is None:
        broken.append({
            "importer": importer,
            "file": str(file),
            "line": getattr(node, "lineno", 0),
            "import_stmt": stmt,
            "target": module_name,
            "reason": f"module '{module_name}' missing",
        })
        return

    if names:
        for alias in names:
            if alias.name == "*":
                continue
            ok, detail = resolve_from_symbol(root, importer, module_name, alias.name, lazy_map)
            if not ok:
                broken.append({
                    "importer": importer,
                    "file": str(file),
                    "line": getattr(node, "lineno", 0),
                    "import_stmt": f"from {module_name} import {alias.name}",
                    "target": f"{module_name}.{alias.name}",
                    "reason": detail,
                })


# ─── Entrypoint BFS ──────────────────────────────────────────────────────────
def build_internal_edges(root: Path, lazy_map: dict[str, str]) -> dict[str, set[str]]:
    """Build module -> set(internal modules imported) adjacency."""
    if not _MODULE_IMPORTS:
        _populate_index(root)
    edges: dict[str, set[str]] = {}
    for mod, records in _MODULE_IMPORTS.items():
        edges.setdefault(mod, set())
        pkg_parts = mod.split(".")[:-1]
        for record in records:
            imp_mod = record["module"]
            level = record["level"]
            for alias in record["names"]:
                if imp_mod is None:  # `import a.b.c`
                    target = alias.name
                    if not is_internal(root, target.split(".")[0]):
                        continue
                    edges[mod].add(lazy_map.get(target, target))
                elif level:  # relative
                    base = pkg_parts[: max(0, len(pkg_parts) - level + 1)]
                    rel_mod = ".".join([*base, imp_mod] if imp_mod else base)
                    if not rel_mod or not is_internal(root, rel_mod.split(".")[0]):
                        continue
                    edges[mod].add(lazy_map.get(rel_mod, rel_mod))
                else:  # `from a.b import c`
                    if not is_internal(root, imp_mod.split(".")[0]):
                        continue
                    edges[mod].add(lazy_map.get(imp_mod, imp_mod))
    return edges


def reachable_closure(edges: dict[str, set[str]], roots: list[str]) -> set[str]:
    seen: set[str] = set()
    stack = [r for r in roots if r in edges]
    while stack:
        mod = stack.pop()
        if mod in seen:
            continue
        seen.add(mod)
        for nxt in edges.get(mod, ()):
            if nxt not in seen:
                stack.append(nxt)
    return seen


# ─── Main ────────────────────────────────────────────────────────────────────
def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=None, help="backend root (default: this script's parent parent)")
    parser.add_argument("--entrypoints", nargs="*", default=_DEFAULT_ENTRYPOINTS, help="entrypoint files")
    parser.add_argument("--json", default=None, help="write full JSON report to this path")
    parser.add_argument("--live-only", action="store_true", help="only report broken imports inside reachable closure")
    parser.add_argument(
        "--scope",
        choices=["prod", "all"],
        default="prod",
        help="'prod' = tests/alembic বাদ (দ্রুত, ডিফল্ট); 'all' = সব ফাইল",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve() if args.root else Path(__file__).resolve().parent.parent
    lazy_map = load_lazy_tools_map(root)

    extra_skip = frozenset() if args.scope == "all" else _PROD_SKIP
    _populate_index(root, extra_skip)
    modules: dict[str, Path] = dict(_MODULE_INDEX)

    broken: list[dict[str, Any]] = []
    for mod in sorted(modules):
        broken.extend(audit_module(root, mod, lazy_map))

    edges = build_internal_edges(root, lazy_map)
    entry_roots = [path_to_module(root, (root / ep).resolve()) for ep in args.entrypoints if (root / ep).exists()]
    live = reachable_closure(edges, entry_roots)

    for rec in broken:
        rec["live"] = rec.get("importer") in live

    orphans = sorted(
        (m for m in modules if m not in live),
        key=lambda m: (m.split(".")[0], m),
    )

    live_broken = [b for b in broken if b.get("live")]
    report: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "root": str(root),
        "entrypoints": entry_roots,
        "stats": {
            "total_modules": len(modules),
            "reachable_modules": len(live),
            "orphan_modules": len(orphans),
            "broken_imports": len(broken),
            "live_broken_imports": len(live_broken),
        },
        "broken_imports": broken,
        "orphans": [{"module": m, "lines": _MODULE_LINES.get(m, 0)} for m in orphans],
    }

    if args.json:
        Path(args.json).write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"📦 Backend root: {root}")
    print(f"   modules scanned : {len(modules)}")
    print(f"   reachable       : {len(live)}")
    print(f"   orphan modules  : {len(orphans)}")
    print(f"   broken imports  : {len(broken)}  (live: {len(live_broken)}, latent: {len(broken) - len(live_broken)})")

    shown = live_broken if args.live_only else broken
    if shown:
        print("\n❌ Broken imports:")
        for b in sorted(shown, key=lambda r: (not r.get("live", False), r["importer"])):
            mark = "🔴LIVE" if b.get("live") else "⚪lat "
            print(f"  {mark} {b['importer']}:{b.get('line', '?')}  {b.get('import_stmt', '<parse error>')}")
            print(f"        -> {b['reason']}")
    else:
        print("\n✅ No broken internal imports detected.")

    if not args.live_only:
        top = Counter(m.split(".")[0] for m in orphans)
        print("\n📭 Orphan modules by top-level package (count):")
        for pkg, cnt in top.most_common():
            print(f"  {pkg:12s} {cnt}")

    if args.json:
        print(f"\n💾 JSON report written to: {args.json}")

    return 1 if live_broken else 0


if __name__ == "__main__":
    sys.exit(main())

