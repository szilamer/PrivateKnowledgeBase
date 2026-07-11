import json
from datetime import UTC, datetime
from uuid import UUID

from domain.ontology_proposals import (
    OntologyProposal,
    OntologyProposalKind,
    OntologyProposalStatus,
    UnmappedEntityCandidate,
    UnmappedRelationshipCandidate,
)
from ontology.loader import load_ontology_snapshot
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


def _parse_proposal(mapping: dict[str, object]) -> OntologyProposal:
    proposed_raw = mapping.get("proposed_definition") or {}
    evidence_raw = mapping.get("evidence") or {}
    if isinstance(proposed_raw, str):
        proposed_raw = json.loads(proposed_raw)
    if isinstance(evidence_raw, str):
        evidence_raw = json.loads(evidence_raw)
    return OntologyProposal(
        id=mapping["id"],  # type: ignore[arg-type]
        owner_id=mapping["owner_id"],  # type: ignore[arg-type]
        kind=OntologyProposalKind(str(mapping["kind"])),
        status=OntologyProposalStatus(str(mapping["status"])),
        title=str(mapping["title"]),
        rationale=str(mapping["rationale"]),
        proposed_definition=dict(proposed_raw) if isinstance(proposed_raw, dict) else {},
        evidence=dict(evidence_raw) if isinstance(evidence_raw, dict) else {},
        ontology_version=str(mapping["ontology_version"]),
        decision_rationale=str(mapping["decision_rationale"])
        if mapping.get("decision_rationale")
        else None,
        created_at=mapping["created_at"],  # type: ignore[arg-type]
        updated_at=mapping["updated_at"],  # type: ignore[arg-type]
        decided_at=mapping.get("decided_at"),  # type: ignore[arg-type]
    )


class PostgresOntologyProposalRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_proposals(self, proposals: list[OntologyProposal]) -> list[OntologyProposal]:
        saved: list[OntologyProposal] = []
        for proposal in proposals:
            target_id = str(proposal.proposed_definition.get("id", ""))
            existing = await self.find_pending_by_target_id(
                proposal.owner_id,
                kind=proposal.kind.value,
                target_id=target_id,
            )
            if existing is not None:
                continue
            await self._session.execute(
                text(
                    """
                    INSERT INTO ontology_proposals (
                        id, owner_id, kind, status, title, rationale,
                        proposed_definition, evidence, ontology_version,
                        created_at, updated_at
                    ) VALUES (
                        :id, :owner_id, :kind, :status, :title, :rationale,
                        CAST(:proposed_definition AS jsonb), CAST(:evidence AS jsonb),
                        :ontology_version, :created_at, :updated_at
                    )
                    """
                ),
                {
                    "id": proposal.id,
                    "owner_id": proposal.owner_id,
                    "kind": proposal.kind.value,
                    "status": proposal.status.value,
                    "title": proposal.title,
                    "rationale": proposal.rationale,
                    "proposed_definition": json.dumps(proposal.proposed_definition),
                    "evidence": json.dumps(proposal.evidence),
                    "ontology_version": proposal.ontology_version,
                    "created_at": proposal.created_at,
                    "updated_at": proposal.updated_at,
                },
            )
            saved.append(proposal)
        return saved

    async def list_proposals(
        self,
        owner_id: UUID,
        *,
        status: OntologyProposalStatus | None = None,
        limit: int = 50,
    ) -> list[OntologyProposal]:
        query = "SELECT * FROM ontology_proposals WHERE owner_id = :owner_id"
        params: dict[str, object] = {"owner_id": owner_id, "limit": limit}
        if status is not None:
            query += " AND status = :status"
            params["status"] = status.value
        query += " ORDER BY created_at DESC LIMIT :limit"
        result = await self._session.execute(text(query), params)
        return [_parse_proposal(dict(row._mapping)) for row in result.fetchall()]

    async def get_by_id(self, proposal_id: UUID, owner_id: UUID) -> OntologyProposal | None:
        result = await self._session.execute(
            text(
                """
                SELECT * FROM ontology_proposals
                WHERE id = :id AND owner_id = :owner_id
                """
            ),
            {"id": proposal_id, "owner_id": owner_id},
        )
        row = result.first()
        if row is None:
            return None
        return _parse_proposal(dict(row._mapping))

    async def update_status(
        self,
        proposal_id: UUID,
        owner_id: UUID,
        *,
        status: OntologyProposalStatus,
        decision_rationale: str | None = None,
    ) -> OntologyProposal | None:
        now = datetime.now(UTC)
        decided_at = now if status != OntologyProposalStatus.PENDING else None
        await self._session.execute(
            text(
                """
                UPDATE ontology_proposals
                SET status = :status,
                    decision_rationale = :decision_rationale,
                    updated_at = :updated_at,
                    decided_at = COALESCE(:decided_at, decided_at)
                WHERE id = :id AND owner_id = :owner_id
                """
            ),
            {
                "id": proposal_id,
                "owner_id": owner_id,
                "status": status.value,
                "decision_rationale": decision_rationale,
                "updated_at": now,
                "decided_at": decided_at,
            },
        )
        return await self.get_by_id(proposal_id, owner_id)

    async def find_pending_by_target_id(
        self,
        owner_id: UUID,
        *,
        kind: str,
        target_id: str,
    ) -> OntologyProposal | None:
        result = await self._session.execute(
            text(
                """
                SELECT * FROM ontology_proposals
                WHERE owner_id = :owner_id
                  AND kind = :kind
                  AND status = 'pending'
                  AND proposed_definition->>'id' = :target_id
                LIMIT 1
                """
            ),
            {"owner_id": owner_id, "kind": kind, "target_id": target_id},
        )
        row = result.first()
        if row is None:
            return None
        return _parse_proposal(dict(row._mapping))


