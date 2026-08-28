"""Tests for core.intent — pure keyword-based intent classification."""

from core.intent import Intent, IntentClassifier, TaskType


def test_classify_coding():
    intent = IntentClassifier().classify("Write a python function to debug the bug")
    assert intent.task_type == TaskType.coding
    assert intent.confidence > 0
    assert intent.requires_admin is False
    assert intent.requires_vision is False


def test_classify_translation():
    intent = IntentClassifier().classify("Please translate this to french")
    assert intent.task_type == TaskType.translation


def test_classify_sentiment():
    intent = IntentClassifier().classify("What is the sentiment, positive or negative?")
    assert intent.task_type == TaskType.sentiment


def test_classify_vision():
    intent = IntentClassifier().classify("Look at this image and screenshot")
    assert intent.task_type == TaskType.vision
    assert intent.requires_vision is True


def test_classify_reasoning():
    intent = IntentClassifier().classify("Prove this math logic and deduce a plan")
    assert intent.task_type == TaskType.reasoning


def test_classify_admin():
    intent = IntentClassifier().classify("Admin: shutdown and disable the kill switch")
    assert intent.task_type == TaskType.admin
    assert intent.requires_admin is True


def test_classify_general_fallback():
    intent = IntentClassifier().classify("How are you today?")
    assert intent.task_type == TaskType.general
    assert intent.confidence == 0.5


def test_classify_confidence_fraction():
    intent = IntentClassifier().classify("code code code debug api")
    assert intent.task_type == TaskType.coding
    # 4 coding matches out of 4 total -> confidence 1.0
    assert intent.confidence == 1.0
