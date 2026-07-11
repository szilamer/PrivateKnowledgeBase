from domain.triage import (
    TriageSensitivity,
    classify_version_metadata,
    triage_floor_risk,
    triage_requires_review,
)


def test_classify_markdown_high_relevance() -> None:
    result = classify_version_metadata(
        external_id="docs/readme.md",
        mime_type="text/markdown",
    )
    assert result.extractor_hint == "markdown"
    assert result.relevance >= 0.9
    assert result.sensitivity == TriageSensitivity.LOW
    assert result.review_risk == "low"


def test_classify_sensitive_path_high_sensitivity() -> None:
    result = classify_version_metadata(
        external_id="config/.env.production",
        mime_type=None,
    )
    assert result.sensitivity == TriageSensitivity.HIGH
    assert result.review_risk == "high"


def test_triage_policy_flags_high_sensitivity() -> None:
    metadata = {"sensitivity": "high", "review_risk": "high"}
    assert triage_requires_review(metadata) is True
    assert triage_floor_risk("low", metadata) == "high"
