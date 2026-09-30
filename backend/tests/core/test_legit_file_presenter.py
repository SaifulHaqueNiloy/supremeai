"""Unit tests for LegitFilePresenter (Anti-Bot Legit Filename and Title Presentation).

বাংলা সারসংক্ষেপ:
------------------
অ্যান্টি-বট এড়ানোর জন্য রোবোটিক ফাইলনেম ও কনভারসেশন টাইটেলকে
মানুষের মতো বিশ্বাসযোগ্য (Legit) রূপে রূপান্তর যাচাই।
"""

from __future__ import annotations

from core.legit_file_presenter import LegitFilePresenter


def test_is_bot_like_name():
    """বাংলা মন্তব্য: বিভিন্ন রোবোটিক ফাইলনেম শনাক্তকরণ টেস্ট।"""
    # রোবোটিক নাম
    assert LegitFilePresenter.is_bot_like_name("tmp_12345.txt") is True
    assert LegitFilePresenter.is_bot_like_name("temp_script.py") is True
    assert LegitFilePresenter.is_bot_like_name("agent_dump.json") is True
    assert LegitFilePresenter.is_bot_like_name("scratch_notes.md") is True
    assert LegitFilePresenter.is_bot_like_name("task_99182.py") is True
    assert LegitFilePresenter.is_bot_like_name("4a8b1c2d-9876-4321-abcd-123456789abc.json") is True

    # মানুষের মতো স্বাভাবিক নাম
    assert LegitFilePresenter.is_bot_like_name("main.py") is False
    assert LegitFilePresenter.is_bot_like_name("DashboardView.tsx") is False
    assert LegitFilePresenter.is_bot_like_name("README.md") is False
    assert LegitFilePresenter.is_bot_like_name("package.json") is False
    assert LegitFilePresenter.is_bot_like_name("auth_service.py") is False


def test_legitimize_filename():
    """বাংলা মন্তব্য: রোবোটিক ফাইলনেমকে লিজিট ডেভেলপার ফাইলে রূপান্তর টেস্ট।"""
    # মানুষের নাম অপরিবর্তিত থাকবে
    assert LegitFilePresenter.legitimize_filename("main.py") == "main.py"
    assert LegitFilePresenter.legitimize_filename("index.css") == "index.css"

    # রোবোটিক নাম বদলে স্বাভাবিক এক্সটেনশনযুক্ত নাম আসবে
    legit_py = LegitFilePresenter.legitimize_filename("tmp_18923.py")
    assert legit_py.endswith(".py")
    assert not LegitFilePresenter.is_bot_like_name(legit_py)

    legit_json = LegitFilePresenter.legitimize_filename("agent_task_dump.json")
    assert legit_json.endswith(".json")
    assert not LegitFilePresenter.is_bot_like_name(legit_json)


def test_humanize_conversation_title():
    """বাংলা মন্তব্য: প্রম্পট থেকে মানুষের মতো স্বাভাবিক চ্যাট টাইটেল তৈরি টেস্ট।"""
    title = LegitFilePresenter.humanize_conversation_title(
        "Refactor our FastAPI authentication endpoints with JWT verification"
    )
    assert len(title) > 0
    assert "Refactor" in title
    assert not LegitFilePresenter.is_bot_like_name(title)

    # রোবোটিক শব্দ বাদ দেওয়া
    cleaned_title = LegitFilePresenter.humanize_conversation_title(
        "bot session task execute this query"
    )
    assert "bot" not in cleaned_title.lower()
    assert "session" not in cleaned_title.lower()
