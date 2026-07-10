from datetime import UTC, datetime
from uuid import uuid4

import pytest
from application.operations.rebuild_service import GraphProjectionRebuildService
from application.policy import LocalPolicyService
from domain.canonical import (
    CanonicalClaim,
    CanonicalEntity,
    ClaimStatus,
    OutboxEventStatus,
)
from domain.entities import EntityType
from domain.identity import DEFAULT_OWNER_ID


class FakeCanonicalRepository:
    async def list_all_entities(self, owner_id: object, *, limit: int) -> list[CanonicalEntity]:
        now = datetime.now(UTC)
        return [
            CanonicalEntity(
                id=uuid4(),
                owner_id=DEFAULT_OWNER_ID,
                entity_type=EntityType.PROJECT,
                canonical_name="Demo",
                aliases=[],
                description=None,
                status="active",
                source_proposal_id=None,
                ontology_version="0.1",
                created_at=now,
                updated_at=now,
            )
        ]

    async def list_all_relationships(self, owner_id: object, *, limit: int) -> list[object]:
        return []

    async def list_all_claims(self, owner_id: object, *, limit: int) -> list[CanonicalClaim]:
        now = datetime.now(UTC)
        claim_id = uuid4()
        return [
            CanonicalClaim(
                id=claim_id,
                owner_id=DEFAULT_OWNER_ID,
                subject_entity_id=None,
                predicate="has_task",
                object_value="Ship hardening",
                status=ClaimStatus.ACTIVE,
                confidence=0.9,
                created_at=now,
                updated_at=now,
            )
        ]

    async def list_contradictions(
        self, owner_id: object, *, status: str | None, limit: int
    ) -> list[object]:
        return []


class FakeProjector:
    def __init__(self) -> None:
        self.events: list[str] = []
        self.cleared = False

    async def ensure_constraints(self) -> None:
        return None

    async def clear_owner(self, owner_id: object) -> None:
        self.cleared = True

    async def project_event(self, event: object) -> None:
        from domain.canonical import OutboxEvent

        assert isinstance(event, OutboxEvent)
        self.events.append(event.event_type)

    async def close(self) -> None:
        return None


@pytest.mark.asyncio
async def test_rebuild_service_projects_canonical_records() -> None:
    projector = FakeProjector()
    service = GraphProjectionRebuildService(
        FakeCanonicalRepository(),  # type: ignore[arg-type]
        projector,
        LocalPolicyService(),
    )
    from domain.identity import OwnerContext

    result = await service.rebuild(OwnerContext())
    assert projector.cleared is True
    assert result.entities_projected == 1
    assert result.claims_projected == 1
    assert "entity.materialized" in projector.events
    assert "claim.materialized" in projector.events


def test_entity_event_payload_shape() -> None:
    service = GraphProjectionRebuildService(
        FakeCanonicalRepository(),  # type: ignore[arg-type]
        FakeProjector(),
        LocalPolicyService(),
    )
    now = datetime.now(UTC)
    entity = CanonicalEntity(
        id=uuid4(),
        owner_id=DEFAULT_OWNER_ID,
        entity_type=EntityType.PROJECT,
        canonical_name="Alpha",
        aliases=["A"],
        description=None,
        status="active",
        source_proposal_id=None,
        ontology_version="0.1",
        created_at=now,
        updated_at=now,
    )
    event = service._entity_event(entity, DEFAULT_OWNER_ID)
    assert event.event_type == "entity.materialized"
    assert event.status == OutboxEventStatus.PENDING
    assert event.payload["canonical_name"] == "Alpha"
