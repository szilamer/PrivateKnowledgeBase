from dataclasses import dataclass

from domain.extraction import ExtractionResult


@dataclass(frozen=True)
class ExtractionLLMResult:
    """Structured LLM extraction response including provider metadata."""

    result: ExtractionResult
    token_usage: dict[str, object] | None = None


@dataclass(frozen=True)
class ExtractionOutcome:
    """Result of an extraction attempt with provider trace for audit and runs."""

    result: ExtractionResult
    provider: str
    fallback_used: bool
    token_usage: dict[str, object] | None = None
    llm_error: str | None = None
