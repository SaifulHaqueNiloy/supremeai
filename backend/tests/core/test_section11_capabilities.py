import pytest

from brain.research_harness import ResearchFinding, ResearchHarness
from core.llm.structured_output_router import StructuredOutputError, StructuredOutputRouter
from core.memory.auto_rag_injector import AutoRAGInjector, MemoryInjectionPolicy
from tools.knowledge.citation_store import CitationStore


def test_citation_store_is_tenant_scoped_and_validates_urls():
    store = CitationStore()
    store.add(tenant_id="a", claim_id="c1", url="https://example.com/source", confidence_score=2)
    assert len(store.for_claim(tenant_id="a", claim_id="c1")) == 1
    assert store.for_claim(tenant_id="b", claim_id="c1") == []
    with pytest.raises(ValueError):
        store.add(tenant_id="a", claim_id="c1", url="file:///secret")


def test_structured_output_router_rejects_invalid_output():
    router = StructuredOutputRouter(max_retries=1)
    assert router.parse("prefix {\"ok\": true}", lambda value: value)["ok"] is True
    with pytest.raises(StructuredOutputError):
        router.parse("not json", lambda value: value)


@pytest.mark.asyncio
async def test_research_harness_runs_bounded_scouts():
    async def scout(query):
        return [ResearchFinding(source="https://example.com", claim=query)]

    async def judge(query, findings):
        return f"{query}: {len(findings)} findings"

    result = await ResearchHarness(max_scouts=2).run("q", [scout, scout, scout], judge)
    assert result.scouts_completed == 2
    assert len(result.findings) == 2


def test_auto_rag_is_opt_in():
    class Retriever:
        def search(self, **kwargs):
            return ["approved fact"]

    injector = AutoRAGInjector(Retriever())
    assert injector.inject(tenant_id="t", prompt="hello", policy=MemoryInjectionPolicy()) == "hello"
    assert "approved fact" in injector.inject(tenant_id="t", prompt="hello", policy=MemoryInjectionPolicy(enabled=True))
