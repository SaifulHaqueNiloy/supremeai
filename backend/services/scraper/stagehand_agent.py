"""
Stagehand self-healing browser agent for the scraper microservice.

বাংলা মন্তব্য: Stagehand (Browserbase) accessibility-tree ভিত্তিক ৩টি অ্যাটমিক
প্রিমিটিভ দেয় — act / extract / observe — যা CSS class বা ID বদলালেও নিজে থেকে
সেলফ-হিলিং ক্লিক/ফর্ম ফিল করে (brittle Selenium/Playwright স্ক্রিপ্টের বিপরীত)।

এই মডিউল fully optional + flagged:
  - ENABLE_STAGEHAND env False থাকলে বা stagehand প্যাকেজ না থাকলে সব কল
    বিদ্যমান Playwright BrowserAgent-এ graceful fallback করে।
  - Stagehand cloud (Browserbase) প্রয়োজন হলে STAGEHAND_API_KEY + STAGEHAND_ENV
    env দিতে হয়; না থাকলে LOCAL Playwright mode-এ চলে (zero-cost)।
"""

from __future__ import annotations

import os
from typing import Any

from loguru import logger

from security import is_safe_url
from web_scraper import WebScraper


def stagehand_enabled() -> bool:
    """True only when explicitly enabled AND the SDK is importable."""
    if os.getenv("ENABLE_STAGEHAND", "false").lower() not in ("1", "true", "yes"):
        return False
    try:
        import stagehand  # noqa: F401

        return True
    except Exception as exc:  # noqa: BLE001 # pragma: no cover - optional dependency
        logger.warning(f"Stagehand enabled but SDK unavailable ({exc}); falling back to Playwright.")
        return False


class StagehandAgent:
    """Self-healing browser primitives with Playwright fallback."""

    def __init__(self, headless: bool = True):
        self.headless = headless
        self.scraper = WebScraper()
        # Lazily import the Playwright agent only when needed for fallback.
        from browser_agent import BrowserAgent

        self._fallback = BrowserAgent(headless=headless)

    async def act(self, url: str, instruction: str) -> dict[str, Any]:
        """Perform a natural-language action (click submit, fill form, ...) self-healing."""
        if not is_safe_url(url):
            return {"success": False, "error": "SSRF check failed: Unauthorized internal access", "url": url}
        if not stagehand_enabled():
            return await self._fallback.navigate_and_interact(url=url, action="fetch")
        try:
            from stagehand import Stagehand

            config = self._build_config()
            async with Stagehand(config=config) as stagehand:
                page = stagehand.page
                await page.goto(url, wait_until="domcontentloaded")
                result = await page.act(instruction)
                return {
                    "success": True,
                    "primitive": "act",
                    "url": url,
                    "instruction": instruction,
                    "result": str(result),
                    "engine": "stagehand",
                }
        except Exception as exc:  # noqa: BLE001
            logger.error(f"Stagehand act failed, falling back: {exc}")
            return await self._fallback.navigate_and_interact(url=url, action="fetch")

    async def extract(self, url: str, instruction: str) -> dict[str, Any]:
        """Extract structured data (e.g. 'pricing table as JSON') via the accessibility tree."""
        if not is_safe_url(url):
            return {"success": False, "error": "SSRF check failed: Unauthorized internal access", "url": url}
        if not stagehand_enabled():
            return self.scraper.fetch_page(url)
        try:
            from stagehand import Stagehand

            config = self._build_config()
            async with Stagehand(config=config) as stagehand:
                page = stagehand.page
                await page.goto(url, wait_until="domcontentloaded")
                data = await page.extract(instruction)
                return {
                    "success": True,
                    "primitive": "extract",
                    "url": url,
                    "instruction": instruction,
                    "data": data,
                    "engine": "stagehand",
                }
        except Exception as exc:  # noqa: BLE001
            logger.error(f"Stagehand extract failed, falling back: {exc}")
            return self.scraper.fetch_page(url)

    async def observe(self, url: str, instruction: str | None = None) -> dict[str, Any]:
        """Observe what is visible on the screen (self-healing element discovery)."""
        if not is_safe_url(url):
            return {"success": False, "error": "SSRF check failed: Unauthorized internal access", "url": url}
        if not stagehand_enabled():
            return self.scraper.fetch_page(url)
        try:
            from stagehand import Stagehand

            config = self._build_config()
            async with Stagehand(config=config) as stagehand:
                page = stagehand.page
                await page.goto(url, wait_until="domcontentloaded")
                obs = await page.observe(instruction or "What is visible on the screen?")
                return {
                    "success": True,
                    "primitive": "observe",
                    "url": url,
                    "observation": str(obs),
                    "engine": "stagehand",
                }
        except Exception as exc:  # noqa: BLE001
            logger.error(f"Stagehand observe failed, falling back: {exc}")
            return self.scraper.fetch_page(url)

    @staticmethod
    def _build_config() -> dict[str, Any]:
        """Stagehand config: cloud if API key present, else LOCAL Playwright (zero-cost)."""
        api_key = os.getenv("STAGEHAND_API_KEY")
        if api_key:
            return {
                "env": os.getenv("STAGEHAND_ENV", "BROWSERBASE"),
                "api_key": api_key,
                "model": os.getenv("STAGEHAND_MODEL", "claude-sonnet-4"),
                "headless": True,
            }
        return {"env": "LOCAL", "model": "local", "headless": True}
