"""specs/001 close-out — configuration contract tests (MASTER_PLAN Phase 1).

বাংলা: এই টেস্টগুলো কনফিগ সিস্টেমের *চুক্তি* লক করে:
  1. server.py-র CORS allow-list অবশ্যই middleware/cors_policy.py resolver দিয়ে
     তৈরি হবে (single source of truth — দুটো সমান্তরাল পথ আর থাকবে না);
  2. wildcard '*' কোনো resolved origin-list-এ বাঁচতে পারবে না;
  3. ConfigValidationReport সৎ হবে — অনুপস্থিত required var = error,
     ভাঙা ফরম্যাট = error, fix suggestion ছাড়া error চলবে না।
"""

from __future__ import annotations

import unittest
from unittest.mock import patch


class TestCorsContract(unittest.TestCase):
    def test_server_origins_built_through_policy_resolvers(self):
        """server.py-র CORS allow-list অবশ্যই resolver-চালিত (source contract)।

        বাংলা: api.server ইমপোর্ট ভারী (asyncpg ইত্যাদি লাগে) — তাই চুক্তিটি
        দুইভাবে যাচাই হয়: (১) সোর্সে resolver ব্যবহার আছে কি না, (২) resolver-
        সমাহিত allow-list-এর রানটাইম বৈশিষ্ট্য (wildcard নেই, dev origin আছে)।
        """
        from pathlib import Path

        server_src = Path(__file__).resolve().parents[3] / "api" / "server.py"
        code = server_src.read_text(encoding="utf-8")
        self.assertIn("resolve_user_cors_origins", code)
        self.assertIn("resolve_admin_cors_origins", code)
        self.assertIn("resolve_user_cors_origins", code)
        # আর সরাসরি env.split() দিয়ে allow-list বানানো হয় না (unification contract)
        self.assertNotIn(
            "_allowed_origins = _dev_origins + _prod_origins",
            code,
            "server.py must build origins through cors_policy resolvers, not raw concat",
        )

    def test_resolved_allowlist_properties(self):
        """Resolver-সমাহিত allow-list (server.py-র নির্মাণপদ্ধতি) চুক্তি মেনে চলে।"""
        from middleware.cors_policy import resolve_admin_cors_origins, resolve_user_cors_origins

        dev = ["http://localhost:3000", "http://localhost:5173", "tauri://localhost"]
        prod = ["https://app.example.com"]
        admin = ["https://admin.example.com"]
        allowed = set(resolve_user_cors_origins(dev + prod)) | set(
            resolve_admin_cors_origins(admin)
        )
        self.assertNotIn("*", allowed)
        self.assertIn("https://app.example.com", allowed)
        self.assertIn("http://localhost:3000", allowed)  # dev convenience preserved

    def test_resolver_drops_wildcard_and_keeps_explicit(self):
        from middleware.cors_policy import resolve_user_cors_origins

        resolved = resolve_user_cors_origins(
            ["*", "http://localhost:3000", "https://app.example.com"]
        )
        self.assertNotIn("*", resolved)
        self.assertIn("https://app.example.com", resolved)

    def test_admin_resolver_guarantees_required_admin_origins(self):
        import os

        from middleware.cors_policy import resolve_admin_cors_origins

        with patch.dict(
            os.environ, {"ADMIN_CORS_ORIGINS": "https://admin.example.com"}, clear=False
        ):
            # মডিউল-লেভেল কনস্ট্যান্ট আগে লোড হতে পারে — resolver-এর কনট্র্যাক্ট:
            # configured যা-ই হোক, ADMIN_ALLOWED_ORIGINS-এ থাকা origin বাদ পড়ে না
            from middleware import cors_policy as cp

            required = cp.ADMIN_ALLOWED_ORIGINS
            resolved = resolve_admin_cors_origins([])
            for origin in required:
                self.assertIn(origin, resolved)


class TestConfigValidationReportContract(unittest.TestCase):
    def test_report_is_honest_about_missing_secret(self):
        import os

        from core.config_validation import build_config_validation_report

        with patch.dict(os.environ, {"JWT_SECRET": ""}, clear=False):
            report = build_config_validation_report(env="test")
        names = {c.name for c in report.errors}
        self.assertIn("JWT_SECRET", names)
        self.assertFalse(report.ok)

    def test_every_error_has_fix_suggestion(self):
        from core.config_validation import build_config_validation_report

        report = build_config_validation_report(env="test")
        for err in report.errors:
            self.assertTrue(
                err.fix_suggestion,
                f"error {err.name} without fix suggestion violates the contract",
            )

    def test_report_fields_shape(self):
        from core.config_validation import build_config_validation_report

        report = build_config_validation_report(env="test")
        data = report.model_dump()
        for key in ("environment", "ok", "errors", "warnings", "checks", "generated_at"):
            self.assertIn(key, data)
        self.assertEqual(data["environment"], "test")

    def test_bad_redis_format_is_error(self):
        import os

        from core.config_validation import build_config_validation_report

        with patch.dict(os.environ, {"REDIS_URL": "not-a-redis-url"}, clear=False):
            report = build_config_validation_report(env="test")
        names = {c.name for c in report.errors}
        self.assertIn("REDIS_URL", names)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