class PostgresUnmappedConceptReader:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def aggregate_unmapped_entities(
        self, owner_id: UUID, *, min_occurrences: int
    ) -> list[UnmappedEntityCandidate]:
        snapshot = load_ontology_snapshot()
        known_types = set(snapshot.entity_type_ids)

        result = await self._session.execute(
            text(
                """
                SELECT payload->>'entity_type' AS entity_type,
                       payload->>'name' AS name,
                       COUNT(*) AS occurrence_count,
                       ARRAY_AGG(id::text ORDER BY created_at DESC) AS proposal_ids
                FROM knowledge_proposals
                WHERE owner_id = :owner_id
                  AND proposal_type IN ('entity', 'entity_resolution')
                  AND status IN ('pending', 'approved')
                  AND payload ? 'entity_type'
                  AND payload ? 'name'
                GROUP BY payload->>'entity_type', payload->>'name'
                HAVING COUNT(*) >= :min_occurrences
                ORDER BY COUNT(*) DESC
                LIMIT 100
                """
            ),
            {"owner_id": owner_id, "min_occurrences": min_occurrences},
        )

        candidates: list[UnmappedEntityCandidate] = []
        for row in result.fetchall():
            mapping = dict(row._mapping)
            entity_type = str(mapping.get("entity_type") or "")
            if not entity_type or entity_type in known_types:
                continue
            proposal_ids = mapping.get("proposal_ids") or []
            sample_ids = (
                [str(item) for item in proposal_ids[:3]] if isinstance(proposal_ids, list) else []
            )
            candidates.append(
                UnmappedEntityCandidate(
                    name=str(mapping.get("name") or ""),
                    entity_type=entity_type,
                    occurrence_count=int(mapping.get("occurrence_count") or 0),
                    sample_proposal_ids=sample_ids,
                )
            )
        return candidates

    async def aggregate_unmapped_relationships(
        self, owner_id: UUID, *, min_occurrences: int
    ) -> list[UnmappedRelationshipCandidate]:
        snapshot = load_ontology_snapshot()
        known_types = set(snapshot.relationship_type_ids)

        result = await self._session.execute(
            text(
                """
                SELECT payload->>'relationship_type' AS relationship_type,
                       COUNT(*) AS occurrence_count,
                       ARRAY_AGG(id::text ORDER BY created_at DESC) AS proposal_ids
                FROM knowledge_proposals
                WHERE owner_id = :owner_id
                  AND proposal_type = 'relationship'
                  AND status IN ('pending', 'approved')
                  AND payload ? 'relationship_type'
                GROUP BY payload->>'relationship_type'
                HAVING COUNT(*) >= :min_occurrences
                ORDER BY COUNT(*) DESC
                LIMIT 50
                """
            ),
            {"owner_id": owner_id, "min_occurrences": min_occurrences},
        )

        candidates: list[UnmappedRelationshipCandidate] = []
        for row in result.fetchall():
            mapping = dict(row._mapping)
            relationship_type = str(mapping.get("relationship_type") or "")
            if not relationship_type or relationship_type in known_types:
                continue
            proposal_ids = mapping.get("proposal_ids") or []
            sample_ids = (
                [str(item) for item in proposal_ids[:3]] if isinstance(proposal_ids, list) else []
            )
            candidates.append(
                UnmappedRelationshipCandidate(
                    relationship_type=relationship_type,
                    occurrence_count=int(mapping.get("occurrence_count") or 0),
                    sample_proposal_ids=sample_ids,
                )
            )
        return candidates
