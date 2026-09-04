"""SupremeAI 2.0 — Portal-ভিত্তিক CORS নীতি (pure functions, কোনো side-effect নেই)।

বাংলা মন্তব্য: User API ও Admin API সম্পূর্ণ আলাদা ব্রাউজার-অরিজিন সেট ট্রাস্ট করে।
এই মডিউলটি সেই নীতিকে একটি জায়গায় কেন্দ্রীভূত করে যাতে:
  1. app_user.py / app_admin.py দুটোই একই সোর্স-অফ-ট্রুথ ব্যবহার করে;
  2. misconfigured env var (যেমন USER_CORS_ORIGINS-এ admin console origin) থাকলেও
     boot-টাইমে সেটি ছেঁকে ফেলা হয় — defense in depth;
  3. টেস্ট ফাইল (tests/test_app_isolation.py) কোনো FastAPI app বুট না করেই
     এবং ENV=production সিমুলেট না করেই নীতিটি যাচাই করতে পারে।

কোনো FastAPI/pydantic import নেই — ইচ্ছাকৃতভাবে dependency-free রাখা হয়েছে।
"""

from __future__ import annotations

import json
import os
from collections.abc import Iterable


def _load_origins(env_var: str, default: tuple[str, ...]) -> tuple[str, ...]:
    val = os.getenv(env_var)
    if val:
        try:
            parsed = json.loads(val)
            if isinstance(parsed, list):
                return tuple(parsed)
        except json.JSONDecodeError:
            return tuple([x.strip() for x in val.split(",") if x.strip()])
    return default


USER_ALLOWED_ORIGINS: tuple[str, ...] = _load_origins(
    "CORS_ORIGINS",
    (
        "https://supremeai-lac.vercel.app",
        "https://supremeai-a.web.app",
        "https://supremeai-admin.web.app",
    ),
)

ADMIN_ALLOWED_ORIGINS: tuple[str, ...] = _load_origins("ADMIN_CORS_ORIGINS", ())

# বাংলা মন্তব্য: সিঙ্গেল ব্যাকএন্ড আর্কিটেকচারের জন্য Denylist ফাঁকা রাখা হলো
USER_ORIGIN_DENYLIST: frozenset[str] = frozenset()

# বাংলা মন্তব্য: সিঙ্গেল ব্যাকএন্ড আর্কিটেকচারের জন্য Denylist ফাঁকা রাখা হলো
ADMIN_ORIGIN_DENYLIST: frozenset[str] = frozenset()


def _dedupe(origins: Iterable[str]) -> list[str]:
    """অর্ডার রক্ষা করে ডুপ্লিকেট বাদ দেয়।"""
    seen: set[str] = set()
    result: list[str] = []
    for origin in origins:
        cleaned = (origin or "").strip()
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        result.append(cleaned)
    return result


def resolve_user_cors_origins(configured: Iterable[str] | None) -> list[str]:
    """User API-এর চূড়ান্ত allow_origins তালিকা তৈরি করে।

    বাংলা মন্তব্য:
      - wildcard ('*') সবসময় বাদ — credentialed CORS-এর সাথে এটি অবৈধ ও অনিরাপদ;
      - admin surface অরিজিন সবসময় বাদ — আর্কিটেকচারাল আইসোলেশন;
      - কিছুই না থাকলে নিরাপদ ডিফল্ট user অরিজিন সেট করা হয় (boot crash এড়াতে)।
    """
    cleaned = [o for o in _dedupe(configured or []) if o != "*" and o not in ADMIN_ORIGIN_DENYLIST]
    if not cleaned:
        return list(USER_ALLOWED_ORIGINS)
    return cleaned


def resolve_admin_cors_origins(configured: Iterable[str] | None) -> list[str]:
    """Admin API-এর চূড়ান্ত allow_origins তালিকা তৈরি করে।

    বাংলা মন্তব্য:
      - wildcard ('*') সবসময় বাদ;
      - user surface অরিজিন সবসময় বাদ (denylist) — admin/user mixing প্রতিরোধ;
      - admin console origin সবসময় উপস্থিত থাকবে — না থাকলে preflight 403/500 হয়।
    """
    cleaned = [o for o in _dedupe(configured or []) if o != "*" and o not in USER_ORIGIN_DENYLIST]
    for required in ADMIN_ALLOWED_ORIGINS:
        if required not in cleaned:
            cleaned.append(required)
    return cleaned


__all__ = [
    "ADMIN_ALLOWED_ORIGINS",
    "ADMIN_ORIGIN_DENYLIST",
    "USER_ALLOWED_ORIGINS",
    "USER_ORIGIN_DENYLIST",
    "resolve_admin_cors_origins",
    "resolve_user_cors_origins",
]
