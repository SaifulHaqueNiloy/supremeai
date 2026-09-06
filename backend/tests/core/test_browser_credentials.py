import os
import time

import jwt
import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("OPENROUTER_API_KEY", "")
os.environ.setdefault("HF_API_KEY", "")
os.environ.setdefault("OLLAMA_URL", "http://127.0.0.1:11434")  # is_local()
from api.deps import get_current_user_token
from api.routes.admin_dashboard import require_admin_token
from core.app import app as app_mod
from core.config import settings
from core.security.secure_credential_store import SecureCredentialStore, generate_key

client = TestClient(app_mod)


def _generate_test_token(sub="admin", role="admin"):
    secret = settings.jwt_secret or "test-secret-key-12345678901234567890"
    return jwt.encode(
        {"sub": sub, "role": role, "exp": time.time() + 3600}, secret, algorithm="HS256"
    )


admin_token = _generate_test_token("admin", "admin")
auth_headers = {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture(autouse=True)
def override_admin_auth():
    """বাংলা: require_admin_token ও get_current_user_token override করা হচ্ছে।"""
    app_mod.dependency_overrides[require_admin_token] = lambda: {
        "sub": "admin",
        "uid": "admin",
        "role": "admin",
    }
    app_mod.dependency_overrides[get_current_user_token] = lambda: {"sub": "admin", "role": "admin"}
    yield
    app_mod.dependency_overrides = {}


@pytest.fixture(autouse=True)
def reset_globals():
    os.environ["SUPREMEAI_API_KEY"] = "test-token"
    import api.routes.browser as browser_mod

    browser_mod.CREDENTIALS.clear()
    browser_mod.RECENT_ACTIVITIES.clear()
    browser_mod.TASKS.clear()
    browser_mod.FINDINGS.clear()
    try:
        yield
    finally:
        os.environ.pop("SUPREMEAI_API_KEY", None)


def test_secure_credential_store_encrypt_decrypt(monkeypatch):
    import json

    monkeypatch.setenv("SUPREMEAI_CREDENTIAL_ENC_KEY", generate_key())
    store = SecureCredentialStore()
    payload = {"serviceName": "example", "username": "user", "password": "secret"}
    ciphertext, key_ref = store.encrypt(json.dumps(payload))
    assert isinstance(ciphertext, str)
    decrypted = store.decrypt(ciphertext, key_ref)
    assert json.loads(decrypted) == payload


def test_secure_credential_store_mask():
    store = SecureCredentialStore()
    assert store.mask("secrets") == "secr***"


def test_browser_save_and_list_credentials():
    resp = client.post(
        "/api/browser/credentials",
        json={"serviceName": "example.com", "username": "user1", "password": "supersecretpassword"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["serviceName"] == "example.com"
    cred_id = body["id"]

    resp = client.get("/api/browser/credentials?userId=default", headers=auth_headers)
    assert resp.status_code == 200
    creds = resp.json()["credentials"]
    assert len(creds) >= 1
    target = next((c for c in creds if c.get("id") == cred_id), creds[0])
    assert target["serviceName"] in ("example.com", "user1")
    # Secret must be masked in API response
    assert "supersecretpassword" not in target.get("password", "")
    assert "***" in target.get("password", "")


def test_browser_credential_lifecycle_use_revoke_delete():
    # 1. Save credential
    resp = client.post(
        "/api/browser/credentials",
        json={"provider": "github.com", "label": "bot-pat", "secret": "ghp_1234567890abcdef"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    cred_id = resp.json()["id"]

    # 2. Use credential (for autonomous browser automation)
    use_resp = client.post(
        f"/api/browser/credentials/{cred_id}/use",
        json={"action": "autofill"},
        headers=auth_headers,
    )
    assert use_resp.status_code == 200
    use_body = use_resp.json()
    assert use_body["id"] == cred_id
    assert use_body["secret"] == "ghp_1234567890abcdef"

    # 3. Revoke credential
    revoke_resp = client.post(
        f"/api/browser/credentials/{cred_id}/revoke",
        headers=auth_headers,
    )
    assert revoke_resp.status_code == 200
    assert revoke_resp.json()["is_revoked"] is True

    # 4. Use of revoked credential should fail
    failed_use = client.post(
        f"/api/browser/credentials/{cred_id}/use",
        json={"action": "autofill"},
        headers=auth_headers,
    )
    assert failed_use.status_code == 400

    # 5. Delete credential
    del_resp = client.delete(
        f"/api/browser/credentials/{cred_id}",
        headers=auth_headers,
    )
    assert del_resp.status_code == 200
    assert del_resp.json()["success"] is True
