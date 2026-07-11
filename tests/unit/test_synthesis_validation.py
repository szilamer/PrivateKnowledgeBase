from domain.questions import AnswerClaim, Citation, RetrievalSignal
from domain.synthesis_validation import (
    detect_citation_conflicts,
    validate_claim_citations,
)


def test_validate_claim_citations_rejects_invented_ids() -> None:
    claims = [
        AnswerClaim(
            text="PostgreSQL is used.",
            confidence=0.9,
            citation_ids=["chunk-real", "chunk-invented"],
        )
    ]
    validated, warnings = validate_claim_citations(claims, {"chunk-real"})
    assert len(validated) == 1
    assert validated[0].citation_ids == ["chunk-real"]
    assert any("chunk-invented" in warning for warning in warnings)


def test_validate_claim_citations_drops_claim_without_valid_ids() -> None:
    claims = [
        AnswerClaim(
            text="Unsupported statement.",
            confidence=0.8,
            citation_ids=["missing-id"],
        )
    ]
    validated, warnings = validate_claim_citations(claims, {"chunk-real"})
    assert validated == []
    assert warnings


def test_detect_citation_conflicts_finds_predicate_mismatch() -> None:
    citations = [
        Citation(
            citation_id="claim-1",
            excerpt="uses_technology: MySQL",
            signal=RetrievalSignal.CANONICAL,
        ),
        Citation(
            citation_id="claim-2",
            excerpt="uses_technology: PostgreSQL",
            signal=RetrievalSignal.CANONICAL,
        ),
    ]
    conflicts = detect_citation_conflicts(citations)
    assert len(conflicts) == 1
    assert "MySQL" in conflicts[0]
    assert "PostgreSQL" in conflicts[0]
