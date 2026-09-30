from typing import Any

from brain.economic_optimizer import BudgetContext, EconomicOptimizer
from core.config import settings


class CognitiveRouter:
    def __init__(self, economic_optimizer: EconomicOptimizer = None):
        self.economic_optimizer = economic_optimizer

    @staticmethod
    def _is_react_candidate(prompt: str) -> tuple[bool, str]:
        """বাংলা মন্তব্য: ReAct-প্রার্থী নির্ধারণ (deterministic, zero-cost)।

        সিদ্ধান্ত চুক্তি: multi-step/reasoning সিগন্যাল থাকলে কাজটি "complex" —
        একক direct LLM কল নয়, বরং ReAct লুপ (decide → execute → observe)
        প্রয়োজন। সাধারণ Q&A/greeting কখনোই প্রার্থী নয় (কস্ট-সেফ)।
        """
        lowered = (prompt or "").lower()
        words = lowered.split()
        if not lowered.strip():
            return False, "empty prompt"

        # বাংলা মন্তব্য: স্পষ্ট multi-step মার্কার — ব্যবহারকারী নিজেই ধাপ বলেছেন
        multi_step_markers = ("step by step", "multi-step", "step-by-step", "first ... then")
        if any(m in lowered for m in multi_step_markers):
            return True, "explicit multi-step instruction detected"

        # বাংলা মন্তব্য: reasoning/strategy কীওয়ার্ড — গভীর চিন্তার সংকেত
        # (brain/reasoning_orchestrator.plan()-এর সেমান্টিক ক্লাসের সাথে সামঞ্জস্যপূর্ণ)
        reasoning_keywords = (
            "prove",
            "math",
            "logic",
            "reason",
            "optimize",
            "strategy",
            "tradeoff",
            "trade-off",
            "plan a",
            "design a",
            "architect",
        )
        if any(k in lowered for k in reasoning_keywords):
            return True, "reasoning/strategy keyword detected"

        # বাংলা মন্তব্য: দৈর্ঘ্য-সিগন্যাল — দীর্ঘ নির্দেশ সাধারণত multi-part হয়
        if len(words) >= 14:
            return True, "long multi-part prompt"

        return False, "simple or direct request"

    async def route(
        self, prompt: str, user_id: str, budget_context: BudgetContext = None
    ) -> dict[str, Any]:
        # Simple heuristic to determine if decomposed
        if "analyze" in prompt.lower() and "implement" in prompt.lower():
            # Decompose
            return {
                "routing_mode": "decomposed",
                "task_graph": {
                    "task_count": 2,
                    "tasks": {
                        "task_1": {"type": "analysis", "provider": "google", "depends_on": []},
                        "task_2": {
                            "type": "implementation",
                            "provider": "groq",
                            "depends_on": ["task_1"],
                        },
                    },
                },
            }

        # Direct route (economic optimizer-চালিত বাজেট পথ — ReAct গেট এখানে নয়:
        # ব্যবহারকারী স্পষ্টভাবে বাজেট-সচেতন direct রাউটিং চেয়েছেন)
        if self.economic_optimizer and budget_context:
            decision = await self.economic_optimizer.optimize_route(
                prompt, "general", budget_context
            )
            return {
                "routing_mode": "direct",
                "provider": decision.provider,
                "model": decision.model,
            }

        default_model = getattr(settings, "model_general", "groq/llama-3.3-70b-versatile")
        if "/" in default_model:
            prov, mod = default_model.split("/", 1)
        else:
            prov, mod = "groq", default_model

        # বাংলা মন্তব্য: ReAct গেট — complex task, বাজেট-context বিহীন পথে
        # routing_mode "react" ফেরত দেয় (Issue #2705 Gap-F)। এটি কেবল রাউটিং
        # সিদ্ধান্ত: প্রকৃত decide_and_execute() নির্বাহ governed dispatcher/
        # পাইপলাইন-এ ঘটে (cognitive_pipeline_dispatcher) — রাউটার কখনো
        # টুল-নির্বাহ করে না (side-effect-free রাউটিং চুক্তি)।
        is_react, react_reason = self._is_react_candidate(prompt)
        if is_react:
            return {
                "routing_mode": "react",
                "provider": prov,
                "model": mod,
                "react": {
                    "enabled": True,
                    "complexity": "complex",
                    "reason": react_reason,
                    "max_iterations": 3,
                    "executor": "brain.reasoning_orchestrator.ReasoningOrchestrator.decide_and_execute",
                },
            }

        return {"routing_mode": "direct", "provider": prov, "model": mod}


_cognitive_router_instance = None


def get_cognitive_router(economic_optimizer: EconomicOptimizer = None) -> CognitiveRouter:
    global _cognitive_router_instance
    if _cognitive_router_instance is None:
        _cognitive_router_instance = CognitiveRouter(economic_optimizer)
    return _cognitive_router_instance
