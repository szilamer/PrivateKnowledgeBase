"""Graph projection rebuild from canonical PostgreSQL state."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from domain.canonical import (
    CanonicalClaim,
    CanonicalEntity,
    CanonicalRelationship,
    ContradictionFinding,
    OutboxEvent,
    OutboxEventStatus,
)
from domain.identity import OwnerContext
from domain.operations import ProjectionRebuildResult

from application.policy import LocalPolicyService
from application.ports.canonical import CanonicalRepository
from application.ports.graph import GraphProjector


class GraphProjectionRebuildService:
    """Phase 6 — rebuild Neo4j from canonical PostgreSQL (ADR-004)."""

    REBUILD_LIMIT = 10_000

    def __init__(
        self,
        canonical: CanonicalRepository,
        projector: GraphProjector,
        policy: LocalPolicyService,
    ) -> None:
        self._canonical = canonical
        self._projector = projector
        self._policy = policy

    async def rebuild(self, owner: OwnerContext) -> ProjectionRebuildResult:
        self._policy.authorize_owner(owner, owner.owner_id)
        owner_id = owner.owner_id

        await self._projector.ensure_constraints()
        await self._projector.clear_owner(owner_id)

        entities = await self._canonical.list_all_entities(owner_id, limit=self.REBUILD_LIMIT)
        relationships = await self._canonical.list_all_relationships(
            owner_id, limit=self.REBUILD_LIMIT
        )
        claims = await self._canonical.list_all_claims(owner_id, limit=self.REBUILD_LIMIT)
        contradictions = await self._canonical.list_contradictions(
            owner_id, status="open", limit=self.REBUILD_LIMIT
        )

        for entity in entities:
            await self._projector.project_event(self._entity_event(entity, owner_id))
        for relationship in relationships:
            await self._projector.project_event(self._relationship_event(relationship, owner_id))
        for claim in claims:
            await self._projector.project_event(self._claim_event(claim, owner_id))
        for finding in contradictions:
            await self._projector.project_event(self._contradiction_event(finding, owner_id))

        return ProjectionRebuildResult(
            entities_projected=len(entities),
            relationships_projected=len(relationships),
            claims_projected=len(claims),
            contradictions_projected=len(contradictions),
            cleared_nodes=True,
        )

    def _entity_event(self, entity: CanonicalEntity, owner_id: UUID) -> OutboxEvent:
        now = datetime.now(UTC)
        return OutboxEvent(
            id=uuid4(),
            aggregate_type="entity",
            aggregate_id=str(entity.id),
            event_type="entity.materialized",
            payload={
                "entity_id": str(entity.id),
                "owner_id": str(owner_id),
                "entity_type": entity.entity_type.value,
                "canonical_name": entity.canonical_name,
                "aliases": entity.aliases,
            },
            created_at=now,
            status=OutboxEventStatus.PENDING,
        )

    def _relationship_event(
        self, relationship: CanonicalRelationship, owner_id: UUID
    ) -> OutboxEvent:
        now = datetime.now(UTC)
        return OutboxEvent(
            id=uuid4(),
            aggregate_type="relationship",
            aggregate_id=str(relationship.id),
            event_type="relationship.materialized",
            payload={
                "relationship_id": str(relationship.id),
                "owner_id": str(owner_id),
                "source_entity_id": str(relationship.source_entity_id),
                "target_entity_id": str(relationship.target_entity_id),
                "relationship_type": relationship.relationship_type,
            },
            created_at=now,
            status=OutboxEventStatus.PENDING,
        )

    def _claim_event(self, claim: CanonicalClaim, owner_id: UUID) -> OutboxEvent:
        now = datetime.now(UTC)
        return OutboxEvent(
            id=uuid4(),
            aggregate_type="claim",
            aggregate_id=str(claim.id),
            event_type="claim.materialized",
            payload={
                "claim_id": str(claim.id),
                "owner_id": str(owner_id),
                "subject_entity_id": str(claim.subject_entity_id)
                if claim.subject_entity_id
                else None,
                "predicate": claim.predicate,
                "object_value": claim.object_value,
                "status": claim.status.value,
                "confidence": claim.confidence,
            },
            created_at=now,
            status=OutboxEventStatus.PENDING,
        )

    def _contradiction_event(self, finding: ContradictionFinding, owner_id: UUID) -> OutboxEvent:
        now = datetime.now(UTC)
        return OutboxEvent(
            id=uuid4(),
            aggregate_type="contradiction",
            aggregate_id=str(finding.id),
            event_type="contradiction.detected",
            payload={
                "finding_id": str(finding.id),
                "owner_id": str(owner_id),
                "existing_claim_id": str(finding.existing_claim_id),
                "conflicting_proposal_id": str(finding.conflicting_proposal_id)
                if finding.conflicting_proposal_id
                else None,
                "summary": finding.summary,
            },
            created_at=now,
            status=OutboxEventStatus.PENDING,
        )
