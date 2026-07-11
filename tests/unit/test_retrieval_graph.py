from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from agents.retrieval.graph import build_retrieval_graph
from domain.canonical import CanonicalClaim, CanonicalEntity
from domain.content import ChunkSearchHit
from domain.entities import EntityType
from domain.graph import GraphEdge, GraphNode, GraphView
from domain.questions import RetrievalSignal


@pytest.mark.asyncio
async def test_retrieval_graph_produces_plan_and_citation_ids() -> None:
    owner_id = uuid4()
    chunk_id = uuid4()
    entity_id = uuid4()
    claim_id = uuid4()
    now = datetime.now(UTC)

    async def search_chunks(
        requested_owner: UUID,
        question: str,
        mode: str,
        limit: int,
    ) -> list[ChunkSearchHit]:
        assert requested_owner == owner_id
        assert question == "What database is used?"
        return [
            ChunkSearchHit(
                chunk_id=chunk_id,
                source_id=uuid4(),
                source_object_version_id=uuid4(),
                external_id="docs/db.md",
                text="PostgreSQL stores canonical knowledge.",
                score=0.9,
                match_type="semantic",
            )
        ]

    async def find_matching_entities(requested_owner: UUID, question: str) -> list[object]:
        assert requested_owner == owner_id
        return [
            CanonicalEntity(
                id=entity_id,
                owner_id=owner_id,
                entity_type=EntityType.TECHNOLOGY,
                canonical_name="PostgreSQL",
                created_at=now,
                updated_at=now,
            )
        ]

    async def expand_neighborhood(requested_owner: UUID, requested_entity_id: UUID) -> GraphView:
        assert requested_owner == owner_id
        assert requested_entity_id == entity_id
        return GraphView(
            nodes=[GraphNode(id=str(entity_id), label="PostgreSQL", node_type="entity")],
            edges=[
                GraphEdge(
                    id="edge-1",
                    source_id=str(entity_id),
                    target_id=str(uuid4()),
                    edge_type="USES_TECHNOLOGY",
                )
            ],
        )

    async def search_claims(requested_owner: UUID, question: str, limit: int) -> list[object]:
        assert requested_owner == owner_id
        return [
            CanonicalClaim(
                id=claim_id,
                owner_id=owner_id,
                predicate="uses_technology",
                object_value="PostgreSQL",
                confidence=0.85,
                created_at=now,
                updated_at=now,
            )
        ]

    graph = build_retrieval_graph(
        search_chunks=search_chunks,
        find_matching_entities=find_matching_entities,
        expand_neighborhood=expand_neighborhood,
        search_claims=search_claims,
    )
    final = await graph.ainvoke(
        {
            "owner_id": owner_id,
            "question": "What database is used?",
            "mode": "hybrid",
            "limit": 5,
            "citations": {},
            "plan": [],
            "related_entities": [],
        }
    )

    plan = final.get("plan", [])
    citation_ids = final.get("citation_ids", [])
    assert len(plan) == 3
    assert plan[0].signal == RetrievalSignal.KEYWORD
    assert plan[1].signal == RetrievalSignal.GRAPH
    assert plan[2].signal == RetrievalSignal.CANONICAL
    assert f"chunk-{chunk_id}" in citation_ids
    assert f"graph-{entity_id}" in citation_ids
    assert f"claim-{claim_id}" in citation_ids
    assert final.get("pipeline_version") == "v1"
