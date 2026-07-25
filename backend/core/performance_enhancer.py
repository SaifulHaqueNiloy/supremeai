"""Performance and Self-Healing Enhancement Module for SupremeAI 2.0
Enhances system performance, resilience, and autonomous healing capabilities.

বাংলা: সুপ্রিমএআই ২.০ এর পারফরম্যান্স এবং সেলফ-হিলিং ক্ষমতা উন্নত করে।
"""

import asyncio
import time
import traceback
from typing import Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import hashlib
import json

from loguru import logger

from core.config import settings
from core.health.self_healer import SelfHealerService, RemediationPipeline
from core.resilience.circuit_breaker import DynamicCircuitBreaker

from brain.model_registry import ModelRegistry


@dataclass
class PerformanceMetrics:
    """Stores performance metrics for system monitoring."""

    request_count: int = 0
    error_count: int = 0
    avg_response_time: float = 0.0
    peak_memory_usage: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class FailureHistoryEntry:
    """Represents a past failure for learning purposes."""

    timestamp: datetime
    error_type: str
    error_message: str
    context: dict[str, Any]
    resolution: str
    resolved: bool = False


class PerformanceOptimizer:
    """Main performance optimizer class implementing the core philosophy."""

    def __init__(self):
        self.metrics: dict[str, PerformanceMetrics] = {}
        self.failure_history: list[FailureHistoryEntry] = []
        self.dynamic_circuit_breakers: dict[str, DynamicCircuitBreaker] = {}
        self.model_registry = ModelRegistry()
        self.self_healer = None
        self.reminder_pipeline = None

        # Initialize self-healing components
        try:
            from utils.firestore_helpers import get_firestore_db

            db = get_firestore_db()
            if db:
                self.self_healer = SelfHealerService(db)
                self.reminder_pipeline = RemediationPipeline(db)
        except ImportError:
            logger.warning("Firestore not available, self-healing features limited")

        logger.info("✅ PerformanceOptimizer initialized with self-healing capabilities")

    def get_circuit_breaker(self, name: str) -> DynamicCircuitBreaker:
        """Get or create a dynamic circuit breaker for a specific operation."""
        if name not in self.dynamic_circuit_breakers:
            self.dynamic_circuit_breakers[name] = DynamicCircuitBreaker(
                name=name, failure_threshold=settings.circuit_breaker_failure_threshold, recovery_timeout=settings.circuit_breaker_cooldown_period
            )
        return self.dynamic_circuit_breakers[name]

    async def track_performance(self, operation: str, execution_time: float, success: bool = True) -> None:
        """Track performance metrics for an operation."""
        if operation not in self.metrics:
            self.metrics[operation] = PerformanceMetrics()

        metrics = self.metrics[operation]
        metrics.request_count += 1

        if not success:
            metrics.error_count += 1

        # Calculate moving average for response time
        total_time = metrics.avg_response_time * (metrics.request_count - 1) + execution_time
        metrics.avg_response_time = total_time / metrics.request_count

        # Update last updated time
        metrics.last_updated = datetime.now()

        # Log performance warnings
        if metrics.error_count > 0 and metrics.request_count > 0:
            error_rate = metrics.error_count / metrics.request_count
            if error_rate > 0.1:  # More than 10% errors
                logger.warning(f"⚠️ High error rate for {operation}: {error_rate:.2%}")

    async def optimize_model_selection(self, task_type: str, context: str = "") -> str:
        """Intelligently select the best model based on task type and context."""
        # Get models by tier and task requirements
        all_models = self.model_registry.MODELS

        # Filter models based on task type
        if task_type == "reasoning":
            suitable_models = [model_id for model_id, model_info in all_models.items() if "reasoning" in model_info.get("strengths", [])]
        elif task_type == "coding":
            suitable_models = [model_id for model_id, model_info in all_models.items() if "coding" in model_info.get("strengths", [])]
        else:
            # Default to general purpose models
            suitable_models = [
                model_id
                for model_id, model_info in all_models.items()
                if model_info.get("tier", 5) <= 2  # Tier 1 and 2 models
            ]

        if not suitable_models:
            # Fallback to any available model
            suitable_models = list(all_models.keys())

        # Select model based on availability and cost
        best_model = None
        best_score = float("-inf")

        for model_id in suitable_models:
            model_info = all_models[model_id]

            # Calculate score based on various factors
            score = 0

            # Tier weighting (higher tier = better quality)
            score += (10 - model_info.get("tier", 5)) * 10

            # Cost consideration (lower cost = higher score if quality is similar)
            cost_factor = 1 / (model_info.get("cost_input_per_million", 999999) + 1)
            score += cost_factor * 5

            # Context length consideration
            if model_info.get("context_length", 0) >= 100000:
                score += 5  # Bonus for large context

            # Check if API key is available
            provider = model_info.get("provider", "")
            api_key = self._get_api_key_for_provider(provider)
            if not api_key:
                score -= 100  # Heavy penalty for unavailable models

            if score > best_score:
                best_score = score
                best_model = model_id

        if best_model:
            logger.info(f"Selected optimal model '{best_model}' for task '{task_type}'")
            return best_model
        else:
            # Fallback to default model
            logger.warning("No optimal model found, falling back to default")
            return "gemini/gemini-2.5-flash"

    def _get_api_key_for_provider(self, provider: str) -> str:
        """Get API key for a specific provider from settings."""
        provider_keys = {
            "anthropic": settings.openrouter_api_key,
            "openai": settings.openai_api_key,
            "google": settings.gemini_api_key,
            "deepseek": settings.deepseek_api_key,
            "groq": settings.groq_api_key,
            "openrouter": settings.openrouter_api_key,
            "huggingface": settings.hf_api_key,
            "nvidia": settings.nvidia_api_key,
        }
        return provider_keys.get(provider, "")

    async def handle_failure(self, error_type: str, error_message: str, context: dict[str, Any]) -> None:
        """Handle system failures with self-healing capabilities."""
        # Record failure in history
        # বাংলা: FailureHistoryEntry-এ সকল required field পূরণ করা হলো (mypy fix)
        failure_entry = FailureHistoryEntry(
            timestamp=datetime.now(),
            error_type=error_type,
            error_message=error_message,
            context=context,
            resolution="pending",  # প্রাথমিক অবস্থায় resolution 'pending' — self-healer পরে আপডেট করবে
        )
        self.failure_history.append(failure_entry)

        # Keep only recent failures to prevent memory bloat
        if len(self.failure_history) > 100:
            self.failure_history = self.failure_history[-100:]

        logger.error(f"Failure recorded: {error_type} - {error_message}")

        # Trigger self-healing if possible
        if self.self_healer and self.reminder_pipeline:
            try:
                # Analyze the error and propose a fix
                error_signature = self._generate_error_signature(error_type, error_message, context)

                # Create a proposed fix based on error pattern
                proposed_fix = await self._generate_fix_proposal(error_type, error_message, context)

                # Submit the fix for remediation
                impact_score = self._calculate_impact_score(error_type)

                fix_id = await self.reminder_pipeline.submit(
                    tenant_id=context.get("tenant_id", "system"),
                    error_pattern=error_signature,
                    proposed_fix=proposed_fix,
                    impact_score=impact_score,
                    dependency_tree=context.get("dependency_tree", ["system"]),
                )

                logger.info(f"Submitted auto-fix for error '{error_type}', fix ID: {fix_id}")

            except Exception as e:
                logger.error(f"Failed to submit auto-fix: {e}")

    def _generate_error_signature(self, error_type: str, error_message: str, context: dict[str, Any]) -> str:
        """Generate a unique signature for the error pattern."""
        error_data = {
            "type": error_type,
            "message": error_message,
            "context_keys": sorted(context.keys()) if context else [],
        }
        error_json = json.dumps(error_data, sort_keys=True, default=str)
        return hashlib.sha256(error_json.encode()).hexdigest()[:16]

    async def _generate_fix_proposal(self, error_type: str, error_message: str, context: dict[str, Any]) -> str:
        """Generate a potential fix for the error."""
        # For demonstration, creating a simple fix proposal
        # In a real system, this would use more sophisticated AI reasoning
        fix_proposals = {
            "LLM_GATEWAY_TIMEOUT": "Increase timeout settings in config",
            "CIRCUIT_BREAKER_OPEN": "Wait for circuit to recover or investigate root cause",
            "RATE_LIMIT_EXCEEDED": "Implement retry logic with exponential backoff",
            "INVALID_API_KEY": "Verify API key configuration in environment",
            "CONNECTION_ERROR": "Check network connectivity and service availability",
        }

        proposal = fix_proposals.get(error_type, f"Manual investigation required for: {error_message}")

        return f"""
# Auto-generated fix proposal for: {error_type}
# Context: {context}

{proposal}

# Implementation suggestion:
# 1. Analyze the error pattern
# 2. Implement appropriate error handling
# 3. Consider circuit breaker adjustments
# 4. Verify configuration settings
"""

    def _calculate_impact_score(self, error_type: str) -> float:
        """Calculate impact score for the error (0.0 to 1.0)."""
        high_impact_errors = ["LLM_GATEWAY_TIMEOUT", "CONNECTION_ERROR", "INVALID_API_KEY", "DATABASE_CONNECTION_FAILED", "AUTHENTICATION_FAILED"]

        if error_type in high_impact_errors:
            return 0.8
        elif "PERFORMANCE" in error_type.upper():
            return 0.6
        else:
            return 0.3

    async def adaptive_load_balancing(self, task_type: str, workload: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Distribute workload intelligently based on current system capacity."""
        # Track current system load
        active_tasks = len([m for m in self.metrics.values() if m.last_updated > datetime.now() - timedelta(seconds=30)])

        # Adjust processing strategy based on load
        if active_tasks > 10:  # High load
            logger.warning("High system load detected, optimizing task distribution")
            # Reduce concurrent processing
            chunk_size = max(1, len(workload) // 5)  # Process in smaller chunks
        else:
            chunk_size = max(1, len(workload) // 2)  # Process in larger chunks

        # Distribute tasks in chunks
        processed_workload = []
        for i in range(0, len(workload), chunk_size):
            chunk = workload[i : i + chunk_size]
            processed_chunk = await self._process_workload_chunk(task_type, chunk)
            processed_workload.extend(processed_chunk)

            # Small delay between chunks to prevent overwhelming
            if active_tasks > 5:
                await asyncio.sleep(0.1)

        return processed_workload

    async def _process_workload_chunk(self, task_type: str, chunk: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Process a chunk of workload with appropriate error handling."""
        results = []

        for item in chunk:
            try:
                # Select optimal model for this specific task
                model = await self.optimize_model_selection(task_type)

                # Execute the task - for now we'll skip the direct LLM call to avoid circular import
                start_time = time.time()

                # Instead of calling LLM directly, we'll return a simulated result
                # This avoids importing llm_gateway which causes circular import
                result = {"success": True, "text": f"Simulated result for task: {item.get('prompt', 'default prompt')}", "model": model, "cost": 0.0}

                execution_time = time.time() - start_time
                await self.track_performance(f"task_{task_type}", execution_time, success=True)
                results.append(result)

            except Exception as e:
                execution_time = time.time() - start_time
                await self.track_performance(f"task_{task_type}", execution_time, success=False)

                # Handle the failure with self-healing
                await self.handle_failure(
                    error_type="TASK_EXECUTION_ERROR", error_message=str(e), context={"task_type": task_type, "item": item, "error": str(e)}
                )

                # Return error result
                results.append({"success": False, "error": str(e), "traceback": traceback.format_exc()})

        return results

    async def _execute_task_with_model(self, item: dict[str, Any], model: str) -> dict[str, Any]:
        """Execute a single task with the specified model."""
        # This method will be implemented to work with the LLM gateway
        # but we'll avoid direct import to prevent circular dependencies
        # For now, we return a simulated response
        return {"success": True, "text": f"Processed with model {model}: {item.get('prompt', 'default')}", "model": model, "cost": 0.0}


# Global instance of the performance optimizer
performance_optimizer = PerformanceOptimizer()


def get_performance_optimizer() -> PerformanceOptimizer:
    """Get the global performance optimizer instance."""
    return performance_optimizer
