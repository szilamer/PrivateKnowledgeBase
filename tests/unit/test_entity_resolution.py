from uuid import uuid4

from domain.entities import EntityMatch, EntityType
from domain.entity_resolution import name_similarity, resolve_entity
from domain.extraction import ExtractedEntity


def test_name_similarity_exact_match() -> None:
    assert name_similarity("PostgreSQL", "postgresql") == 1.0


def test_name_similarity_partial_overlap() -> None:
    score = name_similarity("Knowledge Base", "Private Knowledge Base")
    assert score > 0.5


def test_resolve_entity_new_when_no_candidates() -> None:
    entity = ExtractedEntity(
        local_id="e1",
        name="New Concept",
        entity_type=EntityType.CONCEPT,
        confidence=0.8,
    )
    action, matches = resolve_entity(entity, [])
    assert action == "new"
    assert matches == []


def test_resolve_entity_link_high_confidence() -> None:
    entity = ExtractedEntity(
        local_id="e1",
        name="PostgreSQL",
        entity_type=EntityType.TECHNOLOGY,
        confidence=0.9,
    )
    candidates = [
        EntityMatch(
            entity_id=uuid4(),
            canonical_name="PostgreSQL",
            entity_type=EntityType.TECHNOLOGY,
            score=0.95,
            match_reason="exact",
        )
    ]
    action, matches = resolve_entity(entity, candidates)
    assert action == "link"
    assert len(matches) == 1


def test_resolve_entity_ambiguous_close_scores() -> None:
    entity = ExtractedEntity(
        local_id="e1",
        name="Atlas Project",
        entity_type=EntityType.PROJECT,
        confidence=0.7,
    )
    candidates = [
        EntityMatch(
            entity_id=uuid4(),
            canonical_name="Atlas",
            entity_type=EntityType.PROJECT,
            score=0.9,
            match_reason="alias",
        ),
        EntityMatch(
            entity_id=uuid4(),
            canonical_name="Atlas Initiative",
            entity_type=EntityType.PROJECT,
            score=0.88,
            match_reason="alias",
        ),
    ]
    action, matches = resolve_entity(entity, candidates)
    assert action == "ambiguous"
    assert len(matches) <= 3
