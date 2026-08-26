import warnings

from core.unified_learning import LearningEvent, LearningType, get_learning_engine


class FederatedLearningAgent:
    def __init__(self):
        self._real = get_learning_engine()
        warnings.warn(
            "FederatedLearningAgent is deprecated, use UnifiedLearningEngine", DeprecationWarning
        )

    async def aggregate_learnings(self, data):
        # Mapped to federated aggregation learning event
        event = LearningEvent(
            event_type=LearningType.FEDERATED_AGGREGATION,
            source="federated_agent",
            input_data="aggregate",
            output_data=str(data),
        )
        return await self._real.learn(event)
