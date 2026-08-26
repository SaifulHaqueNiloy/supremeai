import warnings

from core.unified_learning import LearningEvent, LearningType, get_learning_engine


class LearningLoop:
    def __init__(self):
        self._real = get_learning_engine()
        warnings.warn("LearningLoop is deprecated, use UnifiedLearningEngine", DeprecationWarning)

    def compute_ewc_loss_penalty(
        self,
        cur_weights: dict,
        old_weights: dict,
        fisher: dict,
        ewc_lambda: float = 1.0,
    ) -> float:
        """Compute EWC (Elastic Weight Consolidation) loss penalty.

        EWC penalty = 0.5 * lambda * sum_i fisher_i * (cur_i - old_i)^2
        This discourages drift from previously learned weights.
        """
        penalty = 0.0
        for key in cur_weights:
            if key in old_weights and key in fisher:
                diff = cur_weights[key] - old_weights[key]
                penalty += 0.5 * ewc_lambda * fisher[key] * (diff ** 2)
        return penalty

    async def observe_and_learn(self, input_data, output_data, **kwargs):
        event = LearningEvent(
            event_type=LearningType.PATTERN_RECOGNITION,
            source="learning_loop",
            input_data=str(input_data),
            output_data=str(output_data),
            **kwargs,
        )
        return await self._real.learn(event)

    async def retrieve_insights(self, context):
        from core.unified_learning import LearningQuery

        return await self._real.recall(LearningQuery(query_text=str(context)))
