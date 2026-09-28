# backend/tools/ensemble_router.py
# SupremeAI 2.0 — Provider Selection Intelligence (PSI) Ensemble Router Facade
# ==============================================================================
# বাংলা মন্তব্য: এটি পুরানো PSI Ensemble Router-এর backward-compatible facade।
# সরাসরি ক্যানোনিকাল LLM Gateway (core.llm.llm_gateway) ব্যবহার করে রিকোয়েস্ট পরিচালনা করে।
# Rule 14 / Consolidation Invariant: ডুপ্লিকেট বাদ দিয়ে ক্যানোনিকাল গেটওয়েতে একীভূত করা।

from typing import Any

from core.llm.llm_gateway import get_llm_gateway
from core.logging_config import logger


class EnsembleRouter:
    """
    বাংলা মন্তব্য: প্রজেক্টের কোর এআই রউটিং ইঞ্জিন — PSI রুলস মেনে একাধিক
    এআই প্রভাইডারের মধ্যে অটো-সুইচিং ও ক্যানোনিকাল LLM Gateway ডেলিগেশন পরিচালনা করে।
    """

    def __init__(self) -> None:
        self.quota_exhausted: set[str] = set()

    async def route_and_vote(self, prompt: str, models: list[str] | None = None) -> dict[str, Any]:
        """
        বাংলা মন্তব্য: প্রম্পট গ্রহণ করে ক্যানোনিকাল LLM Gateway-এর মাধ্যমে রেসপন্স তৈরি করে।
        """
        try:
            gateway = get_llm_gateway()
            res = await gateway.async_generate(prompt)
            text = res.get("text", "") or res.get("content", "")
            provider = res.get("provider", "canonical_gateway")
            return {
                "status": "success",
                "best_model": str(provider),
                "best_response": text,
                "all_responses": {str(provider): text},
                "quota_exhausted_models": list(self.quota_exhausted),
            }
        except Exception as exc:
            logger.error(f"Ensemble routing exception: {exc}")
            return {
                "status": "error",
                "error": str(exc),
                "best_model": "fallback",
                "best_response": "Zero-cost local resilience fallback active.",
                "all_responses": {},
            }
