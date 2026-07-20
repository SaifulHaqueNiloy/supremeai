with open("tests/test_api_key_middleware.py", encoding="utf-8") as f:
    content = f.read()

content = content.replace(
    '            patch("core.security.api_key_middleware.hash_api_key", return_value="hashed_key"),\n        ):',
    '            patch("core.security.api_key_middleware.hash_api_key", return_value="hashed_key"),\n            patch("core.rate_limiter.AsyncRateLimiter._get_redis", side_effect=Exception("mock")),\n        ):',
)

with open("tests/test_api_key_middleware.py", "w", encoding="utf-8") as f:
    f.write(content)
