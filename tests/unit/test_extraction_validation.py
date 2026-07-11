from domain.entities import EntityType
from domain.extraction import (
    EXTRACTION_SCHEMA_VERSION,
    ExtractedEntity,
    ExtractedTask,
    ExtractionResult,
)
from domain.extraction_validation import validate_extraction_result


def test_validate_accepts_well_formed_result() -> None:
    result = ExtractionResult(
        schema_version=EXTRACTION_SCHEMA_VERSION,
        entities=[
            ExtractedEntity(
                local_id="e1",
                name="PostgreSQL",
                entity_type=EntityType.TECHNOLOGY,
                confidence=0.9,
            )
        ],
        tasks=[
            ExtractedTask(
                local_id="t1",
                title="Ship feature",
                confidence=0.8,
            )
        ],
    )
    passed, errors = validate_extraction_result(result)
    assert passed is True
    assert errors == []


def test_validate_rejects_duplicate_local_ids() -> None:
    result = ExtractionResult(
        entities=[
            ExtractedEntity(
                local_id="dup",
                name="A",
                entity_type=EntityType.CONCEPT,
                confidence=0.7,
            ),
            ExtractedEntity(
                local_id="dup",
                name="B",
                entity_type=EntityType.CONCEPT,
                confidence=0.7,
            ),
        ],
    )
    passed, errors = validate_extraction_result(result)
    assert passed is False
    assert any("duplicate" in err for err in errors)


def test_validate_rejects_wrong_schema_version() -> None:
    result = ExtractionResult(schema_version="9.9.9")
    passed, errors = validate_extraction_result(result)
    assert passed is False
    assert any("schema_version" in err for err in errors)
