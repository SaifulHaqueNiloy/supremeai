"""
Unit Tests for PromptEnhancementEngine (প্রম্পট উন্নয়ন ও স্টেলথ টেস্ট)
"""

import pytest

from backend.core.prompt_enhancement_engine import (
    EnhancementContext,
    EnhancementMode,
    PromptEnhancementEngine,
    default_enhancer,
)


def test_stealth_chat_strips_meta_leaks_and_keeps_direct_flow():
    """
    বাংলা মন্তব্য: বাইরের প্রম্পট জেনারেটরের মেটা-লাইন ('Copy this to your AI...') মুছে খাঁটি হিউম্যান প্রশ্ন রাখা।
    """
    engine = PromptEnhancementEngine(rng_seed=42)
    raw_prompt = (
        "Copy this prompt to your desired AI's chat:\n"
        "Write a fastapi middleware to log requests without latency."
    )
    result = engine.enhance(raw_prompt, mode=EnhancementMode.STEALTH_CHAT)

    assert result.original_prompt == raw_prompt
    assert "copy this" not in result.enhanced_prompt.lower()
    assert result.enhanced_prompt == "Write a fastapi middleware to log requests without latency."
    assert "stripped_meta_generator_watermarks" in result.applied_tricks
    assert "organic_human_direct_flow" in result.applied_tricks


def test_stealth_chat_strips_robotic_patterns():
    """
    বাংলা মন্তব্য: রোবটিক প্রিফিক্স স্বয়ংক্রিয়ভাবে ক্লিন করে কিনা যাচাই।
    """
    engine = PromptEnhancementEngine(rng_seed=123)
    robotic_prompt = (
        "You are an expert software engineer.\n"
        "Your task is to: fix the redis connection pool issue."
    )
    result = engine.enhance(robotic_prompt, mode=EnhancementMode.STEALTH_CHAT)

    assert "stripped_robotic_prefix" in result.applied_tricks
    assert "You are an expert" not in result.enhanced_prompt
    assert "Your task is to:" not in result.enhanced_prompt
    assert "fix the redis connection pool issue." in result.enhanced_prompt


def test_ui_sparkle_enhancement_with_context():
    """
    বাংলা মন্তব্য: UI-এর বাটন ক্লিক মোডে ফাইল এবং সিলেক্টেড কোড কনটেক্সট যুক্ত হয় কিনা।
    """
    engine = PromptEnhancementEngine()
    context = EnhancementContext(
        current_file_path="backend/core/cache.py",
        selected_code="def get_cache(): pass",
        language="python",
    )
    result = engine.enhance(
        "Optimize this function", mode=EnhancementMode.ENHANCE_UI_CLICK, context=context
    )

    assert "backend/core/cache.py" in result.enhanced_prompt
    assert "def get_cache(): pass" in result.enhanced_prompt
    assert "python" in result.enhanced_prompt
    assert "sparkle_button_enrichment" in result.applied_tricks


def test_dev_api_mode():
    """
    বাংলা মন্তব্য: ডেভেলপার এপিআই মোড প্রম্পট ফরম্যাট ঠিক রাখে কিনা।
    """
    engine = PromptEnhancementEngine()
    context = EnhancementContext(user_intent="refactor")
    result = engine.enhance("Make this async", mode=EnhancementMode.DEV_API, context=context)

    assert "[Intent: refactor]" in result.enhanced_prompt
    assert "Make this async" in result.enhanced_prompt


def test_empty_prompt():
    """
    বাংলা মন্তব্য: ফাঁকা প্রম্পট দিলে ক্র্যাশ না করে নিরাপদে রিটার্ন করে কিনা।
    """
    result = default_enhancer.enhance("   ", mode=EnhancementMode.STEALTH_CHAT)
    assert result.enhanced_prompt == "   "
    assert "empty_prompt_noop" in result.applied_tricks


def test_prompt_enhance_api_endpoint():
    """
    বাংলা মন্তব্য: FastAPI রাউট /v1/prompt/enhance ঠিকমতো কাজ করে কিনা যাচাই।
    """
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from backend.api.routes.web_ai_proxy import router

    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    response = client.post(
        "/v1/prompt/enhance",
        json={
            "prompt": "Fix memory leak in websocket loop",
            "mode": "stealth_chat",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["original_prompt"] == "Fix memory leak in websocket loop"
    assert "organic_human_direct_flow" in data["applied_tricks"]
    assert data["enhanced_prompt"] == "Fix memory leak in websocket loop"


def test_account_session_thread_lifecycle():
    """
    বাংলা সারসংক্ষেপ:
    ------------------
    অ্যাকাউন্ট থ্রেড লাইফসাইকেল যাচাই:
    - প্রথম ৬টি টার্নে একই থ্রেড আইডি থাকবে (স্প্যামিং বন্ধ)
    - ৭ম টার্নে নতুন থ্রেড আইডিতে সুইচ করবে (হিস্ট্রি ব্লোট বন্ধ)
    """
    from backend.core.web_ai_session_bridge import AccountSession

    acc = AccountSession(
        service="claude",
        account_id="claude-acc-1",
        token="tok_123",
        max_thread_turns=6,
    )

    # টার্ন ১: নতুন থ্রেড শুরু
    tid1, is_new1 = acc.get_or_rotate_thread_id()
    assert is_new1 is True
    assert tid1 is not None

    # টার্ন ২ থেকে ৬: একই থ্রেড রিইউজ হবে
    for turn in range(2, 7):
        tid, is_new = acc.get_or_rotate_thread_id()
        assert is_new is False
        assert tid == tid1
        assert acc.thread_turn_count == turn

    # টার্ন ৭: ম্যাক্স টার্ন এক্সিড হওয়ায় নতুন থ্রেড রোটেশন
    tid7, is_new7 = acc.get_or_rotate_thread_id()
    assert is_new7 is True
    assert tid7 != tid1
    assert acc.thread_turn_count == 1


@pytest.mark.asyncio
async def test_account_concurrency_lock():
    """
    বাংলা সারসংক্ষেপ:
    ------------------
    পার-অ্যাকাউন্ট কনকারেন্সি লক যাচাই:
    একই অ্যাকাউন্টে সমান্তরালে ১টির বেশি কাজ যেতে পারবে না।
    """
    from backend.core.web_ai_session_bridge import AccountSession

    acc = AccountSession(service="claude", account_id="acc-test", token="tok")

    assert not acc._lock.locked()

    async with acc._lock:
        assert acc._lock.locked()

    assert not acc._lock.locked()
