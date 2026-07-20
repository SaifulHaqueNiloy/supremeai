import re

with open("tests/test_api_key_middleware.py", encoding="utf-8") as f:
    content = f.read()

pattern = r'        with \(\n            patch\("core\.security\.api_key_middleware\.is_test_environment", return_value=False\),\n            patch\("core\.security\.api_key_middleware\.get_db_pool"\) as mock_pool,\n            patch\("core\.security\.api_key_middleware\.hash_api_key", return_value="hashed_key"\),\n        \):'

new_general = (
    "        with (\n"
    '            patch("core.security.api_key_middleware.is_test_environment", return_value=False),\n'
    '            patch("core.security.api_key_middleware.get_db_pool") as mock_pool,\n'
    '            patch("core.security.api_key_middleware.hash_api_key", return_value="hashed_key"),\n'
    '            patch("core.security.api_key_middleware.AsyncRateLimiter.acquire", new_callable=AsyncMock, return_value=True),\n'
    "        ):"
)

content = re.sub(pattern, new_general, content)


def replace_in_func(match):
    func_content = match.group(0)
    func_content = func_content.replace("return_value=True", "return_value=False")
    return func_content


content = re.sub(
    r"def test_rate_limit_exceeded.*?assert resp\.status_code == 429",
    replace_in_func,
    content,
    flags=re.DOTALL,
)

with open("tests/test_api_key_middleware.py", "w", encoding="utf-8") as f:
    f.write(content)
