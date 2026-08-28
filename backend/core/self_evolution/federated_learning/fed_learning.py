import warnings

from core.unified_learning import LearningEvent, LearningType, get_learning_engine


class FederatedLearningCoordinator:
    def __init__(self):
        self._real = get_learning_engine()
        warnings.warn(
            "FederatedLearningCoordinator is deprecated, use UnifiedLearningEngine",
            DeprecationWarning,
        )

    async def coordinate(self, peer_updates):
        event = LearningEvent(
            event_type=LearningType.FEDERATED_AGGREGATION,
            source="fed_learning_coordinator",
            input_data="peer_updates",
            output_data=str(peer_updates),
        )
        return await self._real.learn(event)
