import warnings
from core.unified_learning import get_learning_engine, LearningEvent, LearningType

class LLMGatewayWithLearning:
    def __init__(self):
        self._real = get_learning_engine()
        warnings.warn("LLMGatewayWithLearning is deprecated, use UnifiedLearningEngine", DeprecationWarning)
        
    async def learn_completion(self, prompt, result, **kwargs):
        event = LearningEvent(
            event_type=LearningType.PATTERN_RECOGNITION,
            source="llm_gateway",
            input_data=str(prompt),
            output_data=str(result),
            **kwargs
        )
        return await self._real.learn(event)
        
    async def get_learned_context(self, prompt):
        from core.unified_learning import LearningQuery
        return await self._real.recall(LearningQuery(query_text=str(prompt)))
