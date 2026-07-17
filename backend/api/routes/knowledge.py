#!/usr/bin/env python3
"""
API Endpoints for Knowledge Base Interaction.
"""

from fastapi import APIRouter
from fastapi import Depends
from pydantic import BaseModel

from api.dependencies import get_current_user_token


router = APIRouter()


class ScribeQuestion(BaseModel):
    """Request model for asking a question to the Scribe."""

    question: str


@router.post("/knowledge/ask-scribe", tags=["Knowledge Base"])
async def ask_the_scribe(
    request: ScribeQuestion,
    user: dict = Depends(get_current_user_token),  # Basic security
):
    """
    Asks a question to the AI Scribe about the codebase.
    The Scribe uses a RAG approach on the indexed documentation.
    """

    # বাংলা মন্তব্য: সার্ভার স্টার্টআপ ফেইলর এড়াতে রানটাইমে ডাইনামিকালি ইম্পোর্ট করা হচ্ছে
    from ask_scribe import answer_question
    answer = await answer_question(request.question)
    return {"answer": answer}
