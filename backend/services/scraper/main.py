"""
SupremeAI Scraper Microservice — FastAPI Application

Decoupled from the main backend. Exposes browser automation + web scraping
as a standalone HTTP API. Designed to run on Render free tier (port 8081).

Endpoints:
  GET  /health        — Liveness probe
  POST /scrape        — Fetch URL, return cleaned text + links (httpx)
  POST /browse        — Full Playwright browser automation (click, type, screenshot, etc.)
  POST /recipe        — Execute a multi-step automation recipe
"""

from __future__ import annotations

import os
import sys

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from browser_agent import BrowserAgent, BrowseRequest
from web_scraper import WebScraper

MAX_CONCURRENCY = int(os.getenv("SCRAPER_MAX_CONCURRENCY", "3"))
TIMEOUT_SECONDS = int(os.getenv("SCRAPER_TIMEOUT_SECONDS", "45"))

app = FastAPI(
    title="SupremeAI Scraper Microservice",
    description="Standalone browser automation and web scraping service",
    version="1.0.0",
)

_scraper = WebScraper()
_agent = BrowserAgent(headless=True)


class ScrapeRequest(BaseModel):
    url: str
    extraction_prompt: str | None = None


@app.get("/health")
async def health_check():
    try:
        import playwright.async_api as _pw
        playwright_ok = callable(getattr(_pw, "async_playwright", None))
    except ImportError:
        playwright_ok = False

    return {
        "status": "healthy",
        "service": "supremeai-scraper",
        "max_concurrency": MAX_CONCURRENCY,
        "timeout_seconds": TIMEOUT_SECONDS,
        "playwright_available": playwright_ok,
    }


@app.post("/scrape")
async def scrape(request: ScrapeRequest):
    if not request.url:
        raise HTTPException(status_code=400, detail="URL is required")
    result = _scraper.fetch_page(request.url)
    return result


@app.post("/browse")
async def browse(request: BrowseRequest):
    if not request.url:
        raise HTTPException(status_code=400, detail="URL is required")
    result = await _agent.navigate_and_interact(
        url=request.url,
        action=request.action or "fetch",
        selector=request.selector,
        text=request.text,
        wait_for=request.wait_for,
    )
    return result


class RecipeRequest(BaseModel):
    steps: list
    initial_url: str | None = None


@app.post("/recipe")
async def recipe(request: RecipeRequest):
    result = await _agent.execute_recipe(steps=request.steps, initial_url=request.initial_url)
    return result


if "pytest" in sys.modules:
    _APP_IMPORT_STRING = "main:app"
else:
    _APP_IMPORT_STRING = "main:app"

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8081"))
    uvicorn.run(_APP_IMPORT_STRING, host="0.0.0.0", port=port)
