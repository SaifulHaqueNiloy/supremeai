"""#1833 — advertised-vs-actual API contract tests.

বাংলা: public /docs পেজ আর কখনো অস্বলুত endpoint দেখাবে না, আর
health-aggregation তার docstring-অনুযায়ী /admin-api/health-aggregation-এই
মাউন্ট থাকবে (double prefix নিষিদ্ধ)।
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
FRONTEND_PAGES = REPO_ROOT / "frontend" / "src" / "pages" / "PublicPages.tsx"
ROUTERS = REPO_ROOT / "backend" / "api" / "routers.py"
HEALTH_AGG = REPO_ROOT / "backend" / "api" / "routes" / "health_aggregation.py"


class TestDocsPageContract:
    def test_fabricated_chat_completions_row_removed(self):
        text = FRONTEND_PAGES.read_text(encoding="utf-8")
        assert "chat/completions" not in text, (
            "public /docs must not advertise endpoints that do not exist"
        )

    def test_real_chat_entrypoints_documented(self):
        text = FRONTEND_PAGES.read_text(encoding="utf-8")
        assert "/api/v1/stream/chat" in text, "real SSE chat entrypoint must be listed"
        assert "/api/chat/orchestrate" in text, "real orchestration entrypoint must be listed"


class TestHealthAggregationMount:
    def test_no_double_prefix_in_registry(self):
        import re

        text = ROUTERS.read_text(encoding="utf-8")
        block_match = re.search(
            r'\{\s*(?:#[^}]*\n\s*)*"path":\s*"api\.routes\.health_aggregation".*?\}',
            text,
            re.DOTALL,
        )
        assert block_match, "health_aggregation registry entry not found"
        block = block_match.group(0)
        assert '"prefix": ""' in block, (
            "health_aggregation must mount prefix-less (its own /admin-api prefix applies)"
        )

    def test_live_path_matches_docstring_and_frontend(self):
        # বাংলা মন্তব্য (#2504 CI round-5): মূল টেস্টটি frontend consumer
        # (ServiceHealthMonitor.tsx) পড়ত — #2503 (#2481 dead-component cleanup)
        # সেটি ডিলিট করেছে, কিন্তু এই কন্ট্র্যাক্ট-টেস্ট রেখে গিয়েছিল। ব্যাকএন্ড
        # পক্ষের assertion গুলো এখনও পুরোপুরি বৈধ — সেগুলোই রাখা হলো:
        # (১) router prefix সঠিক, (২) লাইভ রুট docstring-অনুযায়ী mount-এড।
        router_text = HEALTH_AGG.read_text(encoding="utf-8")
        assert 'prefix="/admin-api"' in router_text
        # লাইভ রুট নিজেই docstring-এর advertised পাথে আছে কিনা
        assert '@router.get("/health-aggregation"' in router_text, (
            "live route must stay at /health-aggregation (mounted under /admin-api)"
        )
