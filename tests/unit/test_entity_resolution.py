from uuid import uuid4

from domain.entities import EntityMatch, EntityType
from domain.entity_resolution import (
    build_entity_resolution_spec,
    merge_alias_lists,
    name_similarity,
    requires_review,
    resolve_entity,
)
from domain.extraction import ExtractedEntity
from domain.proposals import ProposalType


def test_name_similarity_exact_match() -> None:
    assert name_similarity("PostgreSQL", "postgresql") == 1.0


def test_name_similarity_partial_overlap() -> None:
    score = name_similarity("Knowledge Base", "Private Knowledge Base")
    assert score > 0.5


def test_merge_alias_lists_deduplicates_case_insensitive() -> None:
    merged = merge_alias_lists(["PostgreSQL"], ["postgresql", "Postgres"])
    assert merged == ["PostgreSQL", "Postgres"]


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


def test_resolve_entity_link_via_alias_candidate() -> None:
    entity = ExtractedEntity(
        local_id="e1",
        name="Postgres",
        entity_type=EntityType.TECHNOLOGY,
        confidence=0.85,
    )
    candidates = [
        EntityMatch(
            entity_id=uuid4(),
            canonical_name="PostgreSQL",
            entity_type=EntityType.TECHNOLOGY,
            score=0.9,
            match_reason="alias",
        )
    ]
    action, matches = resolve_entity(entity, candidates)
    assert action == "link"
    assert matches[0].match_reason == "alias"


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


def test_build_entity_resolution_spec_includes_ranked_candidates_for_ambiguous() -> None:
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
    spec = build_entity_resolution_spec(entity, "ambiguous", candidates)
    assert spec.proposal_type == ProposalType.ENTITY_RESOLUTION
    assert spec.needs_review is True
    assert len(spec.payload["candidates"]) == 2


def test_requires_review_merge_type_always_true() -> None:
    assert requires_review("low", ProposalType.MERGE.value, confidence=0.99) is True
