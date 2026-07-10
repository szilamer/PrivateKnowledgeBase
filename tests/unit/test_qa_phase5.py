import json
from pathlib import Path

import pytest
from adapters.llm.answer_synthesis import HeuristicAnswerSynthesizer, tokenize_query
from domain.questions import Citation, RetrievalSignal


def test_tokenize_query_filters_short_tokens() -> None:
    tokens = tokenize_query("What is the PKB project status?")
    assert "is" not in tokens
    assert "pkb" in tokens
    assert "project" in tokens


@pytest.mark.asyncio
async def test_heuristic_synthesizer_returns_citations() -> None:
    synthesizer = HeuristicAnswerSynthesizer()
    citations = [
        Citation(
            citation_id="chunk-1",
            excerpt="PostgreSQL stores canonical knowledge.",
            score=0.9,
            signal=RetrievalSignal.SEMANTIC,
        )
    ]
    answer = await synthesizer.synthesize("What database is used?", citations)
    assert answer.citations
    assert answer.claims
    assert "PostgreSQL" in answer.answer


def test_golden_questions_schema() -> None:
    path = Path(__file__).resolve().parents[1] / "evaluation" / "golden_questions.json"
    items = json.loads(path.read_text())
    assert len(items) >= 3
    for item in items:
        assert "id" in item
        assert "question" in item
        assert "expected_signals" in item
        assert isinstance(item["expected_signals"], list)
