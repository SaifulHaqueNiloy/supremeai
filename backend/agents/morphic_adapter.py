# backend/agents/morphic_adapter.py
import os
from typing import Dict, Any
import google.generativeai as genai

class MorphicAdapter:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-1.5-pro')
        else:
            self.model = None

    def _get_morphic_system_prompt(self) -> str:
        """মর্ফিক ইঞ্জিনের জন্য ওয়াটারটাইট প্রম্পট আর্কিটেকচার"""
        return """
        You are the Core Morphic Adaptation Engine of SupremeAI 2.0.
        Your sole task is to refactor arbitrary, raw Python code or MCP tools into a standardized Supreme Tool Contract.

        [STRICT CODE CONTRACT]
        1. The output MUST contain a single entry-point function exactly named: `execute_tool(payload: dict) -> dict:`
        2. All inner logic, variables, and helper functions must be self-contained within the code.
        3. The input `payload` will contain all necessary arguments passed as a dictionary.
        4. The function MUST return a dictionary containing the keys: 'success' (bool) and 'result' (any data) or 'error' (str).

        [SECURITY GUARDRAILS]
        - DO NOT import or use forbidden libraries: `os`, `subprocess`, `sys`, `requests`, `urllib`, `socket`.
        - If the raw code requires web scraping, network fetch, or system commands, wrap them into abstract logic or safely fail.
        - NEVER output markdown text, conversational explanations, or backticks (```python). Output ONLY clean, valid, executable Python code.
        """

    def adapt_code_to_contract(self, raw_code: str, skill_description: str) -> Dict[str, Any]:
        """কাঁচা পাইথন কোডকে এআই প্রম্পটের মাধ্যমে সুপ্রীম চুক্তিতে রি-রাইট করে"""
        if not self.model:
            return {"success": False, "code": "", "detail": "Gemini API Client is not configured in environment."}

        prompt = f"""
        Refactor the following raw code to fit the execute_tool(payload: dict) -> dict contract.

        [Skill Description]
        {skill_description}

        [Raw Source Code]
        {raw_code}
        """

        try:
            response = self.model.generate_content(
                contents=prompt,
                generation_config={"temperature": 0.1}, # Low temperature for strict structural code
            )

            adapted_code = response.text.strip()

            if adapted_code.startswith("```python"):
                adapted_code = adapted_code.split("```python")[1].split("```")[0].strip()
            elif adapted_code.startswith("```"):
                adapted_code = adapted_code.split("```")[1].split("```")[0].strip()

            return {
                "success": True,
                "code": adapted_code,
                "detail": "Morphic adaptation rewrite completed successfully."
            }
        except Exception as e:
            return {
                "success": False,
                "code": "",
                "detail": f"LLM Morphic adaptation failure: {str(e)}"
            }
