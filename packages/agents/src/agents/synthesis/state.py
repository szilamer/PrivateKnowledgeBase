from typing import TypedDict

from domain.questions import AnswerClaim, Citation
from domain.synthesis_outcome import SynthesisDraft


class SynthesisState(TypedDict, total=False):
    question: str
    citations: list[Citation]
    context_package: dict[str, str]
    allowed_citation_ids: list[str]
    draft: SynthesisDraft
    answer: str
    confidence: float
    insufficient_evidence: bool
    claims: list[AnswerClaim]
    warnings: list[str]
    conflicts: list[str]
    model: str | None
    pipeline_version: str
    validation_passed: bool
    error: str | None
