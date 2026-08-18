from typing import Any

from loguru import logger

from core.cost_guard import cost_guard
from core.orchestration.cloud_sandbox_orchestrator import CloudSandboxOrchestrator
from tools.code.local_code_executor import LocalCodeExecutor


class TaskRouter:
    """বাংলা মন্তব্য: High Coupling ফিক্স — রাউটার এখন অবজেক্ট সৃষ্টি করবে না,
    শুধুমাত্র সঠিক এক্সিকিউটরে টাস্ক পাস করবে (Abstraction Layer).
    """

    def __init__(self) -> None:
        self.local_executor = LocalCodeExecutor()
        self.cloud_orchestrator = CloudSandboxOrchestrator()

    def process_requirement(self, task_description: str, max_cost: float = 0.01) -> dict[str, Any]:
        logger.info(f"Processing requirement: '{task_description}' max_cost={max_cost}")
        desc_lower = task_description.lower()
        prompt_len = len(task_description)

        token_budget = "small" if prompt_len <= 500 else "medium" if prompt_len <= 2000 else "large"
        modality = "text"
        if any(w in desc_lower for w in ["image", "picture", "photo", "vision"]):
            modality = "image"
        if any(w in desc_lower for w in ["video", "voice", "audio", "speech"]):
            modality = "multimodal"

        if "code" in desc_lower or "program" in desc_lower or "script" in desc_lower:
            task_type = "coding"
        elif (
            "image" in desc_lower
            or "picture" in desc_lower
            or "photo" in desc_lower
            or "draw" in desc_lower
            or "generate an image" in desc_lower
        ):
            task_type = "image_generation"
        elif "scrape" in desc_lower or "crawl" in desc_lower:
            task_type = "web_scraping_local"
        elif "system" in desc_lower or "terminal" in desc_lower:
            task_type = "system_control"
        else:
            task_type = "general"

        reasoning_depth = "low"
        if any(w in desc_lower for w in ["math", "reasoning", "analyze", "research"]):
            reasoning_depth = "high"
        elif modality != "text":
            reasoning_depth = "medium"

        return {
            "task_type": task_type,
            "cost_limit": float(max_cost),
            "token_budget": token_budget,
            "reasoning_depth": reasoning_depth,
            "modality": modality,
        }

    def analyze_and_route(self, task_description: str, max_cost: float = 0.01) -> dict[str, Any]:
        return self.process_requirement(task_description, max_cost=max_cost)

    async def route_and_dispatch(self, task_context: dict) -> dict:
        task_type = task_context.get("task_type", "local")
        cost_limit = float(task_context.get("cost_limit", task_context.get("cost", 0.0)))
        tenant_id = task_context.get("tenant_id", "anonymous")

        # ── CostGuard enforcement (Stabilization Gate gap) ──
        # Map the estimated cost to an execution tier and reject the task when the
        # tenant's tier quota is exhausted. CostGuard owns the fail-safe semantics
        # (free tier is always allowed; non-free tiers require Redis quota headroom).
        tier = "premium" if cost_limit > 0.5 else "economy" if cost_limit > 0.02 else "free"
        try:
            budget_ok = await cost_guard.validate_budget(tenant_id, tier)
        except Exception as exc:  # never let CostGuard crash a dispatch
            logger.warning(f"CostGuard budget check skipped due to error: {exc}")
            budget_ok = True
        if not budget_ok:
            logger.warning(
                f"💰 TaskRouter rejected task for tenant={tenant_id} tier={tier} "
                f"cost={cost_limit}: budget exceeded"
            )
            return {
                "status": "rejected",
                "reason": "budget_exceeded",
                "tenant_id": tenant_id,
                "tier": tier,
                "cost": cost_limit,
            }

        logger.info(f"🔀 TaskRouter directing context path to target tier: {task_type}")

        if task_type in ["web_scraping_local", "local", "coding"]:
            # ব্রাউজার বা লোকাল কোড রানারের দায়িত্ব লোকাল এক্সিকিউটরের ওপর অর্পণ
            code = task_context.get("code", "")
            result = await self.local_executor.execute_local_code(code)
            result["cost"] = cost_limit
            return result

        elif task_type == "heavy_cloud_sandbox":
            # ক্লাউড ম্যানেজমেন্টের ভার অর্কেস্ট্রেটরের ওপর অর্পণ
            config = task_context.get("config", {})
            result = await self.cloud_orchestrator.create_sandbox(config)
            return {"status": "success", "data": result, "cost": cost_limit}

        raise ValueError(f"Unknown execution route tier: {task_type}")
