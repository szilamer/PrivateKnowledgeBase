import pytest
from agents.synthesis.graph import build_synthesis_graph
from domain.questions import AnswerClaim, Citation, RetrievalSignal
from domain.synthesis_outcome import SynthesisDraft


@pytest.mark.asyncio
async def test_synthesis_graph_strips_invented_citation_ids() -> None:
    citations = [
        Citation(
            citation_id="chunk-1",
            excerpt="PostgreSQL stores canonical knowledge.",
            score=0.9,
            signal=RetrievalSignal.SEMANTIC,
        )
    ]

    async def synthesize_draft(
        question: str,
        context_package: dict[str, str],
        context_citations: list[Citation],
    ) -> SynthesisDraft:
        assert question == "What database is used?"
        assert "chunk-1" in context_package
        return SynthesisDraft(
            answer="PostgreSQL is used.",
            confidence=0.85,
            insufficient_evidence=False,
            claims=[
                AnswerClaim(
                    text="PostgreSQL is used.",
                    confidence=0.85,
                    citation_ids=["chunk-1", "chunk-fake"],
                )
            ],
            warnings=[],
            conflicts=[],
            model="test",
        )

    graph = build_synthesis_graph(synthesize_draft=synthesize_draft)
    final = await graph.ainvoke({"question": "What database is used?", "citations": citations})

    claims = final.get("claims", [])
    assert len(claims) == 1
    assert claims[0].citation_ids == ["chunk-1"]
    warnings = final.get("warnings", [])
    assert any("chunk-fake" in warning for warning in warnings)
    assert final.get("validation_passed") is True
