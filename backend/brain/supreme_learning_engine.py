import warnings

from core.unified_learning import LearningEvent, LearningQuery, LearningType, get_learning_engine


class SupremeLearningEngine:
    def __init__(self):
        self._real = get_learning_engine()
        warnings.warn(
            "SupremeLearningEngine is deprecated, use UnifiedLearningEngine", DeprecationWarning
        )

    async def process_chat_message(self, query, user_id=None, **kwargs):
        context = await self._real.recall(
            LearningQuery(query_text=query, user_id=user_id, max_results=5)
        )
        if context:
            best = context[0]
            return {
                "response": best.outcome,
                "confidence": best.confidence,
                "was_self_sufficient": best.confidence > 0.7,
            }
        return {"response": None, "confidence": 0, "was_self_sufficient": False}

    async def learn_from_chat_response(self, conversation, response, **kwargs):
        if isinstance(conversation, list):
            prompt = conversation[-1].get("content", "") if conversation else ""
        else:
            prompt = str(conversation)
        return await self._real.learn_from_chat(prompt, response, **kwargs)
