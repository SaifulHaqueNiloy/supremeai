"""Tests for services/knowledge_qa.py — Knowledge QA service."""
import pytest
from services.knowledge_qa import KnowledgeQA


class TestKnowledgeQA:
    def test_init(self):
        qa = KnowledgeQA()
        assert qa is not None

    @pytest.mark.asyncio
    async def test_ask_returns_answer(self):
        qa = KnowledgeQA()
        result = await qa.ask("What is SupremeAI?")
        assert result is not None
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_ask_empty_question(self):
        qa = KnowledgeQA()
        result = await qa.ask("")
        assert result is not None

    @pytest.mark.asyncio
    async def test_ask_bengali_question(self):
        qa = KnowledgeQA()
        result = await qa.ask("সুপ্রিমএআই কী?")
        assert result is not None
