"""Tests for Stagehand self-healing integration (flagged + Playwright fallback).

These tests verify the critical correctness property — when Stagehand is NOT
enabled (or its SDK is missing) every call transparently falls back to the
existing Playwright path. They do NOT require a real browser or network.
"""

from __future__ import annotations

import os
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

import main as scraper_main
from stagehand_agent import StagehandAgent, stagehand_enabled


def test_stagehand_disabled_by_default(monkeypatch):
    monkeypatch.delenv("ENABLE_STAGEHAND", raising=False)
    assert stagehand_enabled() is False


def test_stagehand_enabled_requires_sdk(monkeypatch):
    monkeypatch.setenv("ENABLE_STAGEHAND", "true")
    # SDK intentionally NOT installed in test env -> must report disabled
    assert stagehand_enabled() is False


@pytest.mark.asyncio
async def test_act_falls_back_to_playwright_when_disabled(monkeypatch):
    monkeypatch.delenv("ENABLE_STAGEHAND", raising=False)
    agent = StagehandAgent(headless=True)
    # Replace the real Playwright fallback with a stub (no browser needed)
    agent._fallback = AsyncMock()
    agent._fallback.navigate_and_interact = AsyncMock(
        return_value={"success": True, "engine": "playwright-fallback"}
    )
    result = await agent.act("https://example.com", "click submit")
    assert result["success"] is True
    assert result["engine"] == "playwright-fallback"
    agent._fallback.navigate_and_interact.assert_awaited_once()


@pytest.mark.asyncio
async def test_act_falls_back_when_enabled_but_sdk_missing(monkeypatch):
    monkeypatch.setenv("ENABLE_STAGEHAND", "true")  # reports enabled check skipped
    # Force stagehand_enabled() to True, but the SDK import will fail -> fallback
    monkeypatch.setattr("stagehand_agent.stagehand_enabled", lambda: True)
    agent = StagehandAgent(headless=True)
    agent._fallback = AsyncMock()
    agent._fallback.navigate_and_interact = AsyncMock(
        return_value={"success": True, "engine": "playwright-fallback"}
    )
    result = await agent.act("https://example.com", "click submit")
    assert result["success"] is True
    assert result["engine"] == "playwright-fallback"


def test_health_exposes_stagehand_flag(monkeypatch):
    monkeypatch.delenv("ENABLE_STAGEHAND", raising=False)
    client = TestClient(scraper_main.app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert "stagehand_enabled" in resp.json()
    assert resp.json()["stagehand_enabled"] is False


def test_browse_stagehand_endpoint_falls_back(monkeypatch):
    monkeypatch.delenv("ENABLE_STAGEHAND", raising=False)

    # Stub the agent used inside the route so no browser is launched
    wrong_help = None  # noqa: F841
    fake = AsyncMock()
    fake.act = AsyncMock(return_value={"success": True, "primitive": "act", "engine": "stub"})
    fake.extract = AsyncMock(return_value={"success": True, "primitive": "extract"})
    fake.observe = AsyncMock(return_value={"success": True, "primitive": "observe"})

    class FakeAgent:
        def __init__(self, *a, **k):
            pass

        async def act(self, url, instruction):
            return await fake.act(url, instruction)

        async def extract(self, url, instruction):
            return await fake.extract(url, instruction)

        async def observe(self, url, instruction=None):
            return await fake.observe(url, instruction)

    monkeypatch.setattr(scraper_main, "StagehandAgent", FakeAgent)
    client = TestClient(scraper_main.app)
    resp = client.post("/browse_stagehand", json={"url": "https://example.com", "primitive": "act"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["primitive"] == "act"
