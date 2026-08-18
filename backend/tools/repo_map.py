"""Tree-sitter Repo Map — compact codebase architecture summarizer.

বাংলা মন্তব্য: বড় কোডবেসে (৫০০+ ফাইল) সব কোড LLM-এ পাঠানো অসম্ভব। এই মডিউল পুরো
রিপোজিটরির AST পার্স করে সবচেয়ে গুরুত্বপূর্ণ ক্লাস/ফাংশন সিগনেচার ও ইমপোর্ট গ্রাফ
নিয়ে একটি সুপার-কম্প্যাক্ট ম্যাপ (<max_tokens) বানায়। PageRank দিয়ে গুরুত্ব র‍্যাঙ্ক করা হয়।

`tree_sitter` ও `tree_sitter_language_pack` lazy import করা হয় — প্যাকেজ না থাকলে
মডিউল ইমপোর্ট ফেইল করবে না, শুধু fallback (ফাইল-লিস্ট মাত্র) রিটার্ন করবে।
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

from loguru import logger

# Skip these directories entirely when walking the repo
_DEFAULT_SKIP_DIRS = {
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    "env",
    ".env",
    "dist",
    "build",
    ".next",
    ".turbo",
    "coverage",
    "htmlcov",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
}

# Map file extension -> tree-sitter language key (supported by tree-sitter-language-pack)
_EXT_LANG: dict[str, str] = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".go": "go",
    ".rs": "rust",
    ".java": "java",
}

# Per-language definition node types we want to surface in the map
_DEF_NODE_TYPES: dict[str, set[str]] = {
    "python": {"function_definition", "async_function_definition", "class_definition"},
    "javascript": {
        "function_declaration",
        "class_declaration",
        "method_definition",
        "generator_function_declaration",
    },
    "typescript": {
        "function_declaration",
        "class_declaration",
        "method_definition",
        "generator_function_declaration",
        "interface_declaration",
        "type_alias_declaration",
    },
    "go": {"function_declaration", "method_declaration", "type_declaration"},
    "rust": {"function_item", "struct_item", "enum_item", "impl_item", "trait_item"},
    "java": {"method_declaration", "class_declaration", "interface_declaration"},
}

# Field names for the symbol's name + parameters (most languages share these)
_NAME_FIELD = "name"
_PARAMS_FIELD = "parameters"


@dataclass
class Symbol:
    name: str
    kind: str  # "function" | "class" | "method" | ...
    signature: str
    file: str
    line: int
    calls: list[str] = field(default_factory=list)


@dataclass
class RepoMap:
    root: str
    files: list[str]
    symbols: list[Symbol]
    ranked_files: list[str] = field(default_factory=list)
    map_text: str = ""


class RepoMapBuilder:
    """Builds a token-budgeted, PageRank-ranked map of a codebase."""

    def __init__(
        self,
        root: str,
        max_tokens: int = 1500,
        include_exts: list[str] | None = None,
        skip_dirs: set[str] | None = None,
    ):
        self.root = os.path.abspath(root)
        self.max_tokens = max_tokens
        self.include_exts = set(include_exts or list(_EXT_LANG.keys()))
        self.skip_dirs = (skip_dirs or set()) | _DEFAULT_SKIP_DIRS
        self._parsers: dict[str, Any] = {}
        self._ts_available = self._check_ts()

    @staticmethod
    def _check_ts() -> bool:
        try:
            import tree_sitter  # noqa: F401
            import tree_sitter_language_pack  # noqa: F401

            return True
        except Exception as exc:  # pragma: no cover - optional dependency
            logger.warning(f"RepoMapBuilder: tree_sitter unavailable ({exc}); using fallback map.")
            return False

    # ── filesystem walk ──────────────────────────────────────────────
    def _discover_files(self) -> list[str]:
        found: list[str] = []
        for dirpath, dirnames, filenames in os.walk(self.root):
            dirnames[:] = [d for d in dirnames if d not in self.skip_dirs]
            for fn in filenames:
                ext = os.path.splitext(fn)[1].lower()
                if ext in self.include_exts:
                    found.append(os.path.join(dirpath, fn))
        found.sort()
        return found

    # ── parsing ──────────────────────────────────────────────────────
    def _get_parser(self, lang: str):
        if lang in self._parsers:
            return self._parsers[lang]
        import tree_sitter
        import tree_sitter_language_pack as tslp

        language = tslp.get_language(lang)
        parser = tree_sitter.Parser(language)
        self._parsers[lang] = parser
        return parser

    def _extract_symbols(self, path: str, lang: str) -> list[Symbol]:
        try:
            with open(path, "rb") as fh:
                source = fh.read()
        except Exception as exc:  # pragma: no cover
            logger.warning(f"RepoMapBuilder: cannot read {path}: {exc}")
            return []

        parser = self._get_parser(lang)
        tree = parser.parse(source)
        def_types = _DEF_NODE_TYPES.get(lang, set())
        symbols: list[Symbol] = []

        def walk(node: Any) -> None:
            if node.type in def_types:
                name_node = node.child_by_field_name(_NAME_FIELD)
                name = name_node.text.decode("utf-8", "replace") if name_node else "<anon>"
                # signature: kind + name + params (truncated)
                params_node = node.child_by_field_name(_PARAMS_FIELD)
                params = ""
                if params_node is not None:
                    ptxt = params_node.text.decode("utf-8", "replace")
                    if len(ptxt) > 80:
                        ptxt = ptxt[:77] + "..."
                    params = ptxt
                kind = node.type.replace("_definition", "").replace("_declaration", "")
                sig = f"{kind} {name}{(' ' + params) if params else ''}"
                symbols.append(
                    Symbol(
                        name=name,
                        kind=kind,
                        signature=sig,
                        file=path,
                        line=node.start_point[0] + 1,
                    )
                )
            for child in node.children:
                walk(child)

        walk(tree.root_node)
        return symbols

    # ── import graph + PageRank ──────────────────────────────────────
    def _build_import_edges(self, files: list[str]) -> dict[str, set[str]]:
        """Lightweight import edge detection (file -> imported sibling files)."""
        edges: dict[str, set[str]] = {f: set() for f in files}
        by_module: dict[str, str] = {}
        for f in files:
            rel = os.path.relpath(f, self.root)
            module = os.path.splitext(rel)[0].replace(os.sep, ".")
            by_module[module] = f

        for f in files:
            try:
                with open(f, "r", encoding="utf-8", errors="replace") as fh:
                    text = fh.read()
            except Exception:
                continue
            # crude but cheap: match `from x import` / `import x` for python,
            # and relative import-like paths for js/ts (`from './foo'`).
            imported_modules: list[str] = []
            for line in text.splitlines():
                s = line.strip()
                if s.startswith("from ") and " import " in s:
                    mod = s[5:].split(" import ")[0].strip()
                    if mod.startswith(".") or mod in by_module:
                        imported_modules.append(mod)
                elif s.startswith("import "):
                    mod = s[7:].split()[0].strip()
                    if mod in by_module:
                        imported_modules.append(mod)
                elif " from '" in s or ' from "' in s:
                    seg = s.split(" from ")[-1].strip().strip("'\"")
                    if seg.startswith("."):
                        imported_modules.append(seg)
            for mod in imported_modules:
                target = self._resolve_module(mod, f, by_module)
                if target and target != f:
                    edges[f].add(target)
        return edges

    @staticmethod
    def _resolve_module(mod: str, from_file: str, by_module: dict[str, str]) -> str | None:
        if mod in by_module:
            return by_module[mod]
        if mod.startswith("."):
            # resolve relative import against the importing file's module path
            parts = os.path.splitext(os.path.relpath(from_file))[0].replace(os.sep, ".").split(".")
            levels = len(mod) - len(mod.lstrip("."))
            top = parts[: len(parts) - levels] if levels else parts
            rel = mod.lstrip(".")
            cand = ".".join(filter(None, [*top, *rel.split(".")]))
            return by_module.get(cand)
        return None

    @staticmethod
    def _pagerank(edges: dict[str, set[str]], iterations: int = 30, damping: float = 0.85) -> dict[str, float]:
        """Minimal PageRank (pure python, no networkx dependency)."""
        nodes = list(edges.keys())
        if not nodes:
            return {}
        rank = {n: 1.0 / len(nodes) for n in nodes}
        out_links = {n: [t for t in edges[n] if t in edges] for n in nodes}
        for _ in range(iterations):
            new_rank = {n: (1 - damping) / len(nodes) for n in nodes}
            for n in nodes:
                out = out_links[n]
                if out:
                    share = damping * rank[n] / len(out)
                    for t in out:
                        new_rank[t] += share
                else:
                    # dangling node: distribute to all
                    share = damping * rank[n] / len(nodes)
                    for t in nodes:
                        new_rank[t] += share
            rank = new_rank
        return rank

    # ── map assembly ────────────────────────────────────────────────
    @staticmethod
    def _rel(root: str, path: str) -> str:
        """Relative path normalized to forward slashes (cross-platform stable)."""
        return os.path.relpath(path, root).replace(os.sep, "/")

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        # rough heuristic: ~4 chars per token for code
        return max(1, len(text) // 4)

    def build(self) -> RepoMap:
        files = self._discover_files()
        map_obj = RepoMap(root=self.root, files=files, symbols=[])

        if not self._ts_available:
            # Fallback: just list files (still useful, near-zero cost)
            map_obj.map_text = "Repository file index (tree_sitter unavailable):\n" + "\n".join(
                self._rel(self.root, f) for f in files
            )
            return map_obj

        all_symbols: list[Symbol] = []
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            lang = _EXT_LANG.get(ext)
            if not lang:
                continue
            try:
                syms = self._extract_symbols(f, lang)
            except Exception as exc:  # pragma: no cover
                logger.warning(f"RepoMapBuilder: parse failed for {f}: {exc}")
                continue
            for s in syms:
                s.file = self._rel(self.root, s.file)
            all_symbols.extend(syms)

        map_obj.symbols = all_symbols

        # Rank files by PageRank over the import graph
        edges = self._build_import_edges(files)
        ranks = self._pagerank(edges)
        ranked = sorted(files, key=lambda f: ranks.get(f, 0.0), reverse=True)
        map_obj.ranked_files = [self._rel(self.root, f) for f in ranked]

        # Greedily assemble map within token budget
        lines: list[str] = [f"# Repo Map ({len(files)} files, {len(all_symbols)} symbols, budget={self.max_tokens}tok)"]
        used = self._estimate_tokens("\n".join(lines))
        # Header: ranked file list (compact)
        file_index = "FILES (ranked): " + " | ".join(self._rel(self.root, f) for f in ranked)
        lines.append(file_index)
        used += self._estimate_tokens(file_index)

        # Then top symbols per highest-ranked files until budget
        sym_by_file: dict[str, list[Symbol]] = {}
        for s in all_symbols:
            sym_by_file.setdefault(s.file, []).append(s)
        for f in ranked:
            rel = self._rel(self.root, f)
            syms = sym_by_file.get(rel, [])
            if not syms:
                continue
            block = f"\n## {rel}\n" + "\n".join(f"  L{s.line}: {s.signature}" for s in syms[:25])
            cost = self._estimate_tokens(block)
            if used + cost > self.max_tokens:
                # try to fit at least the file header
                if used + self._estimate_tokens(f"\n## {rel} (truncated)") <= self.max_tokens:
                    lines.append(f"\n## {rel} (truncated)")
                break
            lines.append(block)
            used += cost

        map_obj.map_text = "\n".join(lines)
        return map_obj


def build_repo_map(root: str, max_tokens: int = 1500) -> str:
    """Convenience helper returning the map text for an agent context."""
    return RepoMapBuilder(root=root, max_tokens=max_tokens).build().map_text
