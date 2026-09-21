import os
from unittest.mock import patch

import jwt
import pytest
from fastapi.testclient import TestClient

from core.app import app
from core.config import settings

client = TestClient(app)

mock_token = jwt.encode(
    {"user_id": "test-user-id", "role": "admin"}, settings.jwt_secret, algorithm="HS256"
)
auth_headers = {"Authorization": f"Bearer {mock_token}"}


@pytest.fixture(autouse=True)
def mock_stripe():
    with patch("stripe.checkout.Session.create") as mock_session:
        # Instead of a dict, make the mock return an object with .id and .url
        mock_session.return_value.id = "cs_test_123"
        mock_session.return_value.url = "https://stripe.com/test"
        yield mock_session


def test_get_plans():
    # Verify plans list — SUBSCRIPTION_PLANS is a dict keyed by plan name
    resp = client.get("/payments/plans", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "plans" in data
    plans = data["plans"]
    assert "free" in plans
    assert plans["free"]["id"] == "price_free"


def test_create_checkout_session_mock():
    # The endpoint validates the raw key shape before calling Stripe; provide
    # a test-mode key via the env-backed secret cache so the (autouse-mocked)
    # Stripe SDK path is exercised. stripe_api_key is a read-only property.
    with patch.dict(os.environ, {"STRIPE_API_KEY": "sk_test_dummy_key"}):
        resp = client.post(
            "/payments/checkout",
            json={
                "price_id": "price_basic_monthly",
                "success_url": "http://localhost/success",  # is_local()
                "cancel_url": "http://localhost/cancel",  # is_local()
                "user_id": "test-user-id",
            },
            headers=auth_headers,
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["session_id"] == "cs_test_123"
    assert "https://stripe.com/test" in data["url"]


def test_webhook_ignored_if_missing_config():
    # Verify the webhook fail-safe contract: a request without a signature
    # header takes the ignore path ("misconfiguration shouldn't break
    # production/CI") instead of erroring. We exercise the missing-signature
    # half of the guard deterministically — in CI the secret vault mocks a
    # non-empty STRIPE_WEBHOOK_SECRET, so the missing-SECRET half cannot be
    # triggered by patching the settings field (read-only property over the
    # env-backed secret cache). Both halves hit the same ignore branch.
    headers = {**auth_headers}  # no stripe-signature header
    resp = client.post("/payments/webhook", headers=headers, content=b"some-payload")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ignored"
    assert body["reason"] == "missing_stripe_webhook_secret_or_signature"
