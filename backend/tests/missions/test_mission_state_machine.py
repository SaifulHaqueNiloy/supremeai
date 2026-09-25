"""Tests for missions/state_machine.py — Mission lifecycle state machine."""
import pytest
from missions.state_machine import MissionState, assert_transition


class TestMissionStateMachine:
    """Mission states: PENDING → RUNNING → terminal."""

    def test_pending_to_running(self):
        assert_transition(MissionState.PENDING, MissionState.RUNNING)

    def test_running_to_succeeded(self):
        assert_transition(MissionState.RUNNING, MissionState.SUCCEEDED)

    def test_running_to_failed(self):
        assert_transition(MissionState.RUNNING, MissionState.FAILED)

    def test_running_to_cancelled(self):
        assert_transition(MissionState.RUNNING, MissionState.CANCELLED)

    def test_invalid_skip_running(self):
        with pytest.raises(Exception):
            assert_transition(MissionState.PENDING, MissionState.SUCCEEDED)

    def test_terminal_cannot_revert(self):
        with pytest.raises(Exception):
            assert_transition(MissionState.SUCCEEDED, MissionState.RUNNING)

    def test_failed_cannot_revert(self):
        with pytest.raises(Exception):
            assert_transition(MissionState.FAILED, MissionState.RUNNING)
