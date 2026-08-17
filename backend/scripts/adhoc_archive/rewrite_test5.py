import re

with open("tests/test_api_key_middleware.py", encoding="utf-8") as f:
    content = f.read()

# Make sure os is imported
if "import os" not in content:
    content = "import os\n" + content

# For each test except test_rate_limit_exceeded, insert os.environ["RATE_LIMIT_ENABLED"] = "false" before app = FastAPI()
# For test_rate_limit_exceeded, insert os.environ["RATE_LIMIT_ENABLED"] = "true" before app = FastAPI()


def inject_env(match):
    test_name = match.group(1)
    if "test_rate_limit_exceeded" in test_name:
        return f'def {test_name}(self):\n        os.environ["RATE_LIMIT_ENABLED"] = "true"\n        app = FastAPI()'
    else:
        return f'def {test_name}(self):\n        os.environ["RATE_LIMIT_ENABLED"] = "false"\n        app = FastAPI()'


content = re.sub(
    r"def (test_[a-zA-Z0-9_]+)\(self\):\n\s*(?:\"\"\"[^\"]*\"\"\"\n\s*)?app = FastAPI\(\)",
    inject_env,
    content,
)

# Remove the get_redis patch I added
content = content.replace(
    '            patch("core.rate_limiter.AsyncRateLimiter._get_redis", side_effect=Exception("mock")),\n',
    "",
)

# For test_rate_limit_exceeded, we need to mock _get_redis so it falls back to InMemoryFallbackLimiter and correctly rate limits.
# I will use patch object to mock it.
rl_test = """
    def test_rate_limit_exceeded(self):
        os.environ["RATE_LIMIT_ENABLED"] = "true"
        app = FastAPI()

        @app.get("/api/test")
        def test_endpoint():
            return PlainTextResponse("ok")

        mock_row = {
            "id": "key-123",
            "key_hash": "hashed_key",
            "revoked": False,
            "rate_limit_rps": 1,
            "expires_at": None,
        }

        with (
            patch("core.security.api_key_middleware.is_test_environment", return_value=False),
            patch("core.security.api_key_middleware.get_db_pool") as mock_pool,
            patch("core.security.api_key_middleware.hash_api_key", return_value="hashed_key"),
            patch("core.rate_limiter.AsyncRateLimiter._get_redis", side_effect=Exception("mock")),
        ):
            mock_pool.return_value.fetchrow = AsyncMock(return_value=mock_row)

            app.add_middleware(APIKeyAuthMiddleware)
            client = TestClient(app)

            client.get(
                "/api/test",
                headers={"x-api-key": "sk-supreme-5505050505abcdef"},
            )
            resp = client.get(
                "/api/test",
                headers={"x-api-key": "sk-supreme-5505050505abcdef"},
            )

        assert resp.status_code == 429
"""

content = re.sub(
    r"    def test_rate_limit_exceeded\(self\):.*?assert resp\.status_code == 429",
    rl_test.strip("\n"),
    content,
    flags=re.DOTALL,
)


with open("tests/test_api_key_middleware.py", "w", encoding="utf-8") as f:
    f.write(content)
