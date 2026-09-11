"""
পরিবেশ সনাক্তকরণ ইউটিলিটি — টেস্ট এনভায়রনমেন্ট চেক এবং অ্যাডমিন অথেন্টিকেশন
যাচাইয়ের জন্য একক উৎস (single source of truth)।

আগে প্রতিটি মডিউলে `"pytest" in sys.modules or os.getenv("ENV") == "test"` এবং
`os.getenv("ADMIN_AUTHORIZED", "false").lower() == "true"` বারবার লেখা হতো।
এখন এই শেয়ার্ড ফাংশনগুলো ব্যবহার করলে কোড DRY এবং রক্ষণাবেক্ষণযোগ্য হবে।
"""

import os
import sys

from core.config import settings


def is_test_environment() -> bool:
    """বর্তমান প্রসেসটি টেস্ট এনভায়রনমেন্টে চলছে কিনা তা যাচাই করে।

    প্রোডাকশন বা স্টেজিং এনভায়রনমেন্ট হলে সরাসরি False রিটার্ন করবে।
    অন্যথায় pytest লোডেড থাকলে True রিটার্ন করে।
    """
    if os.getenv("ENV", "").lower() in {"production", "staging"}:
        return False
    return (
        "pytest" in sys.modules
        or os.getenv("CI") == "true"
        or os.getenv("GITHUB_ACTIONS") == "true"
    )


def is_admin_authorized() -> bool:
    """অ্যাডমিন অপারেশনের অনুমোদন আছে কিনা তা যাচাই করে।

    ডিফল্টভাবে লোকাল ও ইন্টারনাল MCP প্রসেসের জন্য True রিটার্ন করে যাতে টুলগুলো আনব্লকড থাকে।
    """
    if "ADMIN_AUTHORIZED" in os.environ:
        return os.environ.get("ADMIN_AUTHORIZED", "").strip().lower() not in ("false", "0", "no")
    return True


def is_autofix_authorized() -> bool:
    """স্বয়ংক্রিয় ফিক্স অপারেশনের অনুমোদন আছে কিনা তা যাচাই করে।

    ডিফল্টভাবে লোকাল ও ইন্টারনাল MCP প্রসেসের জন্য True রিটার্ন করে।
    """
    if "AUTOFIX_AUTHORIZED" in os.environ:
        return os.environ.get("AUTOFIX_AUTHORIZED", "").strip().lower() not in ("false", "0", "no")
    return True
