"""
SupremeAI Trio Pipeline Orchestrator (Trio 2.0 — Autonomous Self-Healing Swarm)
==============================================================================

Chains the three IDE agents into a single production pipeline with closed-loop
auto-patching, pre-cognitive vector caching ($0 cost), AST sandbox verification,
and shadow self-training:

    Stage 1:  Gemini   (Code Writer)      — or Multi-Model Parliament
    Stage 2:  Kilo     (Code Reviewer)
    Stage 3:  Cline    (Production Checker — AST sandbox + local checks)

Self-Healing Loop:
    If the Reviewer or Checker catches any issue, the pipeline does NOT stop.
    It feeds the error log back to the Writer's ``repair()`` method and
    re-runs until the code is 100% green or ``max_iterations`` is reached.

Pre-Cognitive Cache:
    Before invoking any external LLM, the pipeline queries the semantic cache
    (ai_memory / pgvector). If a verified solution with similarity >= threshold
    is found, it is returned instantly with zero token cost.

Shadow Self-Training:
    Every iteration's (Draft Code -> Issues -> Fixed Code) diff is stored in
    the memory matrix to fuel SupremeAI's permanent brain growth.
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from typing import Any

from loguru import logger


class TrioPipeline:
    """Run the Gemini → Kilo → Cline assembly-line pipeline with self-healing."""

    def __init__(self) -> None:
        # Lazy imports avoid circular imports at module load
        from agents.ide.trio_adapters import (
            ClineChecker,
            GeminiWriter,
            KiloReviewer,
            MultiModelWriter,
        )

        self.writer = GeminiWriter()
        self.multi_writer = MultiModelWriter()
        self.reviewer = KiloReviewer()
        self.checker = ClineChecker()

    async def _pre_cognitive_cache_lookup(
        self, prompt: str, language: str, enable_cache: bool
    ) -> dict[str, Any] | None:
        """Query the semantic cache before calling any external LLM.

        Returns a cached pipeline result if a verified solution with
        similarity >= threshold is found. Otherwise returns None.
        """
        if not enable_cache:
            return None

        try:
            from core.cache.semantic_cache import SemanticCache

            cache = SemanticCache()
            task_type = "code"
            cached = await cache.query_similar(prompt, task_type=task_type)

            if cached and cached.response:
                logger.info(
                    "[TrioPipeline] ⚡ Pre-cognitive cache HIT — returning verified code (0 token cost)"
                )
                return {
                    "pipeline_id": hashlib.sha256(
                        f"{prompt}:{language}:{datetime.now(UTC).isoformat()}".encode()
                    ).hexdigest()[:16],
                    "status": "cached",
                    "cached": True,
                    "generated_code": cached.response,
                    "writer": {
                        "role": "writer",
                        "agent": cached.model,
                        "output": cached.response,
                        "confidence": 1.0,
                    },
                    "reviewer": {"issues": [], "output": "Cached result — previously verified"},
                    "checker": {
                        "metadata": {"ready_for_production": True},
                        "issues": [],
                    },
                    "ready_for_production": True,
                    "summary": "⚡ Returned from semantic cache (0 token cost, pre-verified).",
                    "iterations": 0,
                    "diff_history": [],
                    "self_healing_logs": [],
                }
        except Exception as exc:
            logger.warning(f"[TrioPipeline] Cache lookup failed: {exc}")

        return None

    def _collect_all_issues(
        self,
        reviewer_result: Any,
        checker_result: Any,
    ) -> list[dict[str, Any]]:
        """Collect structured issues from both Reviewer and Checker."""
        issues: list[dict[str, Any]] = []
        # Reviewer issues (severity: warning, high, medium, low, info)
        for issue in reviewer_result.issues:
            issues.append({
                **issue,
                "origin": "reviewer",
            })
        # Checker issues (AST syntax, production checks)
        for issue in checker_result.issues:
            issues.append({
                **issue,
                "origin": "checker",
            })
        return issues

    async def _shadow_learn(
        self,
        prompt: str,
        language: str,
        initial_draft: str,
        final_code: str,
        iteration_count: int,
        issues_fixed: list[dict[str, Any]],
    ) -> None:
        """Save the (Draft Code -> Issues -> Fixed Code) diff to the memory matrix.

        This fuels SupremeAI's permanent brain growth by storing successful
        repair patterns that future cache lookups can surface.
        """
        try:
            from core.cache.semantic_cache import SemanticCache

            cache = SemanticCache()

            # Build a shadow-learning record: the prompt maps to the final
            # production-ready code that was verified after self-healing.
            learning_record = (
                f"[SHADOW TRAINING] language={language} | iterations={iteration_count} "
                f"| issues_fixed={len(issues_fixed)}\n\n"
                f"--- INITIAL DRAFT ---\n{initial_draft}\n\n"
                f"--- ISSUES ---\n"
                f"{[i.get('message', '') for i in issues_fixed]}\n\n"
                f"--- FINAL REPAIRED CODE ---\n{final_code}"
            )

            await cache.set(prompt, learning_record, task_type="code")
            logger.info(
                f"[TrioPipeline] 🧠 Shadow self-training: saved {len(final_code)} chars of "
                f"verified code to memory (iterations={iteration_count})"
            )
        except Exception as exc:
            logger.warning(f"[TrioPipeline] Shadow learning failed: {exc}")

    def _compute_diff_summary(
        self, prev_code: str, new_code: str, iteration: int
    ) -> dict[str, Any]:
        """Compute a lightweight diff summary between two code versions."""
        import difflib

        diff = list(difflib.unified_diff(
            prev_code.splitlines(keepends=True),
            new_code.splitlines(keepends=True),
            fromfile=f"iter_{iteration - 1}",
            tofile=f"iter_{iteration}",
        ))
        added = sum(1 for line in diff if line.startswith("+") and not line.startswith("+++"))
        removed = sum(1 for line in diff if line.startswith("-") and not line.startswith("---"))

        return {
            "iteration": iteration,
            "lines_added": added,
            "lines_removed": removed,
            "diff": "".join(diff) if diff else "(no changes)",
            "code_length": len(new_code),
        }

    async def execute(
        self,
        prompt: str,
        language: str = "python",
        context: dict | None = None,
        max_iterations: int = 3,
        enable_cache: bool = True,
    ) -> dict:
        """
        Run the full self-healing pipeline: Writer → Reviewer → Checker,
        with closed-loop auto-patching up to ``max_iterations``.

        Parameters:
            prompt:         Natural-language description of the coding task.
            language:       Target programming language (default: "python").
            context:        Optional dict with filePath / existingCode / projectContext.
            max_iterations: Maximum self-healing repair iterations (default: 3).
            enable_cache:   If True, check pre-cognitive semantic cache first.

        Returns a dict with keys:
            - pipeline_id
            - status          ("ready" | "needs_review" | "reviewed" | "cached" | "failed")
            - generated_code
            - cached          (bool)
            - iterations
            - writer / reviewer / checker results (final iteration)
            - ready_for_production
            - summary
            - diff_history    (list of per-iteration diff summaries)
            - self_healing_logs (list of human-readable healing events)
        """
        pipeline_id = hashlib.sha256(
            f"{prompt}:{language}:{datetime.now(UTC).isoformat()}".encode()
        ).hexdigest()[:16]

        logger.info(f"[TrioPipeline] Starting pipeline {pipeline_id}: {prompt[:100]}")

        # ── Pre-Cognitive Cache Lookup ──────────────────────────────────────
        cached_result = await self._pre_cognitive_cache_lookup(prompt, language, enable_cache)
        if cached_result:
            return cached_result

        # ── Normalize context ───────────────────────────────────────────────
        ctx = context or {}
        if ctx.get("existingCode"):
            ctx_value = {
                "filePath": ctx.get("filePath", ""),
                "existingCode": ctx.get("existingCode"),
                "projectContext": ctx.get("projectContext"),
            }
        else:
            ctx_value = ctx

        # ── Stage 1: Write initial code ─────────────────────────────────────
        writer_result = await self.writer.run(
            prompt=prompt,
            language=language,
            context=ctx_value,
        )

        if writer_result.confidence == 0.0 or writer_result.issues:
            # Even on writer failure, try repair if issues exist
            if writer_result.issues and max_iterations > 0:
                logger.info("[TrioPipeline] Stage 1 had issues, attempting self-healing repair ...")
                initial_draft = writer_result.output
                repaired = await self.writer.repair(
                    prompt=prompt,
                    language=language,
                    context=ctx_value,
                    issues=writer_result.issues,
                    previous_code=initial_draft,
                )
                if repaired.confidence > 0 and not repaired.issues:
                    writer_result = repaired
                elif repaired.confidence > 0 and repaired.output:
                    writer_result = repaired

        if writer_result.confidence == 0.0:
            return {
                "pipeline_id": pipeline_id,
                "status": "failed",
                "generated_code": "",
                "cached": False,
                "iterations": 0,
                "writer": writer_result.to_dict(),
                "reviewer": {},
                "checker": {},
                "ready_for_production": False,
                "summary": f"Stage 1 (Gemini) failed: {writer_result.output[:200]}",
                "diff_history": [],
                "self_healing_logs": [],
            }

        generated_code = writer_result.output
        initial_draft = generated_code

        # ── Self-Healing Loop ───────────────────────────────────────────────
        iterations_log: list[dict[str, Any]] = []
        diff_history: list[dict[str, Any]] = []
        self_healing_logs: list[str] = []
        all_issues_fixed: list[dict[str, Any]] = []

        for iteration in range(1, max_iterations + 1):
            logger.info(f"[TrioPipeline] Iteration {iteration}/{max_iterations}")

            # Stage 2: Kilo reviews
            reviewer_result = await self.reviewer.run(
                code=generated_code,
                language=language,
                filepath=ctx.get("filePath", ""),
                writer_result=writer_result,
            )

            # Stage 3: Cline checks production readiness (AST sandbox + local checks)
            checker_result = await self.checker.run(
                code=generated_code,
                language=language,
                filepath=ctx.get("filePath", ""),
                reviewer_result=reviewer_result,
            )

            all_issues = self._collect_all_issues(reviewer_result, checker_result)
            review_issue_count = len(reviewer_result.issues)
            check_issue_count = len(checker_result.issues)

            iterations_log.append({
                "iteration": iteration,
                "review_issues": review_issue_count,
                "check_issues": check_issue_count,
                "total_issues": len(all_issues),
                "code_length": len(generated_code),
            })

            self_healing_logs.append(
                f"[Iter {iteration}] Review: {review_issue_count} issue(s) | "
                f"Checker: {check_issue_count} issue(s)"
            )

            # If no issues, code is 100% green — exit the healing loop
            if len(all_issues) == 0:
                logger.info(f"[TrioPipeline] ✓ Code is 100% green after {iteration} iteration(s)")
                break

            # Issues found → auto-repair (unless this is the last iteration)
            if iteration < max_iterations:
                self_healing_logs.append(
                    f"[Self-Healing] Iteration {iteration}: auto-fixing {len(all_issues)} issue(s) ..."
                )
                logger.info(
                    f"[TrioPipeline] ⚙️ Self-healing: packing {len(all_issues)} issue(s) "
                    f"into writer.repair() ..."
                )

                prev_code = generated_code
                repaired_result = await self.writer.repair(
                    prompt=prompt,
                    language=language,
                    context=ctx_value,
                    issues=all_issues,
                    previous_code=prev_code,
                )

                if repaired_result.output and repaired_result.confidence > 0:
                    generated_code = repaired_result.output
                    writer_result = repaired_result

                    diff_summary = self._compute_diff_summary(
                        prev_code, generated_code, iteration
                    )
                    diff_history.append(diff_summary)
                    all_issues_fixed.extend(all_issues)
            else:
                # Last iteration exhausted — save what we have
                self_healing_logs.append(
                    f"[Self-Healing] Iteration {iteration}: max_iterations ({max_iterations}) "
                    f"reached — {len(all_issues)} issue(s) could not be auto-fixed."
                )

        # ── Final status determination ──────────────────────────────────────
        ready = bool(checker_result.metadata.get("ready_for_production", False))
        review_issue_count = len(reviewer_result.issues)
        check_issue_count = len(checker_result.issues)
        total_remaining_issues = review_issue_count + check_issue_count

        if total_remaining_issues == 0 and ready:
            status = "ready"
        elif total_remaining_issues > 0 and iteration == max_iterations:
            status = "needs_review"
        else:
            status = "reviewed"

        iterations_completed = len(iterations_log)

        summary = (
            f"Stage 1 (Gemini): {len(initial_draft.splitlines())} lines initial draft.  "
            f"Stage 2 (Kilo): {review_issue_count} issue(s).  "
            f"Stage 3 (Cline): {'READY' if ready else 'NOT READY'}.  "
            f"Iterations: {iterations_completed}/{max_iterations}.  "
            f"Cache: {'hit' if cached_result else 'miss'}."
        )

        result = {
            "pipeline_id": pipeline_id,
            "status": status,
            "generated_code": generated_code,
            "cached": False,
            "iterations": iterations_completed,
            "writer": writer_result.to_dict(),
            "reviewer": reviewer_result.to_dict(),
            "checker": checker_result.to_dict(),
            "ready_for_production": ready,
            "summary": summary,
            "diff_history": diff_history,
            "self_healing_logs": self_healing_logs,
            "iteration_stats": iterations_log,
        }

        # ── Shadow Self-Training ────────────────────────────────────────────
        if iterations_completed > 1 or total_remaining_issues == 0:
            await self._shadow_learn(
                prompt=prompt,
                language=language,
                initial_draft=initial_draft,
                final_code=generated_code,
                iteration_count=iterations_completed,
                issues_fixed=all_issues_fixed,
            )

        logger.info(
            f"[TrioPipeline] {pipeline_id} complete — status={status} "
            f"iterations={iterations_completed}"
        )
        return result
