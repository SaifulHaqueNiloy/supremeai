"""
Prompt Enhancement Engine (প্রম্পট উন্নয়ন ও স্টেলথ ইঞ্জিন)
======================================================
SupremeAI Zero-Cost Ecosystem-এর জন্য প্রম্পট অপ্টিমাইজেশন ও অ্যান্টি-বট কেমোফ্লেজ ইঞ্জিন।

৩টি প্রধান মোড:
1. ENHANCE_UI_CLICK (বাটন ক্লিক মোড - Kilo Code / IDE স্টাইল)
2. DEV_API (সরাসরি প্রোগ্রামাটিক এপিআই রিকোয়েস্ট মোড)
3. STEALTH_CHAT (অ্যান্টি-বট হিউম্যান শেয়ারিং / কপি-পেস্ট কেমোফ্লেজ মোড)
"""

import random
import re
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class EnhancementMode(StrEnum):
    """প্রম্পট উন্নয়নের মোড"""

    ENHANCE_UI_CLICK = "ui_sparkle"  # বাংলা মন্তব্য: এডিটর বা ইনপুট বারের স্পার্কল বাটনে ক্লিক
    DEV_API = "dev_api"  # বাংলা মন্তব্য: এক্সটারনাল ডেভেলপার এপিআই কল
    STEALTH_CHAT = "stealth_chat"  # বাংলা মন্তব্য: অন্য চ্যাট/এআই থেকে কপি-পেস্ট করার হিউম্যান কেমোফ্লেজ


@dataclass
class EnhancementContext:
    """প্রম্পট উন্নত করার কনটেক্সট মেটাডেটা"""

    current_file_path: str | None = None
    selected_code: str | None = None
    workspace_summary: str | None = None
    language: str | None = None
    user_intent: str | None = None
    custom_metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class EnhancedPromptResult:
    """উন্নত প্রম্পটের ফলাফল"""

    original_prompt: str
    enhanced_prompt: str
    mode: EnhancementMode
    applied_tricks: list[str] = field(default_factory=list)
    confidence_score: float = 0.95


