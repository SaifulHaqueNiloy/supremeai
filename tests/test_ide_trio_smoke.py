"""Standalone smoke test for the SupremeAI IDE Trio Pipeline adapters + Trio 2.0.

Run from the repo root:
    python tests/test_ide_trio_smoke.py

Tests:
    1. KiloReviewer basic review (security/lint pattern detection)
    2. ClineChecker local production checks
    3. TrioAgentResult serialization
    4. End-to-end reviewer + checker chain
    5. ClineChecker AST syntax & import validation
    6. Self-healing loop with mocked reviewer/checker issues
    7. Pre-cognitive cache hit simulation
    8. End-to-end pipeline (clean + faulty code paths)
"""

import asyncio
import importlib.util
import sys
import types
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

# Ensure Unicode output works even on cp1252 Windows consoles.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def _load_adapters():
    """Load trio_adapters.py directly via importlib, bypassing the heavy
    `agents/__init__.py` (which pulls in loguru / litellm / pandas chains)."""
    candidates = [
        Path(r"F:\supremeai backup\backend\agents\ide\trio_adapters.py"),
        Path(r"F:\supremeai backup\.kilo\worktrees\dirt-octopus\backend\agents\ide\trio_adapters.py"),
    ]
    path = next((p for p in candidates if p.exists()), None)
    if not path:
        raise RuntimeError("trio_adapters.py not found")

    spec = importlib.util.spec_from_file_location("trio_adapters_standalone", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["trio_adapters_standalone"] = mod
    spec.loader.exec_module(mod)
    return mod


def _load_pipeline(adapters_mod):
    """Load trio_pipeline.py and register adapters as 'agents.ide.trio_adapters'
    so the pipeline's lazy import in __init__ resolves without the heavy package."""
    # Stub loguru if not installed (trio_pipeline.py imports it at module level)
    if "loguru" not in sys.modules:
        try:
            import loguru  # noqa: F401
        except ImportError:
            stub = types.ModuleType("loguru")
            logger_stub = MagicMock()
            logger_stub.info = lambda *a, **kw: None
            logger_stub.warning = lambda *a, **kw: None
            logger_stub.error = lambda *a, **kw: None
            logger_stub.debug = lambda *a, **kw: None
            stub.logger = logger_stub
            sys.modules["loguru"] = stub

    # Build the agents.ide package hierarchy in sys.modules
    agents_pkg = types.ModuleType("agents")
    ide_pkg = types.ModuleType("agents.ide")
    sys.modules["agents"] = agents_pkg
    sys.modules["agents.ide"] = ide_pkg
    sys.modules["agents.ide.trio_adapters"] = adapters_mod

    candidates = [
        Path(r"F:\supremeai backup\backend\core\orchestration\trio_pipeline.py"),
    ]
    path = next((p for p in candidates if p.exists()), None)
    if not path:
        raise RuntimeError("trio_pipeline.py not found")

    spec = importlib.util.spec_from_file_location("trio_pipeline_test", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["trio_pipeline_test"] = mod
    spec.loader.exec_module(mod)
    return mod


# ── Mock helper classes for self-healing loop test ──────────────────────────

class MockWriter:
    """Simulates a Writer that produces issue-laden code, then repairs it."""

    def __init__(self):
        self.role = "writer"
        self.agent_name = "mock_gemini"
        self._call_count = 0

    async def run(self, prompt, language="python", context=None):
        self._call_count += 1
        if self._call_count == 1:
            # First call: produce code with a bare except (reviewer will flag)
            return MockResult(
                role="writer",
                agent="mock_gemini",
                output="def compute(a: int, b: int) -> int:\n    try:\n        return a / b\n    except:\n        return 0\n",
                confidence=0.9,
                issues=[],
            )
        return MockResult(
            role="writer",
            agent="mock_gemini",
            output="def compute(a: int, b: int) -> int:\n    try:\n        return a / b\n    except ZeroDivisionError:\n        return 0\n",
            confidence=0.95,
            issues=[],
        )

    async def repair(self, prompt, language="python", context=None, issues=None, previous_code=""):
        # Repair: replace bare 'except:' with 'except ZeroDivisionError:'
        fixed = previous_code.replace("except:", "except ZeroDivisionError:")
        self._call_count += 1
        return MockResult(
            role="writer",
            agent="mock_gemini",
            output=fixed,
            confidence=0.95,
            issues=[],
            metadata={"repaired": True, "issues_addressed": len(issues or [])},
        )


class MockResult:
    """Lightweight stand-in for TrioAgentResult that the pipeline consumes."""

    def __init__(self, role, agent, output, confidence, issues=None, suggestions=None,
                 metadata=None):
        from datetime import UTC, datetime
        self.role = role
        self.agent = agent
        self.output = output
        self.confidence = confidence
        self.issues = issues or []
        self.suggestions = suggestions or []
        self.metadata = metadata or {}
        self.timestamp = datetime.now(UTC).isoformat()

    def to_dict(self):
        return {
            "role": self.role,
            "agent": self.agent,
            "output": self.output,
            "confidence": self.confidence,
            "issues": self.issues,
            "suggestions": self.suggestions,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
        }


class MockReviewer:
    """Reviewer that flags 'except:' but passes clean code."""

    def __init__(self):
        self.role = "reviewer"
        self.agent_name = "mock_kilo"

    async def run(self, code, language="python", filepath="", writer_result=None):
        if "except:" in code:
            return MockResult(
                role="reviewer", agent="mock_kilo", output="Review: bare except found",
                confidence=0.8,
                issues=[{
                    "type": "bare_except",
                    "message": "Bare 'except:' on line 3 - catches all exceptions",
                    "severity": "medium",
                    "line": 3,
                    "source": "mock-reviewer",
                }],
                metadata={"language": language, "filepath": filepath, "issues_count": 1},
            )
        return MockResult(
            role="reviewer", agent="mock_kilo", output="Code passed review",
            confidence=0.9,
            issues=[],
            metadata={"language": language, "filepath": filepath, "issues_count": 0},
        )


class MockChecker:
    """Checker that flags AST issues but passes clean code."""

    def __init__(self):
        self.role = "checker"
        self.agent_name = "mock_cline"

    async def run(self, code, language="python", filepath="", reviewer_result=None):
        if "except:" in code:
            return MockResult(
                role="checker", agent="mock_cline", output="Check: bare except",
                confidence=0.7,
                issues=[{
                    "type": "prod_check_ast",
                    "message": "Bare except clause",
                    "severity": "medium",
                    "source": "mock-checker",
                }],
                metadata={
                    "language": language, "filepath": filepath,
                    "ready_for_production": False, "checks": [],
                },
            )
        return MockResult(
            role="checker", agent="mock_cline", output="Production ready",
            confidence=0.9,
            issues=[],
            metadata={
                "language": language, "filepath": filepath,
                "ready_for_production": True, "checks": [],
            },
        )


async def main() -> None:
    results = []
    adapters = _load_adapters()
    KiloReviewer = adapters.KiloReviewer
    ClineChecker = adapters.ClineChecker
    TrioAgentResult = adapters.TrioAgentResult
    pipeline_mod = _load_pipeline(adapters)
    TrioPipeline = pipeline_mod.TrioPipeline

    # ── Test 1: Basic review (KiloReviewer._basic_review) ─────────────
    print("\n=== Test 1: KiloReviewer basic review ===")
    try:
        reviewer = KiloReviewer()
        sample = (
            "def api():\n"
            "    secret = 'abc123'  # bad\n"
            "    print('debug')\n"
            "    eval(input())\n"
            "    try:\n"
            "        pass\n"
            "    except:\n"
            "        pass\n"
            "    # TODO fix\n"
        )
        result = await reviewer.run(sample, language="python")
        assert isinstance(result, TrioAgentResult)
        assert result.role == "reviewer"
        assert result.agent == "kilo"
        types = {i["type"] for i in result.issues}
        print(f"  issues found: {[i['type'] for i in result.issues]}")
        assert "hardcoded_secret" in types, "should flag hardcoded secret"
        assert "eval_usage" in types, "should flag eval()"
        assert "bare_except" in types, "should flag bare except"
        assert "debug_statement" in types, "should flag print()"
        print("  ✅ PASSED")
    except Exception as exc:
        print(f"  ❌ FAILED: {exc}")
        results.append("KiloReviewer.basic_review")

    # ── Test 2: ClineChecker local production checks ───────────────────
    print("\n=== Test 2: ClineChecker local checks ===")
    try:
        checker = ClineChecker()
        good_code = (
            "def add(a: int, b: int) -> int:\n"
            "    try:\n"
            "        return a + b\n"
            "    except TypeError as e:\n"
            "        return 0\n"
        )
        local = await checker._run_local_checks(good_code, "python", "")
        result_map = {k: v["passed"] for k, v in local.items()}
        print(f"  checks: {result_map}")
        assert local["no_debug_statements"]["passed"] is True
        assert local["error_handling"]["passed"] is True
        assert local["type_hints"]["passed"] is True
        assert local["no_hardcoded_secrets"]["passed"] is True
        print("  ✅ PASSED")
    except Exception as exc:
        print(f"  ❌ FAILED: {exc}")
        results.append("ClineChecker.local_checks")

    # ── Test 3: TrioAgentResult serialization ──
    print("\n=== Test 3: TrioAgentResult.to_dict ===")
    try:
        r = TrioAgentResult(role="writer", agent="gemini", output="code", confidence=0.9)
        d = r.to_dict()
        assert d["role"] == "writer" and d["agent"] == "gemini"
        assert d["timestamp"], "timestamp should be auto-filled"
        assert isinstance(d["issues"], list)
        print("  ✅ PASSED")
    except Exception as exc:
        print(f"  ❌ FAILED: {exc}")
        results.append("TrioAgentResult.to_dict")

    # ── Test 4: Pipeline result shape exercised through reviewer → checker
    print("\n=== Test 4: end-to-end reviewer + checker chain ===")
    try:
        reviewer = KiloReviewer()
        checker = ClineChecker()
        code = (
            "def handler(req_id: int) -> str:\n"
            "    try:\n"
            "        return f'ok:{req_id}'\n"
            "    except Exception:\n"
            "        return 'err'\n"
        )
        rv = await reviewer.run(code, language="python", filepath="app.py")
        ck = await checker.run(code, language="python", filepath="app.py", reviewer_result=rv)
        assert rv.agent == "kilo" and ck.agent == "cline"
        assert ck.metadata.get("ready_for_production") is not None
        print(f"  reviewer issues: {len(rv.issues)}, checker ready: {ck.metadata['ready_for_production']}")
        print("  ✅ PASSED")
    except Exception as exc:
        print(f"  ❌ FAILED: {exc}")
        results.append("e2e_chain")

    # ── Test 5: ClineChecker AST syntax & import validation ────────────
    print("\n=== Test 5: ClineChecker AST syntax validation ===")
    try:
        checker = ClineChecker()

        # Valid Python code → should pass
        valid_code = "def greet(name: str) -> str:\n    return f'Hello, {name}'"
        r = checker._run_ast_validation(valid_code, "python")
        assert r["passed"] is True, f"Valid code should pass, got: {r['output']}"
        assert len(r["issues"]) == 0
        print(f"  valid code: passed={r['passed']}")

        # Syntax error → should fail with syntax_error
        bad_syntax = "def broken(:\n    return"
        r2 = checker._run_ast_validation(bad_syntax, "python")
        assert r2["passed"] is False, "Syntax error should fail AST validation"
        assert len(r2["issues"]) >= 1
        assert r2["issues"][0]["type"] == "syntax_error"
        print(f"  syntax error caught: {r2['issues'][0]['type']}")

        # Dangerous import → should fail with dangerous_import
        danger_code = "import os\nimport subprocess\n\ndef main():\n    pass\n"
        r3 = checker._run_ast_validation(danger_code, "python")
        assert r3["passed"] is False, "Dangerous import should fail"
        assert len(r3["issues"]) >= 1
        assert r3["issues"][0]["type"] == "dangerous_import"
        print(f"  dangerous import caught: {r3['issues'][0]['type']}")

        # Clean code with safe imports → should pass
        clean_code = "from typing import Optional\ndef foo(x: int) -> Optional[int]:\n    return x\n"
        r4 = checker._run_ast_validation(clean_code, "python")
        assert r4["passed"] is True, f"Clean code should pass, got issues: {r4['issues']}"
        print("  clean code with safe imports: passed=True")

        print("  ✅ PASSED")
    except Exception as exc:
        print(f"  ❌ FAILED: {exc}")
        results.append("ClineChecker.ast_validation")

    # ── Test 6: Self-healing loop with mocked reviewer issues ──────────
    print("\n=== Test 6: Self-healing loop (mocked) ===")
    try:
        pipeline = TrioPipeline()
        pipeline.writer = MockWriter()
        pipeline.reviewer = MockReviewer()
        pipeline.checker = MockChecker()

        result = await pipeline.execute(
            prompt="Create a safe division function",
            language="python",
            max_iterations=3,
            enable_cache=False,  # disable cache to test the loop
        )

        assert result["status"] == "ready", f"Expected 'ready', got '{result['status']}'"
        assert result["iterations"] > 1, f"Expected multiple iterations, got {result['iterations']}"
        assert result["ready_for_production"] is True
        assert "ZeroDivisionError" in result["generated_code"], "Repair should fix bare except"
        assert "except:" not in result["generated_code"], "No bare except should remain"
        assert len(result["self_healing_logs"]) > 0, "Should have healing logs"
        assert len(result["diff_history"]) > 0, "Should have diff history"
        print(f"  iterations: {result['iterations']}")
        print(f"  status: {result['status']}")
        print(f"  healing logs: {len(result['self_healing_logs'])}")
        print(f"  diff entries: {len(result['diff_history'])}")
        print(f"  code fixed: {'ZeroDivisionError' in result['generated_code']}")
        print("  ✅ PASSED")
    except Exception as exc:
        print(f"  ❌ FAILED: {exc}")
        results.append("self_healing_loop")

    # ── Test 7: Pre-cognitive cache hit simulation ─────────────────────
    print("\n=== Test 7: Pre-cognitive cache hit ===")
    try:
        pipeline = TrioPipeline()

        # Mock SemanticCache to simulate a cache hit
        cached_response = "def health() -> dict:\n    return {'status': 'ok'}"

        class MockCacheEntry:
            def __init__(self, response, model):
                self.response = response
                self.model = model

        class MockSemanticCache:
            async def query_similar(self, prompt, task_type="general"):
                if "health" in prompt.lower():
                    return MockCacheEntry(cached_response, "cached_semantic")
                return None

            async def set(self, prompt, response, task_type="general"):
                pass

        # Inject the mock cache into the SemanticCache class used by the pipeline
        pipeline_mod_semantic = pipeline_mod
        # Patch by monkey-patching the import path used in _pre_cognitive_cache_lookup
        import types as _types
        cache_mod = _types.ModuleType("core.cache.semantic_cache")
        cache_mod.SemanticCache = MockSemanticCache
        # Also stub core.cache package
        if "core" not in sys.modules:
            sys.modules["core"] = _types.ModuleType("core")
        if "core.cache" not in sys.modules:
            sys.modules["core.cache"] = _types.ModuleType("core.cache")
        sys.modules["core.cache.semantic_cache"] = cache_mod

        # Reload pipeline to pick up the mock, or directly patch the method
        # Simpler: directly call _pre_cognitive_cache_lookup with mocked cache
        cached_result = await pipeline._pre_cognitive_cache_lookup(
            prompt="Create a health endpoint",
            language="python",
            enable_cache=True,
        )

        assert cached_result is not None, "Cache should have hit for 'health' prompt"
        assert cached_result["cached"] is True
        assert cached_result["status"] == "cached"
        assert cached_result["iterations"] == 0
        assert cached_result["ready_for_production"] is True
        assert cached_result["generated_code"] == cached_response
        print(f"  cached: {cached_result['cached']}")
        print(f"  status: {cached_result['status']}")
        print(f"  iterations: {cached_result['iterations']}")
        print(f"  code length: {len(cached_result['generated_code'])} chars")
        print("  ✅ PASSED")
    except Exception as exc:
        print(f"  ❌ FAILED: {exc}")
        results.append("cache_hit_simulation")

    # ── Test 8: End-to-end pipeline (clean code path) ─────────────────
    print("\n=== Test 8: End-to-end pipeline (clean code, mocked writer) ===")
    try:
        pipeline = TrioPipeline()

        class CleanWriter:
            role = "writer"
            agent_name = "mock_gemini"

            async def run(self, prompt, language="python", context=None):
                return MockResult(
                    role="writer", agent="mock_gemini",
                    output="def add(a: int, b: int) -> int:\n    return a + b\n",
                    confidence=0.95, issues=[],
                )

        class CleanReviewer:
            role = "reviewer"
            agent_name = "mock_kilo"

            async def run(self, code, language="python", filepath="", writer_result=None):
                return MockResult(
                    role="reviewer", agent="mock_kilo", output="Code passed review",
                    confidence=0.9, issues=[],
                    metadata={"language": language, "filepath": filepath, "issues_count": 0},
                )

        class CleanChecker:
            role = "checker"
            agent_name = "mock_cline"

            async def run(self, code, language="python", filepath="", reviewer_result=None):
                return MockResult(
                    role="checker", agent="mock_cline", output="Production ready",
                    confidence=0.9, issues=[],
                    metadata={
                        "language": language, "filepath": filepath,
                        "ready_for_production": True, "checks": [],
                    },
                )

        pipeline.writer = CleanWriter()
        pipeline.reviewer = CleanReviewer()
        pipeline.checker = CleanChecker()

        result = await pipeline.execute(
            prompt="Add two integers",
            language="python",
            max_iterations=3,
            enable_cache=False,
        )

        assert result["status"] == "ready"
        assert result["iterations"] == 1, f"Clean code should need 1 iteration, got {result['iterations']}"
        assert result["ready_for_production"] is True
        assert result["generated_code"] == "def add(a: int, b: int) -> int:\n    return a + b\n"
        assert len(result["self_healing_logs"]) == 1  # one log entry: "Review: 0 | Check: 0"
        print(f"  status: {result['status']}")
        print(f"  iterations: {result['iterations']}")
        print(f"  ready: {result['ready_for_production']}")
        print(f"  healing logs: {len(result['self_healing_logs'])}")
        print("  ✅ PASSED")
    except Exception as exc:
        print(f"  ❌ FAILED: {exc}")
        results.append("e2e_clean_pipeline")

    # ── Summary ──
    print("\n=======================")
    if results:
        print(f"❌ {len(results)} test(s) FAILED: {results}")
        sys.exit(1)
    print("✅ ALL 8 SMOKE TESTS PASSED")
    sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
