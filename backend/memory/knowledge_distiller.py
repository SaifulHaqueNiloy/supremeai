"""
Knowledge Distillation & Model-Independence Engine
===================================================
Intercepts high-tier reasoning trajectories, solutions, and AST patches,
and distills them into compact, structured invariants in `ai_memory` (pgvector)
and `ContextGraphService`.
Includes AST Canonicalizer for structural invariant matching across naming differences.
Enables SupremeAI to progressively reduce reliance on 3rd-party LLMs ($0 Cost).
"""

from __future__ import annotations

import ast
import hashlib
import time
from typing import Any, Dict, List, Optional
from loguru import logger

from memory.context_graph_service import context_graph_service

BUILTIN_SAFE_NAMES = {
    "sum", "len", "max", "min", "range", "abs", "print", "self", "int", "float",
    "str", "bool", "dict", "list", "set", "tuple", "enumerate", "zip", "all", "any", "round"
}


class ASTCanonicalizer:
    """
    Normalizes source code into an invariant structural AST representation.
    """

    @classmethod
    def canonicalize_python(cls, code: str) -> tuple[str, str]:
        """
        Normalizes variable, function, and parameter names to canonical symbols,
        strips docstrings and comments, and returns (canonical_code, ast_fingerprint).
        """
        try:
            tree = ast.parse(code)
            name_map: dict[str, str] = {}
            var_counter = 0

            # 1. Normalize function/class names and remove docstrings
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    node.name = "canonical_fn"
                    if (
                        node.body
                        and isinstance(node.body[0], ast.Expr)
                        and isinstance(node.body[0].value, ast.Constant)
                        and isinstance(node.body[0].value.value, str)
                    ):
                        node.body.pop(0)
                elif isinstance(node, ast.ClassDef):
                    node.name = "CanonicalClass"
                    if (
                        node.body
                        and isinstance(node.body[0], ast.Expr)
                        and isinstance(node.body[0].value, ast.Constant)
                        and isinstance(node.body[0].value.value, str)
                    ):
                        node.body.pop(0)

            # 2. Map function parameters
            for node in ast.walk(tree):
                if isinstance(node, ast.arguments):
                    all_args = list(node.args) + getattr(node, "posonlyargs", []) + getattr(node, "kwonlyargs", [])
                    for arg in all_args:
                        if arg.arg not in name_map and not arg.arg.startswith("__") and arg.arg != "self":
                            name_map[arg.arg] = f"v_{var_counter}"
                            var_counter += 1
                        if arg.arg in name_map:
                            arg.arg = name_map[arg.arg]

            # 3. Map local variable assignments & usages
            for node in ast.walk(tree):
                if isinstance(node, ast.Name):
                    if node.id not in name_map and not node.id.startswith("__") and node.id not in BUILTIN_SAFE_NAMES:
                        name_map[node.id] = f"v_{var_counter}"
                        var_counter += 1
                    if node.id in name_map:
                        node.id = name_map[node.id]

            canonical_code = ast.unparse(tree).strip()
            fingerprint = hashlib.sha256(canonical_code.encode("utf-8")).hexdigest()[:16]
            return canonical_code, fingerprint

        except Exception:
            norm = "".join(code.split())
            fingerprint = hashlib.sha256(norm.encode("utf-8")).hexdigest()[:16]
            return norm, fingerprint


class KnowledgeDistiller:
    """
    Distills reasoning traces and code patterns into long-term vector/graph knowledge.
    """

    def __init__(self):
        self._distilled_cache: dict[str, dict[str, Any]] = {}
        self._ast_index: dict[str, str] = {}  # fingerprint -> distilled_id

    def distill_solution(
        self,
        task_intent: str,
        solution_code: str,
        reasoning_summary: str = "",
        model_source: str = "claude-3.7-sonnet",
        tenant_id: str = "default",
    ) -> dict[str, Any]:
        """
        Distills a working solution into an invariant pattern node and memory record.
        """
        canonical_ast, ast_fingerprint = ASTCanonicalizer.canonicalize_python(solution_code)
        pattern_hash = hashlib.sha256(f"{task_intent}:{ast_fingerprint}".encode("utf-8")).hexdigest()[:12]
        node_id = f"distilled_knowledge_{pattern_hash}"

        distilled_data = {
            "distilled_id": node_id,
            "intent": task_intent.strip(),
            "reasoning_summary": reasoning_summary.strip() or "Auto-distilled reasoning pattern.",
            "code_snippet": solution_code.strip()[:1000],
            "canonical_ast": canonical_ast[:1000],
            "ast_fingerprint": ast_fingerprint,
            "model_source": model_source,
            "tenant_id": tenant_id,
            "created_at": time.time(),
        }

        self._distilled_cache[node_id] = distilled_data
        self._ast_index[ast_fingerprint] = node_id

        # Sync to Context Graph as a Memory node
        try:
            context_graph_service.add_entity_node(
                node_id=node_id,
                node_type="Memory",
                label=f"Knowledge-{task_intent[:25]}",
                metadata=distilled_data,
                tenant_id=tenant_id,
            )
            logger.info(f"[KnowledgeDistiller] Distilled pattern '{node_id}' (AST: {ast_fingerprint}) synced to Context Graph.")
        except Exception as e:
            logger.debug(f"[KnowledgeDistiller] Graph sync skipped: {e}")

        return distilled_data

    def find_distilled_match(self, query: str, tenant_id: str = "default") -> Optional[dict[str, Any]]:
        """
        Fast textual/intent lookup of previously distilled solutions.
        """
        q_lower = query.lower()
        for item in self._distilled_cache.values():
            if item.get("tenant_id") == tenant_id:
                if q_lower in item["intent"].lower() or item["intent"].lower() in q_lower:
                    logger.debug(f"[KnowledgeDistiller] Text match for '{query}' -> '{item['distilled_id']}'")
                    return item
        return None

    def find_structural_ast_match(self, code_sample: str, tenant_id: str = "default") -> Optional[dict[str, Any]]:
        """
        Structural AST invariant lookup regardless of variable, function, or parameter naming differences.
        """
        _, fingerprint = ASTCanonicalizer.canonicalize_python(code_sample)
        distilled_id = self._ast_index.get(fingerprint)
        if distilled_id and distilled_id in self._distilled_cache:
            item = self._distilled_cache[distilled_id]
            if item.get("tenant_id") == tenant_id:
                logger.debug(f"[KnowledgeDistiller] AST invariant match ({fingerprint}) -> '{distilled_id}'")
                return item
        return None


# Singleton instance
knowledge_distiller = KnowledgeDistiller()
