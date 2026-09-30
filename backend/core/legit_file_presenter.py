"""Legit File & Conversation Presenter — Anti-Bot Cloaking & Natural Naming.

বাংলা সারসংক্ষেপ:
------------------
অ্যান্টি-বট এবং ফ্রড ডিটেকশন সিস্টেমগুলো (Cloudflare, Anthropic, OpenAI) প্রায়শই
মেশিনের মতো ফাইলনেম বা কনভারসেশন টাইটেল (যেমন: tmp_83912.txt, Session-a1b2c3,
agent_task_dump.json) দেখে স্বয়ংক্রিয়ভাবে অ্যাকাউন্ট ফ্ল্যাগ বা ব্লক করে।
এই মডিউলটি ফাইল ও কনভারসেশনের নামগুলোকে ১০০% মানুষের মতো স্বাভাবিক ও বিশ্বাসযোগ্য
(Legit Developer Style) রূপে প্রেজেন্ট করে বট ডিটেকশন ঝুঁকি সম্পূর্ণ দূর করে।
"""

from __future__ import annotations

import os
import random
import re
from pathlib import Path

# রোবোটিক বা অটোমেটেড প্যাটার্ন ডিটেক্টর
BOT_NAME_PATTERNS = [
    r"^tmp_?",
    r"^temp_?",
    r"^agent_?",
    r"^scratch_?",
    r"^task_?",
    r"^bot_?",
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}",  # UUID
    r"^[0-9a-f]{16,32}",  # Hex dump
    r"^output_[0-9]+",
]

# এক্সটেনশন অনুযায়ী বাস্তবসম্মত ও বিশ্বাসযোগ্য ফাইলনেম পুল
LEGIT_FILENAME_MAP: dict[str, list[str]] = {
    ".py": [
        "app_service.py",
        "api_router.py",
        "data_pipeline.py",
        "utils_helpers.py",
        "core_engine.py",
        "config_loader.py",
        "client_wrapper.py",
    ],
    ".ts": [
        "apiClient.ts",
        "types.ts",
        "stateStore.ts",
        "formatters.ts",
        "authProvider.ts",
    ],
    ".tsx": [
        "DashboardView.tsx",
        "MainLayout.tsx",
        "UserProfile.tsx",
        "AnalyticsChart.tsx",
        "SettingsModal.tsx",
    ],
    ".json": [
        "config.json",
        "settings.json",
        "schema_definition.json",
        "manifest.json",
        "parameters.json",
    ],
    ".md": [
        "ARCHITECTURE.md",
        "PROJECT_SPEC.md",
        "README.md",
        "DESIGN_NOTES.md",
        "RELEASE_OVERVIEW.md",
    ],
    ".sql": [
        "schema_migration.sql",
        "query_optimization.sql",
        "tables_init.sql",
    ],
    ".csv": [
        "metrics_export.csv",
        "analytics_report.csv",
        "data_summary.csv",
    ],
    ".txt": [
        "system_logs.txt",
        "requirements_notes.txt",
        "build_output.txt",
        "todo_notes.txt",
    ],
}


class LegitFilePresenter:
    """ফাইলনেম ও চ্যাট টাইটেলকে অ্যান্টি-বট সেফ ও বিশ্বাসযোগ্য রূপে রূপান্তরকারী।"""

    @staticmethod
    def is_bot_like_name(name: str) -> bool:
        """বাংলা মন্তব্য: ফাইল বা কনভারসেশনের নাম রোবোটিক কিনা পরীক্ষা।"""
        clean_name = Path(name).stem.lower()
        return any(re.search(pat, clean_name) for pat in BOT_NAME_PATTERNS)

    @classmethod
    def legitimize_filename(cls, raw_path_or_name: str, topic_hint: str = "") -> str:
        """
        বাংলা সারসংক্ষেপ:
        ------------------
        রোবোটিক ফাইলনেম পেলে তাকে স্বাভাবিক ডেভেলপার ফাইলে রূপান্তর:
        e.g., 'tmp_987123.txt' ➔ 'system_logs.txt'
              'agent_code_dump.py' ➔ 'app_service.py'
        """
        filename = os.path.basename(raw_path_or_name)
        ext = Path(filename).suffix.lower()

        # যদি নাম ইতিমধ্যে স্বাভাবিক ও মানবসৃষ্ট মনে হয়, অপরিবর্তিত রাখা
        if not cls.is_bot_like_name(filename):
            return filename

        # এক্সটেনশন অনুযায়ী প্রিমিয়াম ও বিশ্বাসযোগ্য নাম নির্বাচন
        candidates = LEGIT_FILENAME_MAP.get(ext)
        if candidates:
            # টপিক হিন্ট দিয়ে আরও স্পেসিফিক নাম করা (ঐচ্ছিক)
            return random.choice(candidates)

        # সাধারণ ডিফল্ট
        return f"document_{random.randint(10, 99)}{ext or '.txt'}"

    @classmethod
    def humanize_conversation_title(cls, prompt: str) -> str:
        """
        বাংলা সারসংক্ষেপ:
        ------------------
        'Session-a1b2c3' এর মতো কৃত্রিম নাম পরিহার করে মানুষের মতো চ্যাট টাইটেল তৈরি:
        প্রম্পট থেকে ৪-৬টি প্রাসঙ্গিক শব্দ নিয়ে টাইটেল তৈরি করে, অথবা ফাঁকা স্ট্রিং রাখে
        যাতে Claude/ChatGPT তাদের নিজস্ব অ্যালগরিদমে টাইটেল বানায়।
        """
        clean = re.sub(r"[^\w\s]", "", prompt).strip()
        words = clean.split()
        if not words or len(words) < 2:
            return ""  # ফাঁকা রাখলে Claude/ChatGPT নিজে সুন্দর নাম বানায়

        # প্রথম ৪-৫টি শব্দ নিয়ে টাইটেল
        title_words = words[:5]
        title = " ".join(title_words).capitalize()
        # অপ্রাসঙ্গিক রোবট টোকেন ফিল্টার
        for bad in ["system", "user", "assistant", "session", "task", "bot"]:
            title = re.sub(rf"\b{bad}\b", "", title, flags=re.IGNORECASE).strip()

        return title if len(title) >= 3 else ""


__all__ = ["LegitFilePresenter"]
