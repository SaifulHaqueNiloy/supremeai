# pyerrorfix

**Reusable, zero-dependency Python error-detection & auto-fix engine for GitHub Actions pipelines.**

`pyerrorfix` statically scans Python source for the most common runtime errors —
`SyntaxError`, `NameError`, `ZeroDivisionError`, missing `await`, raw SQL
injection, hardcoded secrets, broad `except`, f-string logging, Pydantic v1
deprecations, and **50+ more** — and auto-fixes the safe ones in place.

It was built for the [`SaifulHaqueNiloy/supremeai`](https://github.com/SaifulHaqueNiloy/supremeai)
FastAPI + SQLAlchemy + async backend, but it is **fully reusable**: drop it into
any Python repo (yours or a user's) and it just runs.

---

## Why another linter?

The existing `auto_fix.yml` pipeline only ran `isort` / `black` / `ruff`. Those
are **formatters** — they fix *style*, not *bugs*. `pyerrorfix` finds the
**semantic** errors that formatters can't:

| Formatter (ruff/black) | pyerrorfix |
|---|---|
| `E501` line too long | `missing-await` — coroutine never runs |
| `F401` unused import | `shell-injection` — subprocess(shell=True) |
| `I001` import order | `raw-sql-injection` — f-string SQL |
| — | `hardcoded-secret` — API key in source |
| — | `broad-except` — swallows KeyboardInterrupt |
| — | `fstring-in-logging` — eager formatting |
| — | `pydantic-validation-gap` — `.dict()` removed in v2 |

The two are **complementary** — run both.

---

## Install

```bash
# from source (zero dependencies — Python 3.8+ stdlib only)
pip install -e ./pyerrorfix

# or run directly without installing
python -m pyerrorfix --help
```

---

## CLI

```bash
# scan a path, print human-readable
python -m pyerrorfix analyze backend/

# scan + auto-fix in place
python -m pyerrorfix analyze backend/ --fix

# read code from stdin (used by the web dashboard)
echo 'x = 1/0' | python -m pyerrorfix analyze --stdin --format json

# emit SARIF for GitHub code scanning
python -m pyerrorfix analyze backend/ --format sarif > results.sarif

# print the full error catalog (JSON)
python -m pyerrorfix catalog --format json

# exit codes: 0 = no errors, 1 = errors found, 2 = invocation error
```

### Output formats

| `--format` | use case |
|---|---|
| `console` (default) | developer terminal |
| `json` | programmatic / dashboard API |
| `sarif` | GitHub **Security** tab (native) |
| `markdown` | PR comment / artifact |

---

## GitHub Action (drop-in)

```yaml
# .github/workflows/pyerrorfix.yml
jobs:
  pyerrorfix:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      pull-requests: write
      security-events: write   # to upload SARIF
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }

      - name: Detect + auto-fix + SARIF
        run: |
          python -m pyerrorfix analyze backend --fix --format sarif > pyerrorfix.sarif || true
          python -m pyerrorfix analyze backend --format console --quiet || true

      - name: Upload SARIF to Security tab
        if: always()
        uses: github/codeql-action/upload-sarif@v3
        with: { sarif_file: pyerrorfix.sarif, category: pyerrorfix }

      - name: Open PR with fixes
        uses: peter-evans/create-pull-request@v6
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
          commit-message: "fix(pyerrorfix): auto-fix Python errors [skip ci]"
          title: "🤖 pyerrorfix: auto-fix Python errors"
          branch: "chore/pyerrorfix-${{ github.run_id }}"
```

A ready-to-use workflow is in [`.github/workflows/autofix.yml`](.github/workflows/autofix.yml)
and a composite action wrapper in [`action.yml`](action.yml).

---

## Configuration (optional)

Create `.pyerrorfix.json` in your repo root to silence or re-severity rules:

```json
{
  "rules": {
    "missing-type-hint": { "enabled": false },
    "assert-in-prod":    { "enabled": false },
    "hardcoded-secret":  { "severity": "error" }
  }
}
```

YAML is also supported if PyYAML is installed (`.pyerrorfix.yaml`).

---

## What it detects (66 errors across 12 categories)

| Category | Bengali name | Errors |
|---|---|---|
| Core Python | কোর পাইথন এরর | SyntaxError, IndentationError, TabError, NameError, TypeError, ValueError, AttributeError, IndexError, KeyError, UnboundLocalError, ZeroDivisionError, NotImplementedError, RecursionError, MemoryError, AssertionError, OverflowError, StopIteration, RuntimeError |
| Import & Module | ইমপোর্ট ও মডিউল এরর | ModuleNotFoundError, ImportError, circular import, wildcard import, unused import |
| File & OS | ফাইল ও অপারেটিং সিস্টেম এরর | FileNotFoundError, PermissionError, TimeoutError, EOFError, IsADirectoryError, NotADirectoryError, BlockingIOError |
| Asyncio | এসিনক্রোনাস এরর | coroutine never awaited, CancelledError, InvalidStateError, no running loop, unhandled task exception |
| Database & ORM | ডাটাবেস ও SQLAlchemy এরর | IntegrityError, OperationalError, ProgrammingError, DataError, StatementError (SQLi), NoResultFound, MultipleResultsFound |
| Web & API | ওয়েব ও API এরর | ValidationError, HTTPException, RequestValidationError, SerializationError |
| **Concurrency (NEW)** | কনকারেন্সি এরর | mutable shared state, lock without context, thread-unsafe singleton |
| **Typing (NEW)** | টাইপিং এরর | NoneType member access, Optional without None check, missing type hint |
| **Security (NEW)** | সিকিউরিটি এরর | hardcoded secret, eval/exec, pickle deserialization, shell injection, weak hash |
| **Resources (NEW)** | রিসোর্স লিক এরর | unclosed resource, leaked connection |
| **Deprecation (NEW)** | ডেপ্রিকেশন এরর | removed API (imp/distutils/cgi), moved stdlib name, Python 2 constructs |
| **Logging (NEW)** | লগিং ও এক্সেপশন এরর | f-string in logging, broad except, raise without `from`, print() in production |

> The 6 **(NEW)** categories and several sub-errors (e.g. `NoResultFound`,
> `MultipleResultsFound`, `IsADirectoryError`, `BlockingIOError`,
> `RequestValidationError`) were **missing** from the original error list and
> have been added.

Run `python -m pyerrorfix catalog` to see the full list with Bengali descriptions.

---

## Auto-fixers (idempotent, safe)

| Fixer | What it does |
|---|---|
| `AwaitFixer` | Inserts `await` before known-coroutine calls |
| `BareExceptFixer` | `except:` → `except Exception:` |
| `FStringLogFixer` | `logger.info(f"x {y}")` → `logger.info('x %s', y)` |
| `UnusedImportFixer` | Removes single-name unused imports |
| `ImportSortFixer` | Groups stdlib / third-party / local, sorts within group |

All fixers re-detect after each pass so line numbers stay accurate, and they
are idempotent (running twice = running once). Fixers that would be ambiguous
(e.g. wrapping a multi-line `open()` in `with`) report a suggestion but do not
auto-rewrite — the developer applies them manually.

---

## Architecture

```
pyerrorfix/
├── pyerrorfix/
│   ├── cli.py              # argparse CLI (analyze / catalog / version)
│   ├── config.py           # JSON + optional YAML config loader
│   ├── core/
│   │   ├── issue.py        # Issue / Severity / Category / ScanResult dataclasses
│   │   ├── scanner.py      # orchestrator: detectors → fixers → re-detect
│   │   ├── reporter.py     # console / JSON / SARIF / Markdown
│   │   └── catalog.py      # the 66-error knowledge base (Bengali + English)
│   ├── detectors/          # 13 AST visitors, one per category
│   ├── fixers/             # 5 idempotent source-to-source fixers
│   └── rules/
├── action.yml              # composite GitHub Action
├── .github/workflows/autofix.yml
└── examples/sample_buggy.py
```

**Zero dependencies** — `ast`, `tokenize`, `re`, `pathlib`, `json`, `argparse`
from the stdlib only. Optional PyYAML for YAML config.

---

## Known limitations (single-file analysis)

`pyerrorfix` analyzes **one file at a time**. Names defined in another module
and imported via relative/`__init__` re-exports may show as `NameError`. This
is the standard trade-off for a fast, dependency-free linter (same as `pyflakes`
without cross-file resolution). To silence for a known-safe case, add the rule
to your `.pyerrorfix.json`:

```json
{ "rules": { "undefined-name": { "enabled": false } } }
```

---

## License

MIT
