"""
Durable Workflow Engine with Compensation (Medusa v2 Pattern) for SupremeAI.
Provides transactional durability, step-by-step state tracking, and automatic
reverse compensation (Saga Rollback) when errors or failures occur.
"""

from __future__ import annotations

import asyncio
import inspect
import json
import sqlite3
import traceback
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Coroutine

from loguru import logger


class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    COMPENSATED = "compensated"
    COMPENSATION_FAILED = "compensation_failed"


@dataclass
class StepResult:
    step_name: str
    status: StepStatus
    output: Any = None
    error: str | None = None
    execution_time_ms: float = 0.0


@dataclass
class WorkflowStep:
    name: str
    action: Callable[..., Any | Coroutine[Any, Any, Any]]
    compensation: Callable[..., Any | Coroutine[Any, Any, Any]] | None = None
    required: bool = True
    retry_count: int = 1
    description: str = ""


class DurableWorkflowEngine:
    """
    Durable Workflow Engine implementing the Saga Pattern.
    Executes a sequence of steps. If any step fails, automatically executes
    the compensation actions of all completed steps in reverse order.
    """

    def __init__(self, db_path: str | Path = "checkpoints.db"):
        self.db_path = str(db_path)
        self._init_db()

    def _init_db(self) -> None:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS workflow_runs (
                        run_id TEXT PRIMARY KEY,
                        workflow_name TEXT NOT NULL,
                        status TEXT NOT NULL,
                        input_payload TEXT,
                        output_payload TEXT,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                    """
                )
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS workflow_step_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        run_id TEXT NOT NULL,
                        step_name TEXT NOT NULL,
                        status TEXT NOT NULL,
                        output TEXT,
                        error TEXT,
                        timestamp TEXT NOT NULL,
                        FOREIGN KEY (run_id) REFERENCES workflow_runs (run_id)
                    )
                    """
                )
                conn.commit()
        except Exception as exc:
            logger.warning(f"Could not initialize durable workflow db: {exc}")

    def _record_run_start(self, run_id: str, workflow_name: str, input_payload: dict[str, Any]) -> None:
        now = datetime.now(timezone.utc).isoformat()
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO workflow_runs (run_id, workflow_name, status, input_payload, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (run_id, workflow_name, "running", json.dumps(input_payload, default=str), now, now),
                )
                conn.commit()
        except Exception as exc:
            logger.warning(f"Failed to record workflow start: {exc}")

    def _record_step(self, run_id: str, step_name: str, status: StepStatus, output: Any = None, error: str | None = None) -> None:
        now = datetime.now(timezone.utc).isoformat()
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO workflow_step_logs (run_id, step_name, status, output, error, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (run_id, step_name, status.value, json.dumps(output, default=str) if output else None, error, now),
                )
                conn.commit()
        except Exception as exc:
            logger.warning(f"Failed to record step log: {exc}")

    def _record_run_end(self, run_id: str, status: str, output_payload: dict[str, Any]) -> None:
        now = datetime.now(timezone.utc).isoformat()
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    UPDATE workflow_runs
                    SET status = ?, output_payload = ?, updated_at = ?
                    WHERE run_id = ?
                    """,
                    (status, json.dumps(output_payload, default=str), now, run_id),
                )
                conn.commit()
        except Exception as exc:
            logger.warning(f"Failed to record workflow end: {exc}")

    async def _execute_callable(self, func: Callable[..., Any], context: dict[str, Any]) -> Any:
        if inspect.iscoroutinefunction(func):
            sig = inspect.signature(func)
            if len(sig.parameters) == 0:
                return await func()
            return await func(context)
        else:
            sig = inspect.signature(func)
            if len(sig.parameters) == 0:
                return func()
            return func(context)

    async def run_workflow(
        self,
        workflow_name: str,
        steps: list[WorkflowStep],
        initial_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        run_id = f"wf-{uuid.uuid4().hex[:12]}"
        context: dict[str, Any] = dict(initial_context or {})
        context["_run_id"] = run_id
        context["_workflow_name"] = workflow_name

        self._record_run_start(run_id, workflow_name, context)
        logger.info(f"Starting Durable Workflow [{workflow_name}] with Run ID: {run_id}")

        completed_steps: list[tuple[WorkflowStep, Any]] = []
        step_results: list[StepResult] = []
        failed_step_name: str | None = None
        failure_error: str | None = None

        for step in steps:
            step_success = False
            step_output = None
            step_error = None
            start_time = asyncio.get_event_loop().time()

            logger.info(f"Executing Workflow Step: {step.name}")
            self._record_step(run_id, step.name, StepStatus.RUNNING)

            for attempt in range(max(1, step.retry_count)):
                try:
                    step_output = await self._execute_callable(step.action, context)
                    step_success = True
                    break
                except Exception as exc:
                    step_error = f"{type(exc).__name__}: {exc}"
                    logger.warning(f"Step [{step.name}] failed attempt {attempt + 1}: {step_error}")

            duration_ms = (asyncio.get_event_loop().time() - start_time) * 1000.0

            if step_success:
                context[step.name] = step_output
                completed_steps.append((step, step_output))
                step_res = StepResult(step_name=step.name, status=StepStatus.COMPLETED, output=step_output, execution_time_ms=duration_ms)
                step_results.append(step_res)
                self._record_step(run_id, step.name, StepStatus.COMPLETED, output=step_output)
            else:
                step_res = StepResult(step_name=step.name, status=StepStatus.FAILED, error=step_error, execution_time_ms=duration_ms)
                step_results.append(step_res)
                self._record_step(run_id, step.name, StepStatus.FAILED, error=step_error)

                if step.required:
                    failed_step_name = step.name
                    failure_error = step_error
                    break

        # If a required step failed, trigger Compensation (Saga Rollback) in reverse order
        if failed_step_name:
            logger.error(f"Workflow [{workflow_name}] failed at [{failed_step_name}]. Initiating Saga Compensation Rollback...")
            compensation_logs: list[dict[str, Any]] = []

            for comp_step, comp_output in reversed(completed_steps):
                if comp_step.compensation:
                    logger.info(f"Compensating Step: {comp_step.name}")
                    comp_context = dict(context)
                    comp_context["_step_output"] = comp_output
                    try:
                        await self._execute_callable(comp_step.compensation, comp_context)
                        self._record_step(run_id, f"compensate_{comp_step.name}", StepStatus.COMPENSATED)
                        compensation_logs.append({"step": comp_step.name, "status": "compensated"})
                    except Exception as c_exc:
                        err_msg = f"{type(c_exc).__name__}: {c_exc}"
                        logger.error(f"Compensation for step [{comp_step.name}] failed: {err_msg}")
                        self._record_step(run_id, f"compensate_{comp_step.name}", StepStatus.COMPENSATION_FAILED, error=err_msg)
                        compensation_logs.append({"step": comp_step.name, "status": "compensation_failed", "error": err_msg})

            result_summary = {
                "run_id": run_id,
                "workflow_name": workflow_name,
                "success": False,
                "failed_step": failed_step_name,
                "error": failure_error,
                "step_results": [r.__dict__ for r in step_results],
                "compensated": True,
                "compensation_logs": compensation_logs,
                "context": context,
            }
            self._record_run_end(run_id, "failed_compensated", result_summary)
            return result_summary

        result_summary = {
            "run_id": run_id,
            "workflow_name": workflow_name,
            "success": True,
            "step_results": [r.__dict__ for r in step_results],
            "compensated": False,
            "context": context,
        }
        self._record_run_end(run_id, "completed", result_summary)
        return result_summary
