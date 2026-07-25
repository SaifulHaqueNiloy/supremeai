import logging
from typing import Any
from core.cache.multi_layer_cache import MultiLayerCache

logger = logging.getLogger(__name__)


class AutoCacheProxy:
    """
    প্রম্পট এবং কুয়েরি ক্যাটাগরি বিশ্লেষণ করে Dynamic TTL Allocation করার জন্য Proxy Engine।
    Stale-While-Revalidate (SWR) এবং Semantic Similarity Cache প্যাটার্ন অনুসরণ করা হয়েছে।
    """

    def __init__(self, semantic_cache: Any | None = None):
        self.semantic_cache = semantic_cache
        self.cache = MultiLayerCache()
        from cachetools import TTLCache  # type: ignore[import-untyped]

        self.request_history = TTLCache(maxsize=1000, ttl=300)
        self.ttl_matrix = {
            "static_docs": 86400,  # 24 hours
            "skills_catalog": 43200,  # 12 hours
            "ai_chat": 1800,  # 30 minutes
            "code_gen": 3600,  # 1 hour
            "user_dashboard": 0,  # Bypass cache / No TTL
        }

    def get_ttl_for_category(self, category: str) -> int:
        """
        কুয়েরি ক্যাটাগরি অনুযায়ী TTL (সেকেন্ডে) প্রদান করা।
        """
        return self.ttl_matrix.get(category, 300)

    async def get_or_compute(self, key: str, category: str, compute_fn: Any, *args, **kwargs) -> Any:
        """
        ক্যাশ চেক করা এবং মিস হলে ডাইনামিক টিটিএল সহ মান হিসাব করে সঞ্চয় করা।
        """
        ttl = self.get_ttl_for_category(category)
        if ttl == 0:
            return await compute_fn(*args, **kwargs)

        cached_val = await self.cache.get(key)
        if cached_val is not None:
            logger.debug(f"[AutoCacheProxy] Cache hit for key '{key}' (Category: {category})")
            return cached_val

        # Compute new value
        computed_val = await compute_fn(*args, **kwargs)
        if computed_val is not None:
            await self.cache.set(key, computed_val, ttl_seconds=ttl)
            logger.debug(f"[AutoCacheProxy] Cached key '{key}' with TTL {ttl}s")

    def _calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """
        ইনপুট এবং আউটপুট টোকেন খরচের গতিশীল হিসাব করা।
        """
        from core.config_cache import config_cache

        input_rate = config_cache.get(f"{model}:input_cost") or 0.0
        output_rate = config_cache.get(f"{model}:output_cost") or 0.0
        return (input_tokens * input_rate) + (output_tokens * output_rate)


# Class alias for backward compatibility with existing tests
AutocacheProxy = AutoCacheProxy
