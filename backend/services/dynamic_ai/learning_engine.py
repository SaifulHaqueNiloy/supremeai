import warnings

from core.unified_learning import LearningEvent, LearningType, get_learning_engine

# বাংলা মন্তব্য (ROOT-CAUSE FIX 2): কীওয়ার্ড-ভিত্তিক হালকা task detector।
# এখানে `.orchestrator` মডিউলের `TaskType`-কে import করা যাবে না (circular
# import: orchestrator.py -> .learning_engine -> orchestrator.py)। তাই এখানে
# শুধু ম্যাচিং স্ট্রিং ভ্যালু রিটার্ন করা হয় (orchestrator.TaskType একটি
# StrEnum, তাই এই প্লেইন স্ট্রিং-গুলোর সাথে `==`/dict-lookup স্বাভাবিকভাবেই
# কাজ করবে)।
_TASK_KEYWORDS: dict[str, tuple[str, ...]] = {
    "code_generation": ("code", "function", "python", "javascript", "script", "implement"),
    "code_review": ("review", "refactor", "bug", "debug", "fix"),
    "reasoning": ("why", "explain", "analyze", "reason", "prove", "calculate"),
    "creative_writing": ("story", "poem", "write a", "creative", "essay"),
    "summarization": ("summarize", "summary", "tl;dr", "shorten"),
}


class LearningEngine:
    def __init__(self, *_args, **_kwargs):
        # বাংলা মন্তব্য (ROOT-CAUSE FIX): এই ক্লাস এখন internally
        # UnifiedLearningEngine-এ delegate করে, তাই কোনো constructor arg
        # লাগে না। কিন্তু কলার (orchestrator.py) এখনো পুরনো
        # `LearningEngine(storage_path=...)` সিগনেচার দিয়ে কল করছিল, ফলে
        # `TypeError: LearningEngine() takes no arguments` হতো। backward
        # compatibility রাখতে *args/**kwargs নিয়ে ignore করা হলো (deprecated
        # ওয়ার্নিং তো এমনিতেই দেওয়া হয়)।
        self._real = get_learning_engine()
        warnings.warn("LearningEngine is deprecated, use UnifiedLearningEngine", DeprecationWarning)

    async def observe_and_learn(self, input_data, output_data, **kwargs):
        event = LearningEvent(
            event_type=LearningType.PATTERN_RECOGNITION,
            source="dynamic_ai",
            input_data=str(input_data),
            output_data=str(output_data),
            **kwargs,
        )
        return await self._real.learn(event)

    async def recall_similar(self, query):
        from core.unified_learning import LearningQuery

        results = await self._real.recall(LearningQuery(query_text=query))
        return [r.outcome for r in results]

    # ------------------------------------------------------------------
    # বাংলা মন্তব্য (ROOT-CAUSE FIX 2): নিচের ৪টি মেথড `orchestrator.py`-এর
    # `DynamicAIOrchestrator` কল করে (`load_learning_data`,
    # `detect_task_type`, `get_best_providers_for_task`,
    # `record_interaction`), কিন্তু এই ক্লাসে আগে ডিফাইন করা ছিল না।
    # যেহেতু `LLMRouter.route()` (প্রোডাকশনের মূল non-streaming এন্ট্রি
    # পয়েন্ট) সরাসরি `get_ai_orchestrator().generate()` কল করে, প্রতিটি
    # রিকোয়েস্টে `AttributeError` হতো (production-breaking, শুধু CI-এর
    # সমস্যা ছিল না)। এখানে হালকা-ওজনের বাস্তবায়ন যোগ করা হলো যা
    # UnifiedLearningEngine-কে crash না করিয়ে ব্যবহার করে।
    # ------------------------------------------------------------------

    async def load_learning_data(self) -> None:
        """No-op: UnifiedLearningEngine loads/persists its own state lazily."""
        return None

    def detect_task_type(self, prompt: str) -> str:
        """Lightweight keyword-based task classifier (see _TASK_KEYWORDS)."""
        lowered = (prompt or "").lower()
        for task_type, keywords in _TASK_KEYWORDS.items():
            if any(keyword in lowered for keyword in keywords):
                return task_type
        return "general"

    async def get_best_providers_for_task(
        self, prompt: str, available_providers: list, context: dict | None = None
    ) -> list[tuple[str, float]]:
        """Rank available providers for this task.

        No historical-performance model is wired up yet, so this falls back
        to registry order with a flat confidence score — callers only need
        a `(provider_id, confidence_score)` list and iterate in order, so
        this is a safe, non-crashing default rather than true learned
        ranking.
        """
        return [
            (getattr(p, "provider_id", p), 1.0) if not isinstance(p, str) else (p, 1.0)
            for p in available_providers
        ]

    def record_interaction(
        self,
        provider_id: str,
        task_type: str,
        success: bool,
        latency_ms: float = 0.0,
        estimated_cost: float = 0.0,
    ) -> None:
        """Fire-and-forget interaction logging via UnifiedLearningEngine.

        Callers (orchestrator.py) invoke this synchronously (not awaited),
        so this schedules the actual async learning write instead of
        blocking or requiring `await` at the call site.
        """
        import asyncio

        try:
            asyncio.create_task(
                self.observe_and_learn(
                    input_data={"provider_id": provider_id, "task_type": str(task_type)},
                    output_data={"success": success, "latency_ms": latency_ms},
                    metadata={"estimated_cost": estimated_cost},
                )
            )
        except RuntimeError as e:
            # No running event loop (e.g. called from sync test context) -
            # skip logging rather than crashing the caller.
            import logging

            logging.getLogger(__name__).warning(f"Silenced RuntimeError (no event loop): {e}")
