import warnings

from core.unified_learning import LearningEvent, LearningType, get_learning_engine


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
