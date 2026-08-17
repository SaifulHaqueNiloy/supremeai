"""browser-use inspired agentic browser-control adapter for SupremeAI.

browser-use (AI-agent browser automation) থেকে নেওয়া মূল ধারণা: প্রাকৃতিক ভাষার টাস্ক
দিয়ে এজেন্ট নিজে ব্রাউজার খুলে ক্লিক/টাইপ/ফর্ম/এক্সট্র্যাক্ট করতে পারে — মানুষের মতো।

এখানে browser-use-কে optional dependency হিসেবে ব্যবহার করা হয় (flag + dep থাকলে
আসল ইঞ্জিন, নাহলে একটি zero-cost deterministic fallback যেটা 'humanly testable'
structed result দেয়, যেমন internet_monitor/scout ড্রাইয়ের সময়)। Playwright ইতিমধ্যে
project-এ আছে বলে upstream-এর runtime খরচও নিয়ন্ত্রণে থাকে।
"""

from __future__ import annotations

from typing import Any

from loguru import logger

from integrations._flags import flag, import_available

_ENABLED_FLAG = "SUPREMEAI_BROWSER_USE_ENABLED"


class BrowserUseAdapter:
    """Agentic browser automation bridging optional browser-use with a safe fallback."""

    def __init__(self) -> None:
        self.enabled_flag = _ENABLED_FLAG
        self._engine = None
        if flag(_ENABLED_FLAG) and import_available("browser_use"):
            try:
                from browser_use import Agent  # type: ignore[import-not-found]

                self._engine = Agent  # class kept for lazy instantiation
                logger.info("BrowserUseAdapter: upstream browser agent available.")
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning(f"BrowserUseAdapter: upstream import failed: {exc}")
                self._engine = None
        else:
            logger.info(
                "BrowserUseAdapter: upstream disabled/absent, using fallback planner "
                f"(flag={flag(_ENABLED_FLAG)}, dep={import_available('browser_use')})."
            )

    @property
    def active(self) -> bool:
        return self._engine is not None

    def run_task(self, task: str, llm: Any = None, max_steps: int = 10) -> dict[str, Any]:
        """Execute a natural-language browser task; returns {status, result, engine}."""
        if self.active and self._engine is not None:
            try:
                agent = self._engine(task=task, llm=llm, max_steps=max_steps)
                result = agent.run()
                return {"status": "ok", "engine": "upstream", "result": result}
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning(f"BrowserUseAdapter: run failed: {exc}")
                return {"status": "error", "engine": "upstream", "error": str(exc)}

        # zero-cost fallback: deterministic task→action decomposition (plan only)
        return {
            "status": "ok",
            "engine": "fallback",
            "result": {"plan": f"browser-task: {task}", "steps_planned": max_steps},
            "note": "browser-use upstream disabled — plan returned without live browser.",
        }
