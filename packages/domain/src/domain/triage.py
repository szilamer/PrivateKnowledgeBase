from enum import StrEnum

from pydantic import BaseModel, Field

TRIAGE_PIPELINE_VERSION = "v1"

SENSITIVE_PATH_MARKERS = (
    ".env",
    "secret",
    "password",
    "credential",
    "token",
    "private",
    "ssh",
)


class TriageSensitivity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TriageClassification(BaseModel):
    project_hint: str | None = None
    sensitivity: TriageSensitivity = TriageSensitivity.LOW
    relevance: float = Field(ge=0.0, le=1.0, default=0.5)
    extractor_hint: str = "structured"
    review_risk: str = "medium"


def classify_version_metadata(
    *,
    external_id: str,
    mime_type: str | None,
    source_configuration: dict[str, object] | None = None,
) -> TriageClassification:
    """Deterministic triage scoring for ingestion priority (Phase B, ADR-006)."""
    lowered = external_id.lower()
    extension = lowered.rsplit(".", 1)[-1] if "." in lowered else ""
    extractor_hint = (
        "markdown"
        if extension in {"md", "markdown"}
        else "text"
        if extension == "txt"
        else "pdf"
        if extension == "pdf"
        else "structured"
    )
    if mime_type and "markdown" in mime_type:
        extractor_hint = "markdown"
    elif mime_type and mime_type.startswith("text/"):
        extractor_hint = "text"

    sensitivity = TriageSensitivity.LOW
    sensitive_extension = extension in {"key", "pem", "p12", "pfx"}
    if any(marker in lowered for marker in SENSITIVE_PATH_MARKERS) or sensitive_extension:
        sensitivity = TriageSensitivity.HIGH

    relevance = 0.55
    if extension in {"md", "txt", "markdown"}:
        relevance = 0.92
    elif extension in {"pdf", "rst"}:
        relevance = 0.7
    elif extension in {"json", "yaml", "yml", "toml"}:
        relevance = 0.65

    review_risk = "medium"
    if sensitivity == TriageSensitivity.HIGH:
        review_risk = "high"
    elif relevance >= 0.85 and sensitivity == TriageSensitivity.LOW:
        review_risk = "low"

    config = source_configuration or {}
    project_hint = None
    for key in ("default_project", "project_hint", "project"):
        if config.get(key):
            project_hint = str(config[key])
            break

    return TriageClassification(
        project_hint=project_hint,
        sensitivity=sensitivity,
        relevance=relevance,
        extractor_hint=extractor_hint,
        review_risk=review_risk,
    )


def triage_requires_review(triage_metadata: dict[str, object]) -> bool:
    return triage_metadata.get("sensitivity") == TriageSensitivity.HIGH.value or (
        triage_metadata.get("review_risk") == "high"
    )


def triage_floor_risk(risk: str, triage_metadata: dict[str, object]) -> str:
    if triage_metadata.get("sensitivity") == TriageSensitivity.HIGH.value:
        return "high"
    if triage_metadata.get("review_risk") == "high" and risk == "low":
        return "medium"
    return risk
