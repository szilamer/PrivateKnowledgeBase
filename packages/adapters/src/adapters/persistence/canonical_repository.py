import json
from uuid import UUID

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
from domain.entities import EntityType
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


def _parse_entity(row: object) -> CanonicalEntity:
    mapping = dict(row._mapping)  # type: ignore[attr-defined]
    return CanonicalEntity(
        id=mapping["id"],
        owner_id=mapping["owner_id"],
        entity_type=EntityType(mapping["entity_type"]),
        canonical_name=mapping["canonical_name"],
        aliases=mapping.get("aliases") or [],
        description=mapping.get("description"),
        status=mapping["status"],
        source_proposal_id=mapping.get("source_proposal_id"),
        ontology_version=mapping["ontology_version"],
        created_at=mapping["created_at"],
        updated_at=mapping["updated_at"],
    )


def _parse_claim(row: object, provenance: list[ClaimProvenance]) -> CanonicalClaim:
    mapping = dict(row._mapping)  # type: ignore[attr-defined]
    return CanonicalClaim(
        id=mapping["id"],
        owner_id=mapping["owner_id"],
        subject_entity_id=mapping.get("subject_entity_id"),
        predicate=mapping["predicate"],
        object_value=mapping["object_value"],
        object_entity_id=mapping.get("object_entity_id"),
        status=ClaimStatus(mapping["status"]),
        confidence=float(mapping["confidence"]),
        valid_from=mapping.get("valid_from"),
        valid_to=mapping.get("valid_to"),
        observed_at=mapping.get("observed_at"),
        source_proposal_id=mapping.get("source_proposal_id"),
        superseded_by=mapping.get("superseded_by"),
        created_at=mapping["created_at"],
        updated_at=mapping["updated_at"],
        provenance=provenance,
    )


class PostgresCanonicalRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_entity(self, entity: CanonicalEntity) -> CanonicalEntity:
        await self._session.execute(
            text(
                """
                INSERT INTO canonical_entities (
                    id, owner_id, entity_type, canonical_name, aliases,
                    description, status, source_proposal_id, ontology_version,
                    created_at, updated_at
                ) VALUES (
                    :id, :owner_id, :entity_type, :canonical_name,
                    CAST(:aliases AS jsonb), :description, :status,
                    :source_proposal_id, :ontology_version, :created_at, :updated_at
                )
                ON CONFLICT (owner_id, entity_type, canonical_name)
                DO UPDATE SET
                    aliases = EXCLUDED.aliases,
                    description = EXCLUDED.description,
                    status = EXCLUDED.status,
                    source_proposal_id = EXCLUDED.source_proposal_id,
                    updated_at = EXCLUDED.updated_at
                """
            ),
            {
                "id": entity.id,
                "owner_id": entity.owner_id,
                "entity_type": entity.entity_type.value,
                "canonical_name": entity.canonical_name,
                "aliases": json.dumps(entity.aliases),
                "description": entity.description,
                "status": entity.status,
                "source_proposal_id": entity.source_proposal_id,
                "ontology_version": entity.ontology_version,
                "created_at": entity.created_at,
                "updated_at": entity.updated_at,
            },
        )
        return entity

    async def get_entity(self, entity_id: UUID, owner_id: UUID) -> CanonicalEntity | None:
        result = await self._session.execute(
            text("SELECT * FROM canonical_entities WHERE id = :id AND owner_id = :owner_id"),
            {"id": entity_id, "owner_id": owner_id},
        )
        row = result.first()
        return _parse_entity(row) if row else None

    async def list_entities(
        self, owner_id: UUID, *, limit: int, cursor: UUID | None
    ) -> tuple[list[CanonicalEntity], UUID | None]:
        query = "SELECT * FROM canonical_entities WHERE owner_id = :owner_id"
        params: dict[str, object] = {"owner_id": owner_id, "limit": limit + 1}
        if cursor:
            query += " AND id > :cursor"
            params["cursor"] = cursor
        query += " ORDER BY id LIMIT :limit"
        result = await self._session.execute(text(query), params)
        rows = result.fetchall()
        entities = [_parse_entity(row) for row in rows[:limit]]
        next_cursor = None
        if len(rows) > limit:
            next_cursor = dict(rows[limit]._mapping)["id"]
        return entities, next_cursor

    async def find_entity_by_name(
        self, owner_id: UUID, entity_type: str, canonical_name: str
    ) -> CanonicalEntity | None:
        result = await self._session.execute(
            text(
                """
                SELECT * FROM canonical_entities
                WHERE owner_id = :owner_id
                  AND entity_type = :entity_type
                  AND canonical_name = :canonical_name
                """
            ),
            {
                "owner_id": owner_id,
                "entity_type": entity_type,
                "canonical_name": canonical_name,
            },
        )
        row = result.first()
        return _parse_entity(row) if row else None

    async def create_claim(self, claim: CanonicalClaim) -> CanonicalClaim:
        await self._session.execute(
            text(
                """
                INSERT INTO canonical_claims (
                    id, owner_id, subject_entity_id, predicate, object_value,
                    object_entity_id, status, confidence, valid_from, valid_to,
                    observed_at, source_proposal_id, superseded_by,
                    created_at, updated_at
                ) VALUES (
                    :id, :owner_id, :subject_entity_id, :predicate, :object_value,
                    :object_entity_id, :status, :confidence, :valid_from, :valid_to,
                    :observed_at, :source_proposal_id, :superseded_by,
                    :created_at, :updated_at
                )
                """
            ),
            {
                "id": claim.id,
                "owner_id": claim.owner_id,
                "subject_entity_id": claim.subject_entity_id,
                "predicate": claim.predicate,
                "object_value": claim.object_value,
                "object_entity_id": claim.object_entity_id,
                "status": claim.status.value,
                "confidence": claim.confidence,
                "valid_from": claim.valid_from,
                "valid_to": claim.valid_to,
                "observed_at": claim.observed_at,
                "source_proposal_id": claim.source_proposal_id,
                "superseded_by": claim.superseded_by,
                "created_at": claim.created_at,
                "updated_at": claim.updated_at,
            },
        )
        for item in claim.provenance:
            await self.add_provenance(item)
        return claim

    async def get_claim(self, claim_id: UUID, owner_id: UUID) -> CanonicalClaim | None:
        result = await self._session.execute(
            text("SELECT * FROM canonical_claims WHERE id = :id AND owner_id = :owner_id"),
            {"id": claim_id, "owner_id": owner_id},
        )
        row = result.first()
        if not row:
            return None
        provenance = await self._load_provenance(claim_id)
        return _parse_claim(row, provenance)

    async def list_claims(
        self, owner_id: UUID, *, limit: int, cursor: UUID | None, status: str | None = None
    ) -> tuple[list[CanonicalClaim], UUID | None]:
        query = "SELECT * FROM canonical_claims WHERE owner_id = :owner_id"
        params: dict[str, object] = {"owner_id": owner_id, "limit": limit + 1}
        if status:
            query += " AND status = :status"
            params["status"] = status
        if cursor:
            query += " AND id > :cursor"
            params["cursor"] = cursor
        query += " ORDER BY id LIMIT :limit"
        result = await self._session.execute(text(query), params)
        rows = result.fetchall()
        claims: list[CanonicalClaim] = []
        for row in rows[:limit]:
            claim_id = row._mapping["id"]
            provenance = await self._load_provenance(claim_id)
            claims.append(_parse_claim(row, provenance))
        next_cursor = None
        if len(rows) > limit:
            next_cursor = dict(rows[limit]._mapping)["id"]
        return claims, next_cursor

    async def find_active_claims(
        self,
        owner_id: UUID,
        *,
        subject_entity_id: UUID | None,
        predicate: str,
    ) -> list[CanonicalClaim]:
        result = await self._session.execute(
            text(
                """
                SELECT * FROM canonical_claims
                WHERE owner_id = :owner_id
                  AND predicate = :predicate
                  AND status = 'active'
                  AND (
                    (:subject_entity_id IS NULL AND subject_entity_id IS NULL)
                    OR subject_entity_id = :subject_entity_id
                  )
                """
            ),
            {
                "owner_id": owner_id,
                "subject_entity_id": subject_entity_id,
                "predicate": predicate,
            },
        )
        claims: list[CanonicalClaim] = []
        for row in result.fetchall():
            claim_id = row._mapping["id"]
            provenance = await self._load_provenance(claim_id)
            claims.append(_parse_claim(row, provenance))
        return claims

    async def add_provenance(self, provenance: ClaimProvenance) -> None:
        await self._session.execute(
            text(
                """
                INSERT INTO claim_provenance (
                    id, claim_id, source_object_version_id, content_chunk_id,
                    proposal_id, extraction_run_id, model, confidence, created_at
                ) VALUES (
                    :id, :claim_id, :source_object_version_id, :content_chunk_id,
                    :proposal_id, :extraction_run_id, :model, :confidence, :created_at
                )
                """
            ),
            {
                "id": provenance.id,
                "claim_id": provenance.claim_id,
                "source_object_version_id": provenance.source_object_version_id,
                "content_chunk_id": provenance.content_chunk_id,
                "proposal_id": provenance.proposal_id,
                "extraction_run_id": provenance.extraction_run_id,
                "model": provenance.model,
                "confidence": provenance.confidence,
                "created_at": provenance.created_at,
            },
        )

    async def create_relationship(
        self, relationship: CanonicalRelationship
    ) -> CanonicalRelationship:
        await self._session.execute(
            text(
                """
                INSERT INTO canonical_relationships (
                    id, owner_id, source_entity_id, target_entity_id,
                    relationship_type, status, valid_from, valid_to,
                    source_proposal_id, created_at, updated_at
                ) VALUES (
                    :id, :owner_id, :source_entity_id, :target_entity_id,
                    :relationship_type, :status, :valid_from, :valid_to,
                    :source_proposal_id, :created_at, :updated_at
                )
                """
            ),
            {
                "id": relationship.id,
                "owner_id": relationship.owner_id,
                "source_entity_id": relationship.source_entity_id,
                "target_entity_id": relationship.target_entity_id,
                "relationship_type": relationship.relationship_type,
                "status": relationship.status,
                "valid_from": relationship.valid_from,
                "valid_to": relationship.valid_to,
                "source_proposal_id": relationship.source_proposal_id,
                "created_at": relationship.created_at,
                "updated_at": relationship.updated_at,
            },
        )
        return relationship

    async def create_contradiction(self, finding: ContradictionFinding) -> ContradictionFinding:
        await self._session.execute(
            text(
                """
                INSERT INTO contradiction_findings (
                    id, owner_id, existing_claim_id, conflicting_claim_id,
                    conflicting_proposal_id, status, summary, created_at, updated_at
                ) VALUES (
                    :id, :owner_id, :existing_claim_id, :conflicting_claim_id,
                    :conflicting_proposal_id, :status, :summary, :created_at, :updated_at
                )
                """
            ),
            {
                "id": finding.id,
                "owner_id": finding.owner_id,
                "existing_claim_id": finding.existing_claim_id,
                "conflicting_claim_id": finding.conflicting_claim_id,
                "conflicting_proposal_id": finding.conflicting_proposal_id,
                "status": finding.status.value,
                "summary": finding.summary,
                "created_at": finding.created_at,
                "updated_at": finding.updated_at,
            },
        )
        return finding

    async def list_contradictions(
        self, owner_id: UUID, *, status: str | None, limit: int
    ) -> list[ContradictionFinding]:
        query = "SELECT * FROM contradiction_findings WHERE owner_id = :owner_id"
        params: dict[str, object] = {"owner_id": owner_id, "limit": limit}
        if status:
            query += " AND status = :status"
            params["status"] = status
        query += " ORDER BY created_at DESC LIMIT :limit"
        result = await self._session.execute(text(query), params)
        return [
            ContradictionFinding(
                id=mapping["id"],
                owner_id=mapping["owner_id"],
                existing_claim_id=mapping["existing_claim_id"],
                conflicting_claim_id=mapping.get("conflicting_claim_id"),
                conflicting_proposal_id=mapping.get("conflicting_proposal_id"),
                status=ContradictionStatus(mapping["status"]),
                summary=mapping["summary"],
                created_at=mapping["created_at"],
                updated_at=mapping["updated_at"],
            )
            for row in result.fetchall()
            for mapping in [dict(row._mapping)]
        ]

    async def link_entity_index(self, entity_index_id: UUID, canonical_entity_id: UUID) -> None:
        await self._session.execute(
            text(
                """
                UPDATE entity_index
                SET canonical_entity_id = :canonical_entity_id, updated_at = NOW()
                WHERE id = :id
                """
            ),
            {"id": entity_index_id, "canonical_entity_id": canonical_entity_id},
        )

    async def _load_provenance(self, claim_id: UUID) -> list[ClaimProvenance]:
        result = await self._session.execute(
            text("SELECT * FROM claim_provenance WHERE claim_id = :claim_id"),
            {"claim_id": claim_id},
        )
        return [
            ClaimProvenance(
                id=mapping["id"],
                claim_id=mapping["claim_id"],
                source_object_version_id=mapping.get("source_object_version_id"),
                content_chunk_id=mapping.get("content_chunk_id"),
                proposal_id=mapping.get("proposal_id"),
                extraction_run_id=mapping.get("extraction_run_id"),
                model=mapping.get("model"),
                confidence=mapping.get("confidence"),
                created_at=mapping["created_at"],
            )
            for row in result.fetchall()
            for mapping in [dict(row._mapping)]
        ]


class PostgresOutboxRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def append(self, event: OutboxEvent) -> None:
        await self._session.execute(
            text(
                """
                INSERT INTO outbox_events (
                    id, aggregate_type, aggregate_id, event_type, payload,
                    created_at, status, retry_count
                ) VALUES (
                    :id, :aggregate_type, :aggregate_id, :event_type,
                    CAST(:payload AS jsonb), :created_at, :status, :retry_count
                )
                """
            ),
            {
                "id": event.id,
                "aggregate_type": event.aggregate_type,
                "aggregate_id": event.aggregate_id,
                "event_type": event.event_type,
                "payload": json.dumps(event.payload),
                "created_at": event.created_at,
                "status": event.status.value,
                "retry_count": event.retry_count,
            },
        )

    async def fetch_pending(self, *, limit: int) -> list[OutboxEvent]:
        result = await self._session.execute(
            text(
                """
                SELECT * FROM outbox_events
                WHERE status = 'pending'
                ORDER BY created_at
                LIMIT :limit
                FOR UPDATE SKIP LOCKED
                """
            ),
            {"limit": limit},
        )
        return [
            OutboxEvent(
                id=mapping["id"],
                aggregate_type=mapping["aggregate_type"],
                aggregate_id=mapping["aggregate_id"],
                event_type=mapping["event_type"],
                payload=mapping["payload"],
                created_at=mapping["created_at"],
                processed_at=mapping.get("processed_at"),
                retry_count=mapping["retry_count"],
                status=OutboxEventStatus(mapping["status"]),
            )
            for row in result.fetchall()
            for mapping in [dict(row._mapping)]
        ]

    async def mark_processed(self, event_id: UUID) -> None:
        await self._session.execute(
            text(
                """
                UPDATE outbox_events
                SET status = 'processed', processed_at = NOW()
                WHERE id = :id
                """
            ),
            {"id": event_id},
        )

    async def mark_failed(self, event_id: UUID, *, error: str) -> None:
        await self._session.execute(
            text(
                """
                UPDATE outbox_events
                SET status = 'failed',
                    retry_count = retry_count + 1,
                    payload = payload || CAST(:error AS jsonb)
                WHERE id = :id
                """
            ),
            {"id": event_id, "error": json.dumps({"last_error": error})},
        )

    async def pending_count(self) -> int:
        result = await self._session.execute(
            text("SELECT COUNT(*) AS count FROM outbox_events WHERE status = 'pending'")
        )
        row = result.first()
        if row is None:
            return 0
        return int(dict(row._mapping)["count"])
