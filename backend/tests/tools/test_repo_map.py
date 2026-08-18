"""Unit tests for backend.tools.repo_map (Tree-sitter Repo Map)."""

from __future__ import annotations

import os
import tempfile
import textwrap

from tools.repo_map import RepoMapBuilder, build_repo_map


def _write(tmp: str, rel: str, content: str) -> None:
    path = os.path.join(tmp, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)


def _make_fixture(tmp: str) -> None:
    _write(
        tmp,
        "pkg/core.py",
        textwrap.dedent(
            """
            def bootstrap(config):
                return config

            class Engine:
                def run(self, x):
                    return x
            """
        ),
    )
    _write(
        tmp,
        "pkg/worker.py",
        textwrap.dedent(
            """
            from pkg.core import bootstrap, Engine

            def start():
                e = Engine()
                return e.run(bootstrap({}))
            """
        ),
    )
    _write(
        tmp,
        "pkg/skipme.txt",
        "not a source file\n",
    )


def test_repo_map_finds_symbols_and_ranks_imported_file_first():
    with tempfile.TemporaryDirectory() as tmp:
        _make_fixture(tmp)
        builder = RepoMapBuilder(root=tmp, max_tokens=1500)
        result = builder.build()

        # symbols extracted
        names = {s.name for s in result.symbols}
        assert {"bootstrap", "Engine", "run", "start"} <= names, names

        # imported file (core.py) should rank at/near the top via PageRank
        assert "pkg/core.py" in result.ranked_files
        assert result.ranked_files.index("pkg/core.py") <= result.ranked_files.index("pkg/worker.py")

        # map text within token budget and references the top symbol
        assert "Engine" in result.map_text
        assert RepoMapBuilder._estimate_tokens(result.map_text) <= 1500


def test_repo_map_respects_token_budget():
    with tempfile.TemporaryDirectory() as tmp:
        # create a large file with many symbols to exceed budget
        big = "\n".join(f"def func_{i}(a, b, c, d):\n    return {i}\n" for i in range(200))
        _write(tmp, "bigmod.py", big)
        builder = RepoMapBuilder(root=tmp, max_tokens=300)
        result = builder.build()
        assert RepoMapBuilder._estimate_tokens(result.map_text) <= 300


def test_repo_map_fallback_when_tree_sitter_missing(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        _make_fixture(tmp)
        builder = RepoMapBuilder(root=tmp, max_tokens=1500)
        monkeypatch.setattr(RepoMapBuilder, "_check_ts", staticmethod(lambda: False))
        builder._ts_available = False
        result = builder.build()
        # Fallback still lists files
        assert "pkg/core.py" in result.map_text
        assert result.symbols == []


def test_build_repo_map_helper():
    with tempfile.TemporaryDirectory() as tmp:
        _make_fixture(tmp)
        text = build_repo_map(tmp, max_tokens=800)
        assert isinstance(text, str) and len(text) > 0
