from uuid import UUID, uuid4

import pytest
from agents.entity_resolution.graph import build_entity_resolution_graph
from domain.entities import EntityMatch, EntityType
from domain.extraction import ExtractedEntity
from domain.proposals import ProposalType


@pytest.mark.asyncio
async def test_entity_resolution_graph_ambiguous_with_candidates() -> None:
    owner_id = uuid4()
    entity = ExtractedEntity(
        local_id="e1",
        name="Atlas Project",
        entity_type=EntityType.PROJECT,
        confidence=0.7,
    )
    candidate_a = EntityMatch(
        entity_id=uuid4(),
        canonical_name="Atlas",
        entity_type=EntityType.PROJECT,
        score=0.9,
        match_reason="alias",
    )
    candidate_b = EntityMatch(
        entity_id=uuid4(),
        canonical_name="Atlas Initiative",
        entity_type=EntityType.PROJECT,
        score=0.88,
        match_reason="alias",
    )

    async def find_matches(
        requested_owner: UUID,
        name: str,
        entity_type: str,
        *,
        limit: int = 5,
    ) -> list[EntityMatch]:
        assert requested_owner == owner_id
        assert name == entity.name
        assert entity_type == entity.entity_type.value
        return [candidate_a, candidate_b]

    graph = build_entity_resolution_graph(find_matches=find_matches)
    final = await graph.ainvoke({"entity": entity, "owner_id": owner_id})

    assert final["resolution_action"] == "ambiguous"
    assert final["proposal_type"] == ProposalType.ENTITY_RESOLUTION.value
    assert final["needs_review"] is True
    candidates = final["payload"]["candidates"]
    assert isinstance(candidates, list)
    assert len(candidates) == 2


@pytest.mark.asyncio
async def test_entity_resolution_graph_link_action() -> None:
    owner_id = uuid4()
    entity = ExtractedEntity(
        local_id="e1",
        name="PostgreSQL",
        entity_type=EntityType.TECHNOLOGY,
        confidence=0.9,
    )
    resolved_id = uuid4()

    async def find_matches(
        _owner: UUID,
        _name: str,
        _entity_type: str,
        *,
        limit: int = 5,
    ) -> list[EntityMatch]:
        return [
            EntityMatch(
                entity_id=resolved_id,
                canonical_name="PostgreSQL",
                entity_type=EntityType.TECHNOLOGY,
                score=0.95,
                match_reason="exact",
            )
        ]

    graph = build_entity_resolution_graph(find_matches=find_matches)
    final = await graph.ainvoke({"entity": entity, "owner_id": owner_id})

    assert final["resolution_action"] == "link"
    assert final["proposal_type"] == ProposalType.ENTITY.value
    assert final["payload"]["resolved_entity_id"] == str(resolved_id)
