from uuid import uuid4

import pytest
from agents.ontology.graph import build_ontology_curator_graph
from domain.ontology_proposals import (
    OntologyProposal,
    OntologyProposalKind,
    OntologyProposalStatus,
    UnmappedEntityCandidate,
    UnmappedRelationshipCandidate,
)


@pytest.mark.asyncio
async def test_ontology_curator_graph_proposes_unmapped_entity_type() -> None:
    owner_id = uuid4()
    candidate = UnmappedEntityCandidate(
        name="Atlas",
        entity_type="project",
        occurrence_count=5,
        sample_proposal_ids=["p1", "p2"],
    )

    async def load_entities(requested_owner: object) -> list[UnmappedEntityCandidate]:
        assert requested_owner == owner_id
        return [candidate]

    async def load_relationships(requested_owner: object) -> list[UnmappedRelationshipCandidate]:
        _ = requested_owner
        return []

    saved: list[OntologyProposal] = []

    async def persist(
        requested_owner: object,
        proposals: list[OntologyProposal],
    ) -> list[OntologyProposal]:
        assert requested_owner == owner_id
        saved.extend(proposals)
        return proposals

    graph = build_ontology_curator_graph(
        load_unmapped_entities=load_entities,
        load_unmapped_relationships=load_relationships,
        persist_proposals=persist,
    )
    final = await graph.ainvoke({"owner_id": owner_id})

    assert len(saved) == 1
    proposal = saved[0]
    assert proposal.kind == OntologyProposalKind.ENTITY_TYPE
    assert proposal.status == OntologyProposalStatus.PENDING
    assert proposal.proposed_definition["id"] == "project"
    assert "project" in proposal.title
    assert final.get("pipeline_version") == "v1"
