# backend/skills/core_knowledge_qa.py
import logging
import os
from typing import Any

from google import genai
from google.genai import types

from core.resilience.circuit_breaker import CircuitBreaker
from core.resilience.circuit_breaker import CircuitBreakerOpenError


logger = logging.getLogger("supremeai.skills.knowledge_qa")

# বাংলা মন্তব্য: গ্লোবাল Gemini Circuit Breaker — ৫ বার ফেইল হলে OPEN, 60স পর HALF_OPEN
_gemini_qa_breaker: CircuitBreaker = CircuitBreaker(
    name="gemini_knowledge_qa",
    failure_threshold=5,
    recovery_timeout=60,
)


def _mock_vector_search(query: str, namespace: str) -> list[dict[str, Any]]:
    """Supabase Vector RPC এর মক রিট্রিভাল লেয়ার।"""
    database_mock = {
        "public_sops": [
            {
                "id": "doc_01",
                "content": "SupremeAI office timing is from 9:00 AM to 6:00 PM, Sunday to Thursday.",
                "source": "Employee Handbook 2026 v1",
            },
            {"id": "doc_02", "content": "Remote work is permitted on Wednesdays with manager approval.", "source": "Remote Work Policy v2"},
        ],
        "company_financials": [
            {"id": "fin_99", "content": "SupremeAI Q1 2026 net profit margin increased by 14.2%.", "source": "Q1 Board Memo Private"}
        ],
    }
    return database_mock.get(namespace, [])


def execute_tool(payload: dict) -> dict:
    """Strict Supreme Tool Contract for Permission-aware RAG with Citations"""
    try:
        user_role = payload.get("user_role", "Standard_User")
        query = payload.get("query", "").strip()

        if not query:
            return {"success": False, "error": "Query content cannot be empty."}

        role_permissions = {"Admin": ["company_financials", "public_sops"], "Manager": ["public_sops"], "Standard_User": ["public_sops"]}

        allowed_namespaces = role_permissions.get(user_role, ["public_sops"])

        retrieved_chunks = []
        for namespace in allowed_namespaces:
            chunks = _mock_vector_search(query, namespace)
            retrieved_chunks.extend(chunks)

        if not retrieved_chunks:
            return {"success": True, "result": {"answer": "I could not find any relevant documents you have permission to access.", "citations": []}}

        context_str = ""
        citations = []
        for idx, chunk in enumerate(retrieved_chunks, 1):
            context_str += f"[{idx}] Source: {chunk['source']}\nContent: {chunk['content']}\n\n"
            citations.append({"citation_id": idx, "source": chunk["source"], "doc_id": chunk["id"]})

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return {"success": False, "error": "Gemini API key is missing from environment."}

        client = genai.Client(api_key=api_key)

        system_instruction = """
        You are an enterprise knowledge-base assistant. Your task is to answer the user's question using ONLY the provided context.
        For every claim or factual statement you make, you MUST cite the source number using brackets like [1] or [2].
        If the answer cannot be found in the context, state that you do not know. Do not hallucinate.
        """

        user_prompt = f"""
        [Context Data]
        {context_str}

        [User Question]
        {query}
        """

        # বাংলা মন্তব্য: সার্কিট ব্রেকার দিয়ে Gemini API কল র্যাপ করা হতেছে
        # OPEN অবস্থায় CircuitBreakerOpenError থ্রো করে ফরোয়ার্ডিং ব্লক করে
        try:
            response = _gemini_qa_breaker.call(
                client.models.generate_content,
                model="gemini-2.5-flash",
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.2,
                ),
            )
        except CircuitBreakerOpenError as cb_exc:
            logger.warning(f"🚨 Gemini Circuit Breaker OPEN: {cb_exc}")
            return {
                "success": False,
                "error": "LLM infrastructure is temporarily unavailable. Circuit breaker active. Please retry in 60 seconds.",
            }

        return {"success": True, "result": {"answer": response.text.strip(), "citations": citations}}

    except Exception as e:
        logger.error(f"Failed inside core_knowledge_qa skill loop: {str(e)}")
        return {"success": False, "error": f"Skill execution anomaly: {str(e)}"}
