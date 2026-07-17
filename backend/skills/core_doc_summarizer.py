# backend/skills/core_doc_summarizer.py
import os
import logging
from typing import Dict, Any
from google import genai
from google.genai import types

logger = logging.getLogger("supremeai.skills.doc_summarizer")

def execute_tool(payload: dict) -> dict:
    """Strict Supreme Tool Contract for Sandbox-isolated File Summarization"""
    try:
        # ১. ইনপুট স্যানিটাইজেশন
        file_content = payload.get("file_content", "").strip()
        summary_length = payload.get("summary_length", "concise")  # concise, detailed

        if not file_content:
            return {"success": False, "error": "Document content is empty or unreadable."}

        # ২. ডিফেন্সিভ সাইজ গার্ড (বাজেট এনফোর্সমেন্ট)
        # অতিরিক্ত বড় ফাইল হলে টোকেন কস্ট ও লেটেন্সি বাউন্ডারি ব্রেক করা রুখতে
        if len(file_content) > 100000:  # আনুমানিক ২৫,০০০ শব্দ
            return {"success": False, "error": "Document exceeds the maximum permissible payload for this skill."}

        # ৩. মডার্ন Gemini Client ইনিশিয়ালাইজেশন
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return {"success": False, "error": "Gemini API key configuration drift detected."}

        client = genai.Client(api_key=api_key)

        # ৪. কনটেক্সট স্পেসিফিক প্রম্পট ইঞ্জিনিয়ারিং
        system_instruction = (
            "You are an expert document intelligence agent operating in a secure corporate sandbox. "
            "Your task is to analyze the provided document content and extract a structured summary. "
            "Highlight the core objectives, key action items, and financial metrics if present. "
            "Maintain an objective corporate tone and do not extrapolate facts beyond the text."
        )

        user_prompt = f"""
        [Target Length: {summary_length.upper()}]
        
        [Document Source Content]
        {file_content}
        """

        # ৫. ২০২৬ স্টেবল ফ্ল্যাশ মডেল দিয়ে হাই-স্পিড ইনফারেন্স
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.3,  # অ্যানালিটিক্যাল কনসিস্টেন্সির জন্য অপ্টিমাইজড
            )
        )

        return {
            "success": True,
            "result": {
                "summary": response.text.strip(),
                "extracted_bytes_processed": len(file_content.encode("utf-8")),
                "model_enforced": "gemini-2.5-flash"
            }
        }

    except Exception as e:
        logger.error(f"Critical execution barrier inside core_doc_summarizer: {str(e)}")
        return {"success": False, "error": f"File analysis exception: {str(e)}"}
