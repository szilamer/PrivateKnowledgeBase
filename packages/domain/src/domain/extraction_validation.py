"""Schema validation gate for extraction agent outputs (doc 15 Phase A-2)."""

from domain.extraction import (
    EXTRACTION_SCHEMA_VERSION,
    ExtractionResult,
)


def validate_extraction_result(result: ExtractionResult) -> tuple[bool, list[str]]:
    """Return (passed, errors). Pydantic construction is assumed; this adds semantic checks."""
    errors: list[str] = []

    if result.schema_version != EXTRACTION_SCHEMA_VERSION:
        errors.append(
            f"unsupported schema_version: {result.schema_version} "
            f"(expected {EXTRACTION_SCHEMA_VERSION})"
        )

    local_ids: set[str] = set()
    for collection_name, items in (
        ("entities", result.entities),
        ("claims", result.claims),
        ("relationships", result.relationships),
        ("tasks", result.tasks),
        ("decisions", result.decisions),
        ("events", result.events),
    ):
        for item in items:
            local_id = getattr(item, "local_id", None)
            if not local_id or not str(local_id).strip():
                errors.append(f"{collection_name}: missing local_id")
                continue
            if local_id in local_ids:
                errors.append(f"duplicate local_id: {local_id}")
            local_ids.add(str(local_id))

    for claim in result.claims:
        if claim.subject_local_id and claim.subject_local_id not in local_ids:
            errors.append(
                f"claim {claim.local_id} references unknown subject {claim.subject_local_id}"
            )

    for relationship in result.relationships:
        if relationship.source_local_id not in local_ids:
            errors.append(
                f"relationship {relationship.local_id} references unknown source "
                f"{relationship.source_local_id}"
            )
        if relationship.target_local_id not in local_ids:
            errors.append(
                f"relationship {relationship.local_id} references unknown target "
                f"{relationship.target_local_id}"
            )

    return len(errors) == 0, errors
