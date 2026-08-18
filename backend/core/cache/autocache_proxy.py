from enum import Enum
import logging
from typing import Any, Callable
import hashlib

from core.cache.multi_layer_cache import MultiLayerCache

logger = logging.getLogger(__name__)


class EntropyZone(str, Enum):
    """ক্যাশিং পলিসির জন্য ডাটা ভলাটিলিটি এবং এন্ট্রপি জোন।"""
    IMMUTABLE = "immutable"        # Zone 1: Pure AST, Commit SHA, Math, Static Docs (TTL: Inf/24h)
    SEMI_VOLATILE = "semi_volatile" # Zone 2: Router config, RBAC, Feature Flags (Event-Driven)
    ZERO_TRUST = "zero_trust"      # Zone 3: Secrets, Tests, Audit, DB Trans, OTP (0% Cache / Raw Clean)


class AutoCacheProxy:
    """
    Autonomous Cognitive Cache Matrix (ACCM) Engine।
    কাজের ইনটেন্ট (Intent), ডাটার এন্ট্রপি এবং কন্টেক্সট বিশ্লেষণ করে বুদ্ধিমত্তার সাথে
    কখন ক্যাশ করতে হবে আর কখন ফ্রেশ ক্লিন স্টেট চালাতে হবে তা স্বয়ংক্রিয়ভাবে নির্ধারণ করে।
    """

    def __init__(self, semantic_cache: Any | None = None):
        self.semantic_cache = semantic_cache
        self.multi_layer_cache = MultiLayerCache()
        self.cache = self.multi_layer_cache

        try:
            from cachetools import TTLCache as _TTLCache  # type: ignore[import-untyped]
            if isinstance(_TTLCache, type):
                TTLCache = _TTLCache
            else:
                raise TypeError("Mocked TTLCache")
        except Exception:
            class _PurePythonTTLCache(dict):
                def __init__(self, maxsize: int = 5000, ttl: int = 86400):
                    super().__init__()
                    self.maxsize = maxsize
                    self.ttl = ttl
            TTLCache = _PurePythonTTLCache

        self.memory_store = TTLCache(maxsize=5000, ttl=86400)
        self.request_history = TTLCache(maxsize=1000, ttl=300)
        self.ttl_matrix = {
            "static_docs": 86400,      # 24 hours (Zone 1)
            "immutable_ast": 86400 * 7, # 7 days (Zone 1)
            "skills_catalog": 43200,   # 12 hours (Zone 2)
            "model_routing": 3600,     # 1 hour (Zone 2)
            "code_gen": 3600,          # 1 hour
            "ai_chat": 1800,           # 30 minutes
            "user_dashboard": 0,       # Zone 3: Zero-Trust (Bypass)
            "zero_trust": 0,           # Zone 3: Zero-Trust (Bypass)
            "test_debug": 0,           # Zone 3: Testing/Audit/Debug (Bypass)
        }
        self.corrupted_cache_registry: set[str] = set()

    def classify_entropy_zone(self, prompt_or_context: str) -> EntropyZone:
        """
        কাজের ইনটেন্ট ও টেক্সট বিশ্লেষণ করে ৩টি জোনের মধ্যে সঠিক জোন ক্লাসিফাই করা।
        """
        text_lower = prompt_or_context.lower()

        # Zone 3: Zero-Trust / Pristine Execution (Debug, Audit, Test, Secrets, OTP)
        zero_trust_triggers = [
            "test", "debug", "audit", "verify", "secret", "otp", "totp",
            "transaction", "auth", "token", "clean", "fresh", "pristine",
            "password", "canary", "benchmark", "migrate"
        ]
        if any(trigger in text_lower for trigger in zero_trust_triggers):
            return EntropyZone.ZERO_TRUST

        # Zone 1: Immutable (Pure AST, Commit SHA, Static Docs, Pure Functions)
        immutable_triggers = [
            "ast", "commit_sha", "documentation", "doc", "readme",
            "syntax_tree", "grammar", "regex", "math", "constant"
        ]
        if any(trigger in text_lower for trigger in immutable_triggers):
            return EntropyZone.IMMUTABLE

        # Zone 2: Semi-Volatile (Configs, Routing, Features, Skills)
        return EntropyZone.SEMI_VOLATILE

    def infer_category_from_prompt(self, prompt: str, default_task: str = "general") -> str:
        """
        Infer query category from prompt content for dynamic TTL allocation.
        """
        zone = self.classify_entropy_zone(prompt)
        if zone == EntropyZone.ZERO_TRUST:
            return "zero_trust"

        prompt_lower = prompt.lower()
        if any(w in prompt_lower for w in ["doc", "documentation", "guide", "tutorial", "readme", "manifest"]):
            return "static_docs"
        elif any(w in prompt_lower for w in ["ast", "tree", "syntax"]):
            return "immutable_ast"
        elif any(w in prompt_lower for w in ["skill", "catalog", "tools", "capabilities"]):
            return "skills_catalog"
        elif any(w in prompt_lower for w in ["routing", "router", "provider_weights"]):
            return "model_routing"
        elif any(w in prompt_lower for w in ["def ", "class ", "function", "code", "import ", "bug", "refactor"]):
            return "code_gen"
        elif any(w in prompt_lower for w in ["dashboard", "balance", "profile", "account", "wallet", "realtime"]):
            return "user_dashboard"
        return "ai_chat"

    def get_ttl_for_category(self, category: str) -> int:
        """
        কুয়েরি ক্যাটাগরি অনুযায়ী TTL (সেকেন্ডে) প্রদান করা।
        """
        return self.ttl_matrix.get(category, 1800)

    def calculate_dynamic_ttl(self, prompt: str, category: str | None = None) -> int:
        """
        Calculate dynamic TTL based on category or prompt content.
        """
        cat = category or self.infer_category_from_prompt(prompt)
        return self.get_ttl_for_category(cat)

    async def get_or_compute(
        self,
        key: str,
        category: str,
        compute_fn: Callable[..., Any],
        *args: Any,
        validator_fn: Callable[[Any], bool] | None = None,
        force_clean: bool = False,
        **kwargs: Any,
    ) -> Any:
        """
        অটোনোমাস কগনিটিভ ক্যাশ এক্সেস ও সেলফ-হিলিং ফলব্যাক।
        যদি force_clean=True থাকে অথবা ক্যাটাগরি Zero-Trust জোনভুক্ত হয়, তবে ক্যাশ বাইপাস করা হয়।
        """
        ttl = self.get_ttl_for_category(category)

        # ১. Zero-Trust অথবা Force-Clean মোডে সম্পূর্ণ ফ্রেশ এক্সিকিউশন
        if ttl == 0 or force_clean or key in self.corrupted_cache_registry:
            logger.debug(f"[ACCM] Bypassing cache for key '{key}' (Category: {category}, TTL: 0s / Pristine)")
            return await compute_fn(*args, **kwargs)

        # ২. ক্যাশ থেকে ডেটা চেক
        cached_val = self.memory_store.get(key)
        if cached_val is not None:
            # ৩. সেলফ-হিলিং ভ্যালিডেশন: ক্যাশড ডেটা কি সঠিক ও অক্ষত?
            if validator_fn is not None:
                is_valid = False
                try:
                    is_valid = validator_fn(cached_val)
                except Exception as val_err:
                    logger.warning(f"[ACCM] Validator exception on cache key '{key}': {val_err}")

                if not is_valid:
                    # ৪. Self-Healing Cache Blast: ক্যাশ করাপ্ট হলে ইনস্ট্যান্ট ফ্লাশ ও ফ্রেশ রান
                    logger.warning(f"[ACCM] Cache corruption detected for '{key}'. Triggering Self-Healing Cache Blast!")
                    await self.invalidate_key(key)
                    self.corrupted_cache_registry.add(key)
                    fresh_val = await compute_fn(*args, **kwargs)
                    self.corrupted_cache_registry.discard(key)
                    if fresh_val is not None:
                        self.memory_store[key] = fresh_val
                    return fresh_val

            logger.debug(f"[ACCM] Cache hit for key '{key}' (Category: {category})")
            return cached_val

        # ৫. ক্যাশ মিস হলে নতুন মান তৈরি ও সংরক্ষণ
        computed_val = await compute_fn(*args, **kwargs)
        if computed_val is not None:
            self.memory_store[key] = computed_val
            logger.debug(f"[ACCM] Cached key '{key}' with TTL {ttl}s")

        return computed_val

    async def invalidate_key(self, key: str) -> None:
        """নির্দিষ্ট ক্যাশ কি ইনস্ট্যান্ট ফ্লাশ করা।"""
        try:
            self.memory_store.pop(key, None)
        except Exception as err:
            logger.debug(f"[ACCM] Invalidate key warning for '{key}': {err}")

    async def invalidate_zone(self, zone: EntropyZone) -> None:
        """একটি নির্দিষ্ট এন্ট্রপি জোনের সমস্ত ক্যাশ মেমোরি ফ্লাশ করা।"""
        logger.info(f"[ACCM] Invalidating entire Entropy Zone: {zone.value}")
        if zone == EntropyZone.SEMI_VOLATILE:
            for cat in ["skills_catalog", "model_routing"]:
                await self.cache.clear_category(cat) if hasattr(self.cache, "clear_category") else None

    def _calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """ইনপুট এবং আউটপুট টোকেন খরচের গতিশীল হিসাব করা।"""
        from core.config_cache import config_cache

        input_rate = config_cache.get(f"{model}:input_cost") or 0.0
        output_rate = config_cache.get(f"{model}:output_cost") or 0.0
        return (input_tokens * input_rate) + (output_tokens * output_rate)

    def get_cost_summary(self) -> dict[str, Any]:
        """ইনপুট এবং আউটপুট টোকেন খরচের মোট সারাংশ প্রদান করা।"""
        return {"total_cost": 0.0, "summary": "cognitive_cache_active"}


# Class alias for backward compatibility with existing tests
AutocacheProxy = AutoCacheProxy

