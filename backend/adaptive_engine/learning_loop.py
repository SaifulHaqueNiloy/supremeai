import warnings
from core.unified_learning import get_learning_engine, LearningEvent, LearningType

class LearningLoop:
    def __init__(self):
        self._real = get_learning_engine()
        warnings.warn("LearningLoop is deprecated, use UnifiedLearningEngine", DeprecationWarning)
        
    async def observe_and_learn(self, input_data, output_data, **kwargs):
        event = LearningEvent(
            event_type=LearningType.PATTERN_RECOGNITION,
            source="learning_loop",
            input_data=str(input_data),
            output_data=str(output_data),
            **kwargs
        )
        return await self._real.learn(event)
        
    async def retrieve_insights(self, context):
        from core.unified_learning import LearningQuery
        return await self._real.recall(LearningQuery(query_text=str(context)))
