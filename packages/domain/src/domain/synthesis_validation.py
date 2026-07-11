from domain.questions import AnswerClaim, Citation, RetrievalSignal


def validate_claim_citations(
    claims: list[AnswerClaim],
    allowed_ids: set[str],
) -> tuple[list[AnswerClaim], list[str]]:
    """Hallucination guard — keep only citation IDs present in the context package."""
    warnings: list[str] = []
    validated: list[AnswerClaim] = []
    for claim in claims:
        valid_ids = [cid for cid in claim.citation_ids if cid in allowed_ids]
        invalid = [cid for cid in claim.citation_ids if cid not in allowed_ids]
        if invalid:
            warnings.append(f"Eltávolított érvénytelen hivatkozás-azonosítók: {', '.join(invalid)}")
        if valid_ids:
            validated.append(claim.model_copy(update={"citation_ids": valid_ids}))
        elif claim.text.strip():
            warnings.append(
                f"Nem támasztható állítás elvetve (nincs érvényes forrás): {claim.text[:80]}"
            )
    return validated, warnings


def detect_citation_conflicts(citations: list[Citation]) -> list[str]:
    """Surface contradictory canonical claim excerpts in the context package."""
    by_predicate: dict[str, set[str]] = {}
    for citation in citations:
        if citation.signal != RetrievalSignal.CANONICAL:
            continue
        if ": " not in citation.excerpt:
            continue
        predicate, value = citation.excerpt.split(": ", 1)
        by_predicate.setdefault(predicate.strip().lower(), set()).add(value.strip())
    conflicts: list[str] = []
    for predicate, values in by_predicate.items():
        if len(values) > 1:
            joined = " vs ".join(sorted(values))
            conflicts.append(f"Ellentmondó bizonyíték a(z) '{predicate}' predikátumra: {joined}")
    return conflicts
