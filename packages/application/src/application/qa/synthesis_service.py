from datetime import UTC, datetime

from domain.questions import Citation, QuestionAnswer
from domain.synthesis_outcome import SynthesisDraft
from domain.synthesis_validation import detect_citation_conflicts, validate_claim_citations

from application.ports.qa import AnswerSynthesizer


class AnswerSynthesisService:
    """Phase G — LangGraph synthesis with citation validation and conflict reporting."""

    def __init__(self, *, use_graph: bool = True) -> None:
        self._use_graph = use_graph

    async def synthesize(
        self,
        question: str,
        citations: list[Citation],
        *,
        synthesizer: AnswerSynthesizer,
    ) -> QuestionAnswer:
        if self._use_graph:
            return await self._synthesize_via_graph(question, citations, synthesizer=synthesizer)
        return await self._synthesize_deterministic(question, citations, synthesizer=synthesizer)

    async def _synthesize_via_graph(
        self,
        question: str,
        citations: list[Citation],
        *,
        synthesizer: AnswerSynthesizer,
    ) -> QuestionAnswer:
        from agents.synthesis.graph import build_synthesis_graph

        async def synthesize_draft(
            draft_question: str,
            context_package: dict[str, str],
            context_citations: list[Citation],
        ) -> SynthesisDraft:
            answer = await synthesizer.synthesize(draft_question, context_citations)
            return SynthesisDraft(
                answer=answer.answer,
                confidence=answer.confidence,
                insufficient_evidence=answer.insufficient_evidence,
                claims=answer.claims,
                warnings=list(answer.warnings),
                conflicts=list(answer.conflicts),
                model=answer.model,
            )

        graph = build_synthesis_graph(synthesize_draft=synthesize_draft)
        final = await graph.ainvoke({"question": question, "citations": citations})
        now = datetime.now(UTC)
        return QuestionAnswer(
            question=question,
            answer=str(final.get("answer", "")),
            confidence=float(final.get("confidence", 0.0)),
            insufficient_evidence=bool(final.get("insufficient_evidence", False)),
            citations=citations,
            claims=list(final.get("claims", [])),
            warnings=list(final.get("warnings", [])),
            conflicts=list(final.get("conflicts", [])),
            model=final.get("model"),
            created_at=now,
        )

    async def _synthesize_deterministic(
        self,
        question: str,
        citations: list[Citation],
        *,
        synthesizer: AnswerSynthesizer,
    ) -> QuestionAnswer:
        answer = await synthesizer.synthesize(question, citations)
        allowed = {citation.citation_id for citation in citations}
        validated_claims, warnings = validate_claim_citations(answer.claims, allowed)
        conflicts = list(dict.fromkeys([*answer.conflicts, *detect_citation_conflicts(citations)]))
        answer.claims = validated_claims
        answer.warnings = list(dict.fromkeys([*answer.warnings, *warnings]))
        answer.conflicts = conflicts
        return answer
