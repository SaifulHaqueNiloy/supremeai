import time
import pytest
from core.llm.prompt_cache_anchor import PromptCacheAnchor
from core.llm.free_tier_quota_balancer import FreeTierQuotaBalancer
from tools.mcp.speculative_warmer import SpeculativeWarmer
from tools.code.ast_context_slicer import ASTContextSlicer
from memory.recency_decay_filter import RecencyDecayFilter


def test_prompt_cache_anchor():
    system_prompt = "You are SupremeAI Principal Engineer."
    tools_schema = [{"name": "web_search", "description": "Searches the web"}]
    messages = [
        {"role": "user", "content": "How to optimize Python FastAPI?"}
    ]

    # Anthropic anchored structure
    anchored_claude = PromptCacheAnchor.anchor_messages(system_prompt, messages, tools_schema, provider="claude")
    assert len(anchored_claude) >= 2
    assert anchored_claude[0]["role"] == "system"
    assert "cache_control" in anchored_claude[0]["content"][0]
    assert anchored_claude[0]["content"][0]["cache_control"]["type"] == "ephemeral"

    # Savings calculation
    savings = PromptCacheAnchor.estimate_cache_savings(total_tokens=10000, cached_prefix_tokens=8000)
    assert savings["savings_ratio"] == 0.8
    assert savings["cost_saved_percentage"] == 72.0
    assert savings["estimated_ttft_reduction_ms"] > 0


def test_free_tier_quota_balancer():
    balancer = FreeTierQuotaBalancer()

    # Initial pick should be optimal
    opt_model = balancer.select_optimal_free_provider()
    assert opt_model in ("gemini/gemini-1.5-flash", "groq/llama-3.3-70b-versatile", "cerebras/llama3.1-70b", "openrouter/auto")

    # Simulate heavy usage on gemini_flash
    for _ in range(16):
        balancer.record_usage("gemini/gemini-1.5-flash", tokens=2500)

    load_gemini = balancer.get_provider_load("gemini_flash")
    assert load_gemini["is_throttled"] is True

    # Next selection should dynamically route to another unthrottled provider
    next_model = balancer.select_optimal_free_provider(preferred_provider="gemini_flash")
    assert next_model != "gemini/gemini-1.5-flash"


@pytest.mark.anyio
async def test_speculative_shadow_warmer():
    warmer = SpeculativeWarmer()
    warmed = False

    def mock_warmup():
        nonlocal warmed
        warmed = True
        return "prewarmed_env"

    warmer.register_warmup_hook("lint", mock_warmup)
    
    # Stream triggers 'lint'
    triggered = await warmer.check_and_speculate("Now checking syntax and linting code...")
    assert "lint" in triggered

    # Wait for shadow task
    await warmer.wait_idle()

    # Check consumed state
    result = warmer.consume_warmed_state("lint")
    assert result == "prewarmed_env"
    assert warmed is True


def test_ast_context_slicer():
    code_sample = '''import os

def calculate_sum(a, b):
    # Important function
    return a + b

def calculate_product(a, b):
    # Another function
    return a * b

class Calculator:
    def __init__(self):
        self.val = 0
'''
    # Slice around line 4 (inside calculate_sum)
    slice_result = ASTContextSlicer.slice_python_block(code_sample, target_line=4, context_padding=1)
    assert slice_result["is_full_file"] is False
    assert slice_result["target_node"] == "calculate_sum"
    assert "calculate_sum" in slice_result["sliced_code"]
    assert slice_result["token_reduction_pct"] > 0.0

    # Generic slice test
    gen_slice = ASTContextSlicer.slice_generic_block(code_sample, target_line=5, window_radius=2)
    assert "calculate_sum" in gen_slice["sliced_code"]


def test_recency_decay_filter():
    filter_engine = RecencyDecayFilter(decay_rate=0.1)
    now = time.time()

    # Fresh memory (0 days old) vs Old memory (100 days old)
    fresh_score = filter_engine.calculate_decayed_score(similarity_score=0.90, created_at_timestamp=now, now=now)
    old_score = filter_engine.calculate_decayed_score(similarity_score=0.90, created_at_timestamp=now - (100 * 86400), now=now)

    assert fresh_score > old_score
    assert fresh_score == 0.90
    assert old_score < 0.70

    # Deduplication test
    candidates = [
        {"content": "Fix JWT token bug", "similarity": 0.85, "created_at": now - 3600},
        {"content": "Fix JWT token bug", "similarity": 0.90, "created_at": now - 7200},  # duplicate text
        {"content": "Add Supabase connection pool", "similarity": 0.80, "created_at": now},
    ]

    filtered = filter_engine.filter_and_rank_memories(candidates, now=now, top_k=5)
    assert len(filtered) == 2  # duplicate removed
    assert filtered[0]["content"] == "Fix JWT token bug"
