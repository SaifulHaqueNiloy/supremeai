import os

from utils.environment import (
    is_admin_authorized,
    is_autofix_authorized,
    is_test_environment,
)


class TestIsTestEnvironment:
    def test_returns_true_when_testing_flag_set(self):
        os.environ["TESTING"] = "true"
        try:
            assert is_test_environment() is True
        finally:
            del os.environ["TESTING"]

    def test_ci_does_not_enable_test_mode(self):
        """CI env var নিজে থেকে কখনো test mode চালু করবে না (is_test_environment contract)।

        বাংলা: এই ফাংশনের চুক্তি — শুধু ``CI=true`` দেখে কখনো True হবে না।
        টেস্টটি pytest-এর ভেতরে চলে, তাই in-process assertion সবসময় True হয়
        (pytest নিজেই sys.modules-এ থাকে) — সেটা CI-র অবদান প্রমাণ করে না।
        সঠিক পরীক্ষা: pytest-মুক্ত subprocess-এ ফাংশনটি চালিয়ে দেখা।
        """
        import subprocess
        import sys

        code = (
            "import os; os.environ['CI']='true'; os.environ.pop('TESTING', None); "
            "os.environ.pop('ENV', None); "
            "from utils.environment import is_test_environment; print(is_test_environment())"
        )
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert result.returncode == 0, f"subprocess failed: {result.stderr[-300:]}"
        assert result.stdout.strip() == "False", (
            "CI env var alone must not enable test mode — "
            f"got {result.stdout.strip()!r} in a pytest-free process"
        )

    def test_returns_false_in_production(self):
        os.environ["ENV"] = "production"
        try:
            assert is_test_environment() is False
        finally:
            del os.environ["ENV"]

    def test_returns_false_in_staging(self):
        os.environ["ENV"] = "staging"
        try:
            assert is_test_environment() is False
        finally:
            del os.environ["ENV"]

    def test_returns_true_default_dev(self):
        if "ENV" in os.environ:
            del os.environ["ENV"]
        if "CI" in os.environ:
            del os.environ["CI"]
        if "GITHUB_ACTIONS" in os.environ:
            del os.environ["GITHUB_ACTIONS"]
        try:
            assert is_test_environment() is True
        finally:
            pass


class TestIsAdminAuthorized:
    def test_returns_true_when_set(self):
        os.environ["ADMIN_AUTHORIZED"] = "true"
        try:
            assert is_admin_authorized() is True
        finally:
            del os.environ["ADMIN_AUTHORIZED"]

    def test_returns_false_when_unset(self):
        if "ADMIN_AUTHORIZED" in os.environ:
            del os.environ["ADMIN_AUTHORIZED"]
        assert is_admin_authorized() is False

    def test_returns_false_case_insensitive(self):
        os.environ["ADMIN_AUTHORIZED"] = "TRUE"
        try:
            assert is_admin_authorized() is True
        finally:
            del os.environ["ADMIN_AUTHORIZED"]


class TestIsAutofixAuthorized:
    def test_returns_true_when_set(self):
        os.environ["AUTOFIX_AUTHORIZED"] = "true"
        try:
            assert is_autofix_authorized() is True
        finally:
            del os.environ["AUTOFIX_AUTHORIZED"]

    def test_returns_false_when_unset(self):
        if "AUTOFIX_AUTHORIZED" in os.environ:
            del os.environ["AUTOFIX_AUTHORIZED"]
        assert is_autofix_authorized() is False
