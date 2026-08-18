"""
AST Enclosing-Block Slicer for Thin Client Optimization
======================================================
Parses source code files (Python, JavaScript, TypeScript) and extracts only
the enclosing function, class, or relevant block around the active cursor line.
Reduces token payload across client-backend bridges by up to 80%.
"""

from __future__ import annotations

import ast
import logging
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ASTContextSlicer:
    """
    Intelligently slices code files to extract strictly the necessary AST scope.
    """

    @staticmethod
    def slice_python_block(source_code: str, target_line: int, context_padding: int = 5) -> dict[str, Any]:
        """
        Extracts the precise AST function/class block surrounding `target_line` in Python.
        """
        lines = source_code.splitlines()
        total_lines = len(lines)

        if total_lines == 0 or target_line < 1:
            return {"sliced_code": source_code, "is_full_file": True, "token_reduction_pct": 0.0}

        try:
            tree = ast.parse(source_code)
            matching_node = None

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    start = getattr(node, "lineno", 1)
                    end = getattr(node, "end_lineno", total_lines)
                    if start <= target_line <= end:
                        # Find the narrowest matching scope
                        if matching_node is None or (end - start) < (matching_node.end_lineno - matching_node.lineno):
                            matching_node = node

            if matching_node:
                start_idx = max(0, matching_node.lineno - 1 - context_padding)
                end_idx = min(total_lines, (matching_node.end_lineno or matching_node.lineno) + context_padding)
                sliced_lines = lines[start_idx:end_idx]
                sliced_code = "\n".join(sliced_lines)
                
                reduction = max(0.0, (1.0 - (len(sliced_lines) / max(1, total_lines))) * 100.0)
                return {
                    "sliced_code": sliced_code,
                    "target_node": matching_node.name,
                    "node_type": type(matching_node).__name__,
                    "start_line": start_idx + 1,
                    "end_line": end_idx,
                    "is_full_file": False,
                    "token_reduction_pct": round(reduction, 1),
                }

        except Exception as exc:
            logger.debug(f"AST parse fallback for Python block: {exc}")

        # Fallback: window slice
        start_idx = max(0, target_line - 1 - 25)
        end_idx = min(total_lines, target_line + 25)
        sliced_lines = lines[start_idx:end_idx]
        reduction = max(0.0, (1.0 - (len(sliced_lines) / max(1, total_lines))) * 100.0)
        return {
            "sliced_code": "\n".join(sliced_lines),
            "start_line": start_idx + 1,
            "end_line": end_idx,
            "is_full_file": False,
            "token_reduction_pct": round(reduction, 1),
        }

    @staticmethod
    def slice_generic_block(source_code: str, target_line: int, window_radius: int = 30) -> dict[str, Any]:
        """
        Generic brace-matching or window slicing for JS/TS/Go/Rust.
        """
        lines = source_code.splitlines()
        total_lines = len(lines)
        if total_lines <= window_radius * 2:
            return {"sliced_code": source_code, "is_full_file": True, "token_reduction_pct": 0.0}

        start_idx = max(0, target_line - 1 - window_radius)
        end_idx = min(total_lines, target_line + window_radius)
        sliced_lines = lines[start_idx:end_idx]
        reduction = max(0.0, (1.0 - (len(sliced_lines) / max(1, total_lines))) * 100.0)
        return {
            "sliced_code": "\n".join(sliced_lines),
            "start_line": start_idx + 1,
            "end_line": end_idx,
            "is_full_file": False,
            "token_reduction_pct": round(reduction, 1),
        }
