"""Tests for core.human_behavior — Bezier path generation + (mocked) browser interactions."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.human_behavior import HumanBehaviorSimulators


def test_generate_bezier_points_count_and_endpoints():
    pts = HumanBehaviorSimulators._generate_bezier_points((0, 0), (100, 100), steps=20)
    assert len(pts) == 20
    assert pts[0] == (0, 0)
    assert pts[-1] == (100, 100)


def test_generate_bezier_points_midpoint_within_bounds():
    pts = HumanBehaviorSimulators._generate_bezier_points((0, 0), (10, 10), steps=5)
    for x, y in pts:
        assert 0 <= x <= 10
        assert 0 <= y <= 10


@pytest.mark.asyncio
async def test_natural_mouse_move_and_click():
    element = MagicMock()
    element.bounding_box = AsyncMock(return_value={"x": 10, "y": 20, "width": 100, "height": 50})
    page = MagicMock()
    page.wait_for_selector = AsyncMock(return_value=element)
    page.mouse.move = AsyncMock()
    page.mouse.click = AsyncMock()

    with patch("asyncio.sleep", new=AsyncMock()):
        await HumanBehaviorSimulators.natural_mouse_move_and_click(page, "#btn")

    page.wait_for_selector.assert_awaited_once_with("#btn", state="visible", timeout=10000)
    assert page.mouse.move.await_count > 0
    page.mouse.click.assert_awaited_once()


@pytest.mark.asyncio
async def test_natural_type():
    element = MagicMock()
    element.focus = AsyncMock()
    page = MagicMock()
    page.wait_for_selector = AsyncMock(return_value=element)
    page.keyboard.type = AsyncMock()

    with patch("asyncio.sleep", new=AsyncMock()):
        await HumanBehaviorSimulators.natural_type(page, "#field", "hi")

    assert page.keyboard.type.await_count == 2


@pytest.mark.asyncio
async def test_natural_mouse_move_raises_on_missing_box():
    element = MagicMock()
    element.bounding_box = AsyncMock(return_value=None)
    page = MagicMock()
    page.wait_for_selector = AsyncMock(return_value=element)

    with patch("asyncio.sleep", new=AsyncMock()):
        with pytest.raises(ValueError):
            await HumanBehaviorSimulators.natural_mouse_move_and_click(page, "#btn")
