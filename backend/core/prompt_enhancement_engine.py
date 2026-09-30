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
    STEALTH_CHAT = "stealth_chat"  # বাংলা মন্তব্য: ডিরেক্ট অর্গানিক হিউম্যান প্রম্পট ফ্লো
    DUAL_AI_CONDUCTOR = "dual_ai_conductor"  # বাংলা মন্তব্য: ২টা এআই নিয়ে মানুষের কাজ করার অটোনোমাস ফ্রেমওয়ার্ক ("Copy this to your AI:")


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

    # বাংলা মন্তব্য: মেটা-ডিরেক্টিভ প্যাটার্ন (বাইরের প্রম্পট জেনারেটর বা টেমপ্লেটের লিক হওয়া টেক্সট)
    META_DIRECTIVE_PATTERNS = [
        r"^\s*(?:please\s+)?copy\s+(?:and\s+paste\s+)?this\s+(?:prompt\s+)?(?:in|into|to)\s+(?:your\s+)?(?:ai(?:'s)?|assistant|chat|desired\s+ai(?:'s)?)[^:\n]*[:\n-]*\s*",
        r"^\s*(?:please\s+)?share\s+this\s+(?:prompt\s+)?(?:with|in)\s+(?:your\s+)?(?:ai(?:'s)?|assistant|chat)[^:\n]*[:\n-]*\s*",
        r"^\s*(?:prompt\s+to\s+copy|copy\s+the\s+following|paste\s+this\s+below)\s*[:\n-]+\s*",
        r"^\s*prompt\s+for\s+(?:the\s+)?(?:ai|assistant|model)[:\s-]*\s*",
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

        # বাংলা মন্তব্য: যদি DUAL_AI_CONDUCTOR মোড হয় বা প্রম্পটে অলরেডি অটোনোমাস ব্লুপ্রিন্ট থাকে, তা পূর্ণ শক্তিতে অক্ষুণ্ণ রাখা
        if mode != EnhancementMode.DUAL_AI_CONDUCTOR and not (
            "copy this to your ai" in clean_prompt.lower()
            or "autonomous execution agent" in clean_prompt.lower()
        ):
            # ধাপ ১: অপ্রাসঙ্গিক মেটা-লিক ফিল্টার
            for pat in self.META_DIRECTIVE_PATTERNS:
                if re.search(pat, clean_prompt, flags=re.IGNORECASE | re.MULTILINE):
                    clean_prompt = re.sub(
                        pat, "", clean_prompt, flags=re.IGNORECASE | re.MULTILINE
                    ).strip()
                    tricks.append("stripped_meta_generator_watermarks")

            # ধাপ ২: রোবটিক প্রিফিক্স থাকলে তা পরিষ্কার করা
            for pat in self.ROBOTIC_PREFIX_PATTERNS:
                if re.search(pat, clean_prompt, flags=re.IGNORECASE):
                    clean_prompt = re.sub(pat, "", clean_prompt, flags=re.IGNORECASE).strip()
                    tricks.append("stripped_robotic_prefix")

        # ধাপ ৩: মোড অনুযায়ী স্পেসিফিক ট্রান্সফর্মেশন
        if mode == EnhancementMode.DUAL_AI_CONDUCTOR:
            enhanced = self._apply_dual_ai_conductor(clean_prompt, context, tricks)
        elif mode == EnhancementMode.STEALTH_CHAT:
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

    AUTONOMOUS_EXECUTION_TEMPLATE = (
        "Copy this to your AI:\n\n"
        "You are an Autonomous Execution Agent. Your primary objective is to execute "
        "the assigned task completely from start to finish without stopping, asking for "
        "mid-task approvals, or handing off partial work.\n\n"
        "### CORE OPERATIONAL DIRECTIVES\n\n"
        "1. TASK BREAKDOWN & SCRATCHPAD\n"
        "- Before taking action, break down the goal into a structured step-by-step execution plan.\n"
        "- Maintain a running checklist of completed vs. remaining steps.\n\n"
        "2. UNINTERRUPTED EXECUTION LOOP\n"
        '- Execute all steps sequentially without pausing to ask "Should I proceed?" or "Would you like me to continue?".\n'
        "- Keep executing actions sequentially until the entire task is 100% complete.\n\n"
        "3. AUTONOMOUS ERROR RECOVERY & SELF-HEALING\n"
        "- If an error, failure, or unexpected result occurs: DO NOT STOP.\n"
        "- Analyze the error, adjust your approach, modify code/commands, and try alternative solutions independently.\n"
        "- Exhaust at least 3 distinct troubleshooting strategies before considering a task blocked.\n"
        "- Only halt and prompt the user if you hit a fatal external blocker (e.g., missing API credentials, permission denied requiring human auth).\n\n"
        "4. VERIFICATION & DEFINITION OF DONE\n"
        "- Do not mark a step or task as complete based on assumptions. Verify results directly (e.g., run tests, inspect output files, verify API responses).\n"
        "- The task is ONLY complete when all requirements in the prompt are fulfilled and verified working.\n\n"
        "5. FINAL DELIVERABLE\n"
        "- Once (and only once) all steps are completed and verified, summarize the actions taken and deliver the final result.\n\n"
        "TASK TO EXECUTE:\n"
        "{task}"
    )

    def _apply_dual_ai_conductor(
        self, prompt: str, context: EnhancementContext | None, tricks: list[str]
    ) -> str:
        """
        বাংলা সারসংক্ষেপ:
        ------------------
        ২টা এআই নিয়ে একজন মানুষের মাল্টি-এআই কাজের বাস্তবসম্মত ট্রিক (Dual AI Conductor):
        ১. 'Copy this to your AI:' দিয়ে শুরু হয় — যা ২য় এআই-র কাছে প্রমাণ করে এটা একজন মানুষের কপি-পেস্ট করা নির্দেশ।
        ২. একই সাথে Autonomous Execution Agent ফ্রেমওয়ার্ক যুক্ত থাকে — যাতে এআই মাঝপথে থেমে না গিয়ে পুরো কাজ শেষ করে।
        ৩. কোডিং বা ব্রাউজিং কনটেক্সট থাকলে নির্দিষ্ট এনভায়রনমেন্ট রুলস যুক্ত হয়।
        """
        tricks.append("dual_ai_conductor_proven_human")
        tricks.append("autonomous_execution_blueprint")

        result = self.AUTONOMOUS_EXECUTION_TEMPLATE.format(task=prompt)

        # এনভায়রনমেন্ট অ্যাডিশন (কোডিং বা টুল স্পেসিফিক রুলস)
        if context:
            if context.language or context.selected_code or context.current_file_path:
                result += (
                    "\n\n### ENVIRONMENT DIRECTIVE (Coding Agent):\n"
                    "When writing or modifying code, run unit tests or syntax checks after every edit. "
                    "If tests fail, fix the code immediately and re-run until all tests pass before moving to the next module."
                )
                tricks.append("coding_agent_env_directive")
            elif context.user_intent and "browse" in context.user_intent.lower():
                result += (
                    "\n\n### ENVIRONMENT DIRECTIVE (Tool/Browsing Agent):\n"
                    "If a page element, selector, or endpoint fails to load or returns an error, wait, retry, "
                    "or find alternative paths automatically. Do not report failure until all alternative options are exhausted."
                )
                tricks.append("browsing_agent_env_directive")

        return result

    def _apply_stealth_chat_camouflage(self, prompt: str, tricks: list[str]) -> str:
        """
        বাংলা সারসংক্ষেপ:
        ------------------
        ন্যাচারাল হিউম্যান প্রম্পট (Anti-Bot Organic Clean):
        ১. কোনো কৃত্রিম টেমপ্লেট প্রিফিক্স ('hey someone shared this...') যোগ করা সম্পূর্ণ নিষিদ্ধ,
           কারণ প্রতি মেসেজে একই টেমপ্লেট থাকলে এআই এটিকে ১০০% বট বলে চিহ্নিত করে।
        ২. বাইরের প্রম্পট জেনারেটর বা টুলের মেটা-ইনস্ট্রাকশন ('Copy this to your AI...') মুছে ফেলা।
        ৩. একজন সত্যিকারের ডেভেলপার যেভাবে সরাসরি টু-দ্য-পয়েন্ট চ্যাট করে, ঠিক সেই আসল প্রশ্ন বজায় রাখা।
        """
        tricks.append("organic_human_direct_flow")
        return prompt

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
