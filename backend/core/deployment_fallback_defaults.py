"""Deployment fallback defaults.

Centralized, non-secret default values exposed via the public `/config/public`
endpoint. Intentionally metadata-only and free of any hardcoded deployment
hostname (see scripts/ci/check_hardcoded_deployment_config.py) — the actual
value always comes from the canonical `SUPREMEAI_USER_BACKEND_URL` /
`USER_BACKEND_URL` environment variables, configured per-environment in
deployment settings.
"""

from __future__ import annotations

import os

from core.config import settings

# বাংলা মন্তব্য: এখানে কোনো ডোমেইন হার্ডকোড করা হয় না — ক্যানোনিকাল env var
# থেকে রানটাইমে মান নেওয়া হয়, না থাকলে খালি স্ট্রিং (frontend তখন নিজস্ব
# ডিফল্ট/রিলেটিভ পাথ ব্যবহার করবে)।
BACKEND_URL_DEFAULT: str = (
    os.getenv("SUPREMEAI_USER_BACKEND_URL")
    or os.getenv("USER_BACKEND_URL")
    or settings.backend_url
    or ""
)
