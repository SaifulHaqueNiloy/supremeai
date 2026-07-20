"""
Tests for core/intent.py
"""

from __future__ import annotations

from core.intent import IntentClassifier


def test_intent_classifier_general():
    clf = IntentClassifier()
    intent = clf.classify("what is the capital of france?")
    assert intent.task_type.value == "general"
    assert intent.confidence >= 0.0


def test_intent_classifier_coding():
    clf = IntentClassifier()
    intent = clf.classify("write a python function to sort a list")
    assert intent.task_type.value == "coding"


def test_intent_classifier_admin():
    clf = IntentClassifier()
    intent = clf.classify("run admin shutdown command now")
    assert intent.task_type.value == "admin"


def test_intent_classifier_translation():
    clf = IntentClassifier()
    intent = clf.classify("translate this to bengali")
    assert intent.task_type.value == "translation"
