from dataclasses import dataclass

from domain.questions import AnswerClaim

SYNTHESIS_PIPELINE_VERSION = "v1"


@dataclass(frozen=True)
class SynthesisDraft:
    """Raw synthesis output before citation validation."""

    answer: str
    confidence: float
    insufficient_evidence: bool
    claims: list[AnswerClaim]
    warnings: list[str]
    conflicts: list[str]
    model: str | None = None
