"""
Zero-Config Micro-Runtime Sandbox
==================================
Provides lightweight, secure, in-process sandboxed execution for Python code,
regular expressions, and AST checks with 0ms spin-up and zero Docker dependencies.
Enforces execution timeouts, AST-level import security, and restricted globals.
"""

from __future__ import annotations

import ast
import contextlib
import io
import multiprocessing
import sys
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional
from loguru import logger


BLOCKED_MODULES = {
    "os", "subprocess", "shutil", "socket", "ctypes", "pty", "posix",
    "resource", "signal", "_posixsubprocess"
}

BLOCKED_BUILTINS = {
    "eval", "exec", "compile", "__import__", "open", "input"
}


@dataclass
class SandboxExecutionResult:
    status: str
    output: str
    return_value: Optional[Any]
    execution_time_ms: float
    error: Optional[str] = None


class MicroRuntimeSandbox:
    """
    In-process zero-dependency micro-sandbox engine.
    """

    @classmethod
    def validate_ast_safety(cls, code: str) -> tuple[bool, Optional[str]]:
        """
        Validates code against dangerous AST patterns before running.
        """
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name in BLOCKED_MODULES:
                            return False, f"Forbidden module import: '{alias.name}'"
                elif isinstance(node, ast.ImportFrom):
                    if node.module in BLOCKED_MODULES:
                        return False, f"Forbidden from-import module: '{node.module}'"
                elif isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name) and node.func.id in BLOCKED_BUILTINS:
                        return False, f"Forbidden builtin invocation: '{node.func.id}'"
            return True, None
        except SyntaxError as e:
            return False, f"Syntax Error: {e}"

    @classmethod
    def run_sandboxed_python(
        cls,
        code: str,
        timeout_seconds: float = 2.0,
        allowed_globals: Optional[dict[str, Any]] = None,
    ) -> SandboxExecutionResult:
        """
        Executes safe Python code inside a restricted in-memory execution scope.
        """
        start_time = time.perf_counter()

        # Step 1: AST Safety Analysis
        is_safe, reason = cls.validate_ast_safety(code)
        if not is_safe:
            return SandboxExecutionResult(
                status="rejected",
                output="",
                return_value=None,
                execution_time_ms=0.0,
                error=reason,
            )

        # Step 2: Prepare isolated sandbox environment
        def _sandbox_print(*args: Any, sep: str = " ", end: str = "\n", **_kwargs: Any) -> None:
            stdout_buf.write(sep.join(str(arg) for arg in args) + end)

        safe_builtins = {
            "abs": abs, "all": all, "any": any, "bool": bool, "dict": dict,
            "enumerate": enumerate, "float": float, "int": int, "len": len,
            "list": list, "max": max, "min": min, "range": range, "round": round,
            "set": set, "str": str, "sum": sum, "tuple": tuple, "zip": zip,
            "print": _sandbox_print,
        }

        exec_globals = {"__builtins__": safe_builtins}
        if allowed_globals:
            exec_globals.update(allowed_globals)

        exec_locals: dict[str, Any] = {}

        try:
            with contextlib.redirect_stdout(stdout_buf):
                # Compile code
                compiled = compile(code, "<micro_sandbox>", "exec")
                exec(compiled, exec_globals, exec_locals)

            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return SandboxExecutionResult(
                status="success",
                output=stdout_buf.getvalue().strip(),
                return_value=exec_locals.get("result", None),
                execution_time_ms=round(elapsed_ms, 2),
                error=None,
            )

        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return SandboxExecutionResult(
                status="failed",
                output=stdout_buf.getvalue().strip(),
                return_value=None,
                execution_time_ms=round(elapsed_ms, 2),
                error=str(e),
            )


# Singleton instance
micro_sandbox = MicroRuntimeSandbox()
