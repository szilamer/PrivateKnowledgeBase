from datetime import UTC, datetime
from uuid import UUID, uuid4

from domain.canonical import (
    CanonicalClaim,
    CanonicalEntity,
    CanonicalRelationship,
    ClaimProvenance,
    ClaimStatus,
    ContradictionFinding,
    ContradictionStatus,
    OutboxEvent,
    OutboxEventStatus,
)
from domain.entities import EntityIndexEntry, EntityType
from domain.proposals import KnowledgeProposal, ProposalType

from application.ports.canonical import CanonicalRepository, OutboxRepository
from application.ports.knowledge import EntityIndexRepository


class CanonicalMaterializationService:
    """Phase 4 — promote approved proposals to canonical knowledge + outbox."""

    def __init__(
        self,
        canonical: CanonicalRepository,
        outbox: OutboxRepository,
        entities: EntityIndexRepository,
    ) -> None:
        self._canonical = canonical
        self._outbox = outbox
        self._entities = entities

    async def materialize_approved_proposal(
        self, owner_id: UUID, proposal: KnowledgeProposal
    ) -> None:
        now = datetime.now(UTC)
        if proposal.proposal_type in {ProposalType.ENTITY, ProposalType.ENTITY_RESOLUTION}:
            await self._materialize_entity(owner_id, proposal, now)
        elif proposal.proposal_type == ProposalType.RELATIONSHIP:
            await self._materialize_relationship(owner_id, proposal, now)
        elif proposal.proposal_type in {
            ProposalType.CLAIM,
            ProposalType.TASK,
            ProposalType.DECISION,
            ProposalType.EVENT,
        }:
            await self._materialize_claim(owner_id, proposal, now)

    async def _materialize_entity(
        self, owner_id: UUID, proposal: KnowledgeProposal, now: datetime
    ) -> None:
        name = str(proposal.payload.get("name", proposal.title))
        entity_type = EntityType(str(proposal.payload.get("entity_type", "concept")))
        aliases = proposal.payload.get("aliases", [])
        entity_id = uuid4()
        if resolved := proposal.payload.get("resolved_entity_id"):
            existing = await self._canonical.get_entity(UUID(str(resolved)), owner_id)
            if existing:
                entity_id = existing.id

        entity = CanonicalEntity(
            id=entity_id,
            owner_id=owner_id,
            entity_type=entity_type,
            canonical_name=name,
            aliases=[str(alias) for alias in aliases] if isinstance(aliases, list) else [],
            description=str(proposal.payload.get("description"))
            if proposal.payload.get("description")
            else None,
            status="active",
            source_proposal_id=proposal.id,
            created_at=now,
            updated_at=now,
        )
        await self._canonical.create_entity(entity)

        entry = EntityIndexEntry(
            id=uuid4(),
            owner_id=owner_id,
            entity_type=entity_type,
            canonical_name=name,
            aliases=entity.aliases,
            status="approved",
            source_proposal_id=proposal.id,
        )
        saved = await self._entities.upsert_from_proposal(entry, source_proposal_id=proposal.id)
        await self._canonical.link_entity_index(saved.id, entity.id)

        await self._emit_outbox(
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
            now=now,
        )

    async def _materialize_relationship(
        self, owner_id: UUID, proposal: KnowledgeProposal, now: datetime
    ) -> None:
        source_ref = str(proposal.payload.get("source_local_id", ""))
        target_ref = str(proposal.payload.get("target_local_id", ""))
        rel_type = str(proposal.payload.get("relationship_type", "RELATES_TO"))
        source_entity = await self._resolve_entity_ref(owner_id, source_ref, proposal)
        target_entity = await self._resolve_entity_ref(owner_id, target_ref, proposal)
        if source_entity is None or target_entity is None:
            return

        relationship = CanonicalRelationship(
            id=uuid4(),
            owner_id=owner_id,
            source_entity_id=source_entity.id,
            target_entity_id=target_entity.id,
            relationship_type=rel_type,
            status="active",
            source_proposal_id=proposal.id,
            created_at=now,
            updated_at=now,
        )
        await self._canonical.create_relationship(relationship)
        await self._emit_outbox(
            aggregate_type="relationship",
            aggregate_id=str(relationship.id),
            event_type="relationship.materialized",
            payload={
                "relationship_id": str(relationship.id),
                "owner_id": str(owner_id),
                "source_entity_id": str(source_entity.id),
                "target_entity_id": str(target_entity.id),
                "relationship_type": rel_type,
            },
            now=now,
        )

    async def _materialize_claim(
        self, owner_id: UUID, proposal: KnowledgeProposal, now: datetime
    ) -> None:
        predicate_map = {
            ProposalType.CLAIM: str(proposal.payload.get("predicate", "claims")),
            ProposalType.TASK: "has_task",
            ProposalType.DECISION: "has_decision",
            ProposalType.EVENT: "has_event",
        }
        value_map = {
            ProposalType.CLAIM: str(proposal.payload.get("value", proposal.title)),
            ProposalType.TASK: str(proposal.payload.get("title", proposal.title)),
            ProposalType.DECISION: str(proposal.payload.get("title", proposal.title)),
            ProposalType.EVENT: str(proposal.payload.get("title", proposal.title)),
        }
        predicate = predicate_map[proposal.proposal_type]
        object_value = value_map[proposal.proposal_type]

        subject_entity_id: UUID | None = None
        subject_ref = proposal.payload.get("subject_local_id")
        if subject_ref:
            entity = await self._resolve_entity_ref(owner_id, str(subject_ref), proposal)
            subject_entity_id = entity.id if entity else None

        claim = CanonicalClaim(
            id=uuid4(),
            owner_id=owner_id,
            subject_entity_id=subject_entity_id,
            predicate=predicate,
            object_value=object_value,
            status=ClaimStatus.ACTIVE,
            confidence=proposal.confidence,
            source_proposal_id=proposal.id,
            observed_at=now,
            created_at=now,
            updated_at=now,
            provenance=[
                ClaimProvenance(
                    id=uuid4(),
                    claim_id=uuid4(),
                    source_object_version_id=span.source_object_version_id,
                    content_chunk_id=span.content_chunk_id,
                    proposal_id=proposal.id,
                    extraction_run_id=proposal.extraction_run_id,
                    confidence=proposal.confidence,
                    created_at=now,
                )
                for span in proposal.evidence
            ],
        )
        for item in claim.provenance:
            item.claim_id = claim.id

        await self._detect_contradictions(owner_id, claim, proposal, now)
        await self._canonical.create_claim(claim)
        await self._emit_outbox(
            aggregate_type="claim",
            aggregate_id=str(claim.id),
            event_type="claim.materialized",
            payload={
                "claim_id": str(claim.id),
                "owner_id": str(owner_id),
                "subject_entity_id": str(subject_entity_id) if subject_entity_id else None,
                "predicate": predicate,
                "object_value": object_value,
                "status": claim.status.value,
                "confidence": claim.confidence,
            },
            now=now,
        )

    async def _detect_contradictions(
        self,
        owner_id: UUID,
        claim: CanonicalClaim,
        proposal: KnowledgeProposal,
        now: datetime,
    ) -> None:
        existing = await self._canonical.find_active_claims(
            owner_id,
            subject_entity_id=claim.subject_entity_id,
            predicate=claim.predicate,
        )
        for prior in existing:
            if prior.object_value.strip().lower() == claim.object_value.strip().lower():
                continue
            finding = ContradictionFinding(
                id=uuid4(),
                owner_id=owner_id,
                existing_claim_id=prior.id,
                conflicting_proposal_id=proposal.id,
                status=ContradictionStatus.OPEN,
                summary=(
                    f"Potential contradiction on '{claim.predicate}': "
                    f"'{prior.object_value}' vs '{claim.object_value}'"
                ),
                created_at=now,
                updated_at=now,
            )
            await self._canonical.create_contradiction(finding)
            await self._emit_outbox(
                aggregate_type="contradiction",
                aggregate_id=str(finding.id),
                event_type="contradiction.detected",
                payload={
                    "finding_id": str(finding.id),
                    "owner_id": str(owner_id),
                    "existing_claim_id": str(prior.id),
                    "conflicting_proposal_id": str(proposal.id),
                    "summary": finding.summary,
                },
                now=now,
            )

    async def _resolve_entity_ref(
        self, owner_id: UUID, local_ref: str, proposal: KnowledgeProposal
    ) -> CanonicalEntity | None:
        name = str(proposal.payload.get("name", proposal.title))
        entity_type = str(proposal.payload.get("entity_type", "concept"))
        if not local_ref.startswith("ent"):
            name = local_ref
        return await self._canonical.find_entity_by_name(owner_id, entity_type, name)

    async def _emit_outbox(
        self,
        *,
        aggregate_type: str,
        aggregate_id: str,
        event_type: str,
        payload: dict[str, object],
        now: datetime,
    ) -> None:
        await self._outbox.append(
            OutboxEvent(
                id=uuid4(),
                aggregate_type=aggregate_type,
                aggregate_id=aggregate_id,
                event_type=event_type,
                payload=payload,
                created_at=now,
                status=OutboxEventStatus.PENDING,
            )
        )