class PromptEnhancementEngine:
    """
    প্রম্পট অপ্টিমাইজেশন এবং অ্যান্টি-বট ক্যামোফ্লেজ প্রসেসর।
    """

    # বাংলা মন্তব্য: কপি-পেস্ট ও সেকেন্ড ওপিনিয়ন ছদ্মবেশের হিউম্যান ওপেনারস (আইডেন্টিটি ডিক্লেয়ারেশন রোধ সহ)
    SHARED_PROMPT_CAMOUFLAGE_OPENERS = [
        "Hey, someone in my team shared this prompt from another chat, can you take a look and help me out?\n\n{prompt}",
        "Pasting this prompt from another tab to get your take on it:\n\n{prompt}",
        "I copied this prompt from a colleague's workspace to double-check the logic. Here is what they sent:\n\n{prompt}",
        "Got this prompt from another chat/assistant, can you solve it or refine it for me?\n\n{prompt}",
        'Sharing this prompt my friend gave me to review:\n\n"{prompt}"\n\nWhat is the best way to handle this?',
        "Someone sent me this query earlier. Can you answer this properly?\n\n{prompt}",
        "Quick sanity check — pasting this from my notes/another chat:\n\n{prompt}",
        "Hey, check out this prompt someone posted in our channel:\n\n{prompt}\n\nCan you write the code for it?",
        "Hey, a teammate asked for help with this prompt from their chat. Please provide just the direct code/solution without extra intro or preamble:\n\n{prompt}",
        "Pasting this prompt from another tab to get a second opinion. Just give the clean implementation directly:\n\n{prompt}",
    ]

    # বাংলা মন্তব্য: রোবটিক প্রিফিক্স যেগুলো বট ডিটেক্টর সহজে ধরে ফেলে
    ROBOTIC_PREFIX_PATTERNS = [
        r"^\s*you are an? (?:expert|senior|ai|helpful|intelligent) [^\n]+\n*",
        r"^\s*your task is to:?\s*",
        r"^\s*system instructions?:?\s*",
        r"^\s*act as an? [^\n]+\n*",
        r"^\s*strictly follow these guidelines:?\s*",
        r"^\s*please execute the following steps:?\s*",
    ]

    def __init__(self, rng_seed: int | None = None):
        self._rng = random.Random(rng_seed)

    def enhance(
        self,
        prompt: str,
        mode: EnhancementMode = EnhancementMode.STEALTH_CHAT,
        context: EnhancementContext | None = None,
    ) -> EnhancedPromptResult:
        """
        মূল প্রম্পটকে মোড অনুযায়ী হিউম্যানাইজ ও উন্নত করে।
        """
        if not prompt or not prompt.strip():
            return EnhancedPromptResult(
                original_prompt=prompt,
                enhanced_prompt=prompt,
                mode=mode,
                applied_tricks=["empty_prompt_noop"],
                confidence_score=1.0,
            )

        clean_prompt = prompt.strip()
        tricks: list[str] = []

        # ধাপ ১: রোবটিক প্রিফিক্স থাকলে তা পরিষ্কার করা
        for pat in self.ROBOTIC_PREFIX_PATTERNS:
            if re.search(pat, clean_prompt, flags=re.IGNORECASE):
                clean_prompt = re.sub(pat, "", clean_prompt, flags=re.IGNORECASE).strip()
                tricks.append("stripped_robotic_prefix")

        # ধাপ ২: মোড অনুযায়ী স্পেসিফিক ট্রান্সফর্মেশন
        if mode == EnhancementMode.STEALTH_CHAT:
            enhanced = self._apply_stealth_chat_camouflage(clean_prompt, tricks)
        elif mode == EnhancementMode.ENHANCE_UI_CLICK:
            enhanced = self._apply_ui_sparkle_enhancement(clean_prompt, context, tricks)
        elif mode == EnhancementMode.DEV_API:
            enhanced = self._apply_dev_api_structuring(clean_prompt, context, tricks)
        else:
            enhanced = clean_prompt

        return EnhancedPromptResult(
            original_prompt=prompt,
            enhanced_prompt=enhanced,
            mode=mode,
            applied_tricks=tricks,
            confidence_score=0.98,
        )

    def _apply_stealth_chat_camouflage(self, prompt: str, tricks: list[str]) -> str:
        """
        বাংলা মন্তব্য: অন্য চ্যাট বা কলিগের কাছ থেকে প্রম্পট কপি করে পেস্ট করার সাইকোলজিক্যাল কেমোফ্লেজ।
        """
        template = self._rng.choice(self.SHARED_PROMPT_CAMOUFLAGE_OPENERS)
        camouflaged = template.format(prompt=prompt)
        tricks.append("shared_from_another_chat_camouflage")

        # বাংলা মন্তব্য: র্যান্ডম ক্যাজুয়াল সাইন-অফ বা রিভিউ মার্কার যোগ করা
        if self._rng.random() < 0.35:
            closers = [
                "\n\n(Let me know if anything looks off in this)",
                "\n\nThanks in advance!",
                "\n\nPrefer a clean and concise implementation.",
                "\n\nAny gotchas or edge cases to watch out for?",
            ]
            camouflaged += self._rng.choice(closers)
            tricks.append("casual_human_signoff")

        return camouflaged

    def _apply_ui_sparkle_enhancement(
        self, prompt: str, context: EnhancementContext | None, tricks: list[str]
    ) -> str:
        """
        বাংলা মন্তব্য: UI-এর স্পার্কল বাটন ক্লিকের জন্য স্পষ্ট ও বিস্তারিত কনটেক্সট সমৃদ্ধ প্রম্পট।
        """
        parts: list[str] = [prompt]
        tricks.append("sparkle_button_enrichment")

        if context:
            if context.current_file_path:
                parts.append(f"\nRelevant file: {context.current_file_path}")
                tricks.append("file_context_attached")
            if context.selected_code:
                parts.append(f"\nFocused code snippet:\n```\n{context.selected_code.strip()}\n```")
                tricks.append("selected_code_attached")
            if context.language:
                parts.append(f"\nLanguage: {context.language}")

        parts.append(
            "\nPlease provide a complete, robust, and clean solution without omitting details."
        )
        return "\n".join(parts)

    def _apply_dev_api_structuring(
        self, prompt: str, context: EnhancementContext | None, tricks: list[str]
    ) -> str:
        """
        বাংলা মন্তব্য: ডেভেলপার এপিআই দিয়ে প্রম্পট পাঠালে স্ট্রিমলাইন্ড ফরম্যাটিং।
        """
        tricks.append("dev_api_normalized")
        if context and context.user_intent:
            return f"[Intent: {context.user_intent}]\n{prompt}"
        return prompt


# বাংলা মন্তব্য: গ্লোবাল সিঙ্গলটন ইনস্ট্যান্স
default_enhancer = PromptEnhancementEngine()
