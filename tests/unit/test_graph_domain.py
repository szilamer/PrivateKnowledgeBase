from datetime import UTC, datetime
from uuid import uuid4

from domain.canonical import CanonicalClaim, ClaimStatus
from domain.contradiction_detection import values_contradict
from domain.graph import GraphEdge, GraphNode, GraphView


def test_graph_view_structure() -> None:
    node_id = str(uuid4())
    view = GraphView(
        nodes=[GraphNode(id=node_id, label="PostgreSQL", node_type="entity")],
        edges=[
            GraphEdge(
                id="edge-1",
                source_id=node_id,
                target_id=str(uuid4()),
                edge_type="USES_TECHNOLOGY",
            )
        ],
    )
    assert len(view.nodes) == 1
    assert view.edges[0].edge_type == "USES_TECHNOLOGY"


def test_contradiction_predicate_mismatch_detectable() -> None:
    assert values_contradict("Use MySQL", "Use PostgreSQL") is True


def test_claim_status_remains_active_on_create() -> None:
    claim = CanonicalClaim(
        id=uuid4(),
        owner_id=uuid4(),
        predicate="uses_technology",
        object_value="PostgreSQL",
        confidence=0.9,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    assert claim.status == ClaimStatus.ACTIVE
