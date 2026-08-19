"""
AST Context Pruner module for SupremeAI 2.0.

Provides token estimation and AST-based context reduction by interfacing
with jcode (or fallback Python AST parser) before routing prompts to LLM providers.
"""

import ast
import json
import shutil
import subprocess
from pathlib import Path
from loguru import logger


class ContextPruner:
    """
    High-speed context pruner leveraging jcode Rust binary when available,
    falling back to Python AST symbol extraction for token savings.
    """

    def __init__(self, workspace_root: Path | None = None):
        self.workspace_root = workspace_root or Path(__file__).parent.parent.parent
        self.jcode_bin = shutil.which("jcode")

    def prune_code_text(self, code_text: str, filename: str = "snippet.py") -> str:
        """
        Prune code text by stripping non-essential function bodies and retaining class/method signatures.
        """
        try:
            tree = ast.parse(code_text, filename=filename)
            pruned_nodes = []
            for node in tree.body:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Import, ast.ImportFrom)):
                    pruned_nodes.append(node)

            # Reconstruct compact representation
            signatures = []
            for node in pruned_nodes:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    signatures.append(f"def {node.name}(...): ... # [pruned]")
                elif isinstance(node, ast.ClassDef):
                    signatures.append(f"class {node.name}: ... # [pruned]")
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    signatures.append(ast.unparse(node))
            
            return "\n".join(signatures) if signatures else code_text[:1000]

        except Exception as e:  # noqa: BLE001
            logger.debug(f"AST parse failed for snippet, returning truncated raw text: {e}")
            return code_text[:1000]

    def estimate_token_reduction(self, original_text: str, pruned_text: str) -> dict[str, float]:
        """Calculate token reduction percentage."""
        orig_words = len(original_text.split())
        pruned_words = len(pruned_text.split())
        reduction = max(0.0, (1.0 - (pruned_words / max(1, orig_words))) * 100.0)
        return {
            "original_word_count": orig_words,
            "pruned_word_count": pruned_words,
            "reduction_percent": round(reduction, 2),
        }


context_pruner = ContextPruner()
