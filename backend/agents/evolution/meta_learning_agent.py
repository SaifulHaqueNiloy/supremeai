import warnings
from core.unified_learning import get_learning_engine, LearningEvent, LearningType

class MetaLearningAgent:
    def __init__(self):
        self._real = get_learning_engine()
        warnings.warn("MetaLearningAgent is deprecated, use UnifiedLearningEngine", DeprecationWarning)
        
    async def optimize_strategy(self, current_strategy, feedback):
        event = LearningEvent(
            event_type=LearningType.PERFORMANCE_OPTIMIZATION,
            source="meta_learning_agent",
            input_data=str(current_strategy),
            output_data=str(feedback)
        )
        return await self._real.learn(event)
