import re

with open("tests/test_api_key_middleware.py", encoding="utf-8") as f:
    content = f.read()


def rewrite_test_func(match):
    func = match.group(0)
    # Remove them from the original location
    func = re.sub(r"        app\.add_middleware\(APIKeyAuthMiddleware\)\n", "", func)
    func = re.sub(r"        client = TestClient\(app\)\n", "", func)

    # Insert them before `resp = client.get(`
    func = func.replace(
        "            resp = client.get(",
        "            app.add_middleware(APIKeyAuthMiddleware)\n            client = TestClient(app)\n\n            resp = client.get(",
    )
    return func


# We will apply this to all the test functions that use client.get
content = re.sub(
    r"    def test_validates_valid_api_key.*?assert resp\.status_code == 200",
    rewrite_test_func,
    content,
    flags=re.DOTALL,
)
content = re.sub(
    r"    def test_rejects_invalid_api_key.*?assert resp\.status_code == 401",
    rewrite_test_func,
    content,
    flags=re.DOTALL,
)
content = re.sub(
    r"    def test_rejects_revoked_api_key.*?assert resp\.status_code == 403",
    rewrite_test_func,
    content,
    flags=re.DOTALL,
)
content = re.sub(
    r"    def test_rejects_expired_api_key.*?assert resp\.status_code == 403",
    rewrite_test_func,
    content,
    flags=re.DOTALL,
)
content = re.sub(
    r"    def test_rate_limit_exceeded.*?assert resp\.status_code == 429",
    rewrite_test_func,
    content,
    flags=re.DOTALL,
)

with open("tests/test_api_key_middleware.py", "w", encoding="utf-8") as f:
    f.write(content)
