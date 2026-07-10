import json
from uuid import UUID, uuid4

from domain.approval import ApprovalDecision
from domain.entities import EntityIndexEntry, EntityMatch, EntityType
from domain.extraction import ExtractionRunStatus
from domain.proposals import EvidenceSpan, KnowledgeProposal, ProposalFilter, ProposalStatus
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


def _parse_proposal(row: object, evidence: list[EvidenceSpan]) -> KnowledgeProposal:
    from domain.proposals import ProposalType, RiskLevel

    mapping = dict(row._mapping)  # type: ignore[attr-defined]
    return KnowledgeProposal(
        id=mapping["id"],
        owner_id=mapping["owner_id"],
        extraction_run_id=mapping["extraction_run_id"],
        proposal_type=ProposalType(mapping["proposal_type"]),
        status=ProposalStatus(mapping["status"]),
        risk_level=RiskLevel(mapping["risk_level"]),
        confidence=float(mapping["confidence"]),
        title=mapping["title"],
        payload=mapping["payload"],
        project_id=mapping["project_id"],
        source_id=mapping["source_id"],
        requires_review=mapping["requires_review"],
        original_payload=mapping["original_payload"],
        created_at=mapping["created_at"],
        updated_at=mapping["updated_at"],
        evidence=evidence,
    )


class PostgresProposalRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_proposal(self, proposal: KnowledgeProposal) -> KnowledgeProposal:
        await self._session.execute(
            text(
                """
                INSERT INTO knowledge_proposals (
                    id, owner_id, extraction_run_id, proposal_type, status,
                    risk_level, confidence, title, payload, project_id,
                    source_id, requires_review, original_payload,
                    created_at, updated_at
                ) VALUES (
                    :id, :owner_id, :extraction_run_id, :proposal_type, :status,
                    :risk_level, :confidence, :title, CAST(:payload AS jsonb),
                    :project_id, :source_id, :requires_review,
                    CAST(:original_payload AS jsonb), :created_at, :updated_at
                )
                """
            ),
            {
                "id": proposal.id,
                "owner_id": proposal.owner_id,
                "extraction_run_id": proposal.extraction_run_id,
                "proposal_type": proposal.proposal_type.value,
                "status": proposal.status.value,
                "risk_level": proposal.risk_level.value,
                "confidence": proposal.confidence,
                "title": proposal.title,
                "payload": json.dumps(proposal.payload),
                "project_id": proposal.project_id,
                "source_id": proposal.source_id,
                "requires_review": proposal.requires_review,
                "original_payload": json.dumps(proposal.original_payload)
                if proposal.original_payload
                else None,
                "created_at": proposal.created_at,
                "updated_at": proposal.updated_at,
            },
        )
        for span in proposal.evidence:
            await self.create_evidence(
                proposal.id,
                source_object_version_id=span.source_object_version_id,
                content_chunk_id=span.content_chunk_id,
                anchor_start=span.anchor_start,
                anchor_end=span.anchor_end,
                excerpt=span.excerpt,
            )
        return proposal

    async def get_by_id(self, proposal_id: UUID, owner_id: UUID) -> KnowledgeProposal | None:
        result = await self._session.execute(
            text("SELECT * FROM knowledge_proposals WHERE id = :id AND owner_id = :owner_id"),
            {"id": proposal_id, "owner_id": owner_id},
        )
        row = result.first()
        if not row:
            return None
        evidence = await self._load_evidence(proposal_id)
        return _parse_proposal(row, evidence)

    async def list_proposals(
        self, owner_id: UUID, filters: ProposalFilter
    ) -> tuple[list[KnowledgeProposal], UUID | None]:
        query = "SELECT * FROM knowledge_proposals WHERE owner_id = :owner_id"
        params: dict[str, object] = {
            "owner_id": owner_id,
            "limit": filters.limit + 1,
        }
        if filters.status:
            query += " AND status = :status"
            params["status"] = filters.status.value
        if filters.proposal_type:
            query += " AND proposal_type = :proposal_type"
            params["proposal_type"] = filters.proposal_type.value
        if filters.risk_level:
            query += " AND risk_level = :risk_level"
            params["risk_level"] = filters.risk_level.value
        if filters.source_id:
            query += " AND source_id = :source_id"
            params["source_id"] = filters.source_id
        if filters.project_id:
            query += " AND project_id = :project_id"
            params["project_id"] = filters.project_id
        if filters.min_confidence is not None:
            query += " AND confidence >= :min_confidence"
            params["min_confidence"] = filters.min_confidence
        if filters.max_confidence is not None:
            query += " AND confidence <= :max_confidence"
            params["max_confidence"] = filters.max_confidence
        if filters.cursor:
            query += " AND id > :cursor"
            params["cursor"] = filters.cursor
        query += " ORDER BY id LIMIT :limit"

        result = await self._session.execute(text(query), params)
        rows = result.fetchall()
        proposals: list[KnowledgeProposal] = []
        for row in rows[: filters.limit]:
            row_id = row._mapping["id"]
            evidence = await self._load_evidence(row_id)
            proposals.append(_parse_proposal(row, evidence))
        next_cursor = rows[filters.limit]._mapping["id"] if len(rows) > filters.limit else None
        return proposals, next_cursor

    async def update_status(
        self,
        proposal_id: UUID,
        owner_id: UUID,
        status: str,
        *,
        payload: dict[str, object] | None = None,
        original_payload: dict[str, object] | None = None,
    ) -> KnowledgeProposal | None:
        await self._session.execute(
            text(
                """
                UPDATE knowledge_proposals
                SET status = :status,
                    payload = COALESCE(CAST(:payload AS jsonb), payload),
                    original_payload = COALESCE(
                        CAST(:original_payload AS jsonb), original_payload
                    ),
                    updated_at = NOW()
                WHERE id = :id AND owner_id = :owner_id
                """
            ),
            {
                "id": proposal_id,
                "owner_id": owner_id,
                "status": status,
                "payload": json.dumps(payload) if payload else None,
                "original_payload": json.dumps(original_payload) if original_payload else None,
            },
        )
        return await self.get_by_id(proposal_id, owner_id)

    async def create_evidence(
        self,
        proposal_id: UUID,
        *,
        source_object_version_id: UUID,
        content_chunk_id: UUID | None,
        anchor_start: int | None,
        anchor_end: int | None,
        excerpt: str | None,
    ) -> None:
        await self._session.execute(
            text(
                """
                INSERT INTO proposal_evidence (
                    id, proposal_id, source_object_version_id,
                    content_chunk_id, anchor_start, anchor_end, excerpt
                ) VALUES (
                    :id, :proposal_id, :source_object_version_id,
                    :content_chunk_id, :anchor_start, :anchor_end, :excerpt
                )
                """
            ),
            {
                "id": uuid4(),
                "proposal_id": proposal_id,
                "source_object_version_id": source_object_version_id,
                "content_chunk_id": content_chunk_id,
                "anchor_start": anchor_start,
                "anchor_end": anchor_end,
                "excerpt": excerpt,
            },
        )

    async def _load_evidence(self, proposal_id: UUID) -> list[EvidenceSpan]:
        result = await self._session.execute(
            text("SELECT * FROM proposal_evidence WHERE proposal_id = :pid"),
            {"pid": proposal_id},
        )
        return [
            EvidenceSpan(
                id=mapping["id"],
                proposal_id=mapping["proposal_id"],
                source_object_version_id=mapping["source_object_version_id"],
                content_chunk_id=mapping["content_chunk_id"],
                anchor_start=mapping["anchor_start"],
                anchor_end=mapping["anchor_end"],
                excerpt=mapping["excerpt"],
            )
            for row in result.fetchall()
            for mapping in [dict(row._mapping)]
        ]


class PostgresExtractionRunRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_run(
        self,
        *,
        run_id: UUID,
        source_object_version_id: UUID,
        owner_id: UUID,
        model: str | None,
        provider: str | None,
        prompt_version: str,
        schema_version: str,
        pipeline_version: str,
        correlation_id: str | None,
    ) -> None:
        await self._session.execute(
            text(
                """
                INSERT INTO extraction_runs (
                    id, source_object_version_id, owner_id, status,
                    model, provider, prompt_version, schema_version,
                    pipeline_version, correlation_id
                ) VALUES (
                    :id, :source_object_version_id, :owner_id, 'running',
                    :model, :provider, :prompt_version, :schema_version,
                    :pipeline_version, :correlation_id
                )
                """
            ),
            {
                "id": run_id,
                "source_object_version_id": source_object_version_id,
                "owner_id": owner_id,
                "model": model,
                "provider": provider,
                "prompt_version": prompt_version,
                "schema_version": schema_version,
                "pipeline_version": pipeline_version,
                "correlation_id": correlation_id,
            },
        )

    async def complete_run(
        self,
        run_id: UUID,
        *,
        status: ExtractionRunStatus,
        token_usage: dict[str, object] | None = None,
        latency_ms: int | None = None,
        error_summary: str | None = None,
    ) -> None:
        await self._session.execute(
            text(
                """
                UPDATE extraction_runs
                SET status = :status,
                    token_usage = CAST(:token_usage AS jsonb),
                    latency_ms = :latency_ms,
                    error_summary = :error_summary,
                    completed_at = NOW()
                WHERE id = :id
                """
            ),
            {
                "id": run_id,
                "status": status.value,
                "token_usage": json.dumps(token_usage) if token_usage else None,
                "latency_ms": latency_ms,
                "error_summary": error_summary,
            },
        )


class PostgresEntityIndexRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_matches(
        self, owner_id: UUID, name: str, entity_type: str, *, limit: int = 5
    ) -> list[EntityMatch]:
        from domain.entity_resolution import name_similarity

        result = await self._session.execute(
            text(
                """
                SELECT id, canonical_name, entity_type, aliases
                FROM entity_index
                WHERE owner_id = :owner_id
                  AND entity_type = :entity_type
                ORDER BY canonical_name
                LIMIT 50
                """
            ),
            {"owner_id": owner_id, "entity_type": entity_type},
        )
        matches: list[EntityMatch] = []
        for row in result.fetchall():
            mapping = dict(row._mapping)
            score = name_similarity(name, str(mapping["canonical_name"]))
            aliases = mapping.get("aliases") or []
            for alias in aliases:
                score = max(score, name_similarity(name, str(alias)))
            if score > 0.4:
                matches.append(
                    EntityMatch(
                        entity_id=mapping["id"],
                        canonical_name=str(mapping["canonical_name"]),
                        entity_type=EntityType(str(mapping["entity_type"])),
                        score=score,
                        match_reason="name_similarity",
                    )
                )
        matches.sort(key=lambda item: item.score, reverse=True)
        return matches[:limit]

    async def upsert_from_proposal(
        self, entry: EntityIndexEntry, *, source_proposal_id: UUID
    ) -> EntityIndexEntry:
        await self._session.execute(
            text(
                """
                INSERT INTO entity_index (
                    id, owner_id, entity_type, canonical_name, aliases,
                    status, source_proposal_id
                ) VALUES (
                    :id, :owner_id, :entity_type, :canonical_name,
                    CAST(:aliases AS jsonb), :status, :source_proposal_id
                )
                ON CONFLICT (owner_id, entity_type, canonical_name)
                DO UPDATE SET
                    aliases = EXCLUDED.aliases,
                    status = EXCLUDED.status,
                    source_proposal_id = EXCLUDED.source_proposal_id,
                    updated_at = NOW()
                """
            ),
            {
                "id": entry.id,
                "owner_id": entry.owner_id,
                "entity_type": entry.entity_type.value,
                "canonical_name": entry.canonical_name,
                "aliases": json.dumps(entry.aliases),
                "status": entry.status,
                "source_proposal_id": source_proposal_id,
            },
        )
        return entry


class PostgresApprovalRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def record_decision(self, decision: ApprovalDecision) -> ApprovalDecision:
        await self._session.execute(
            text(
                """
                INSERT INTO approval_decisions (
                    id, proposal_id, actor_id, action, rationale,
                    edited_payload, correlation_id, created_at
                ) VALUES (
                    :id, :proposal_id, :actor_id, :action, :rationale,
                    CAST(:edited_payload AS jsonb), :correlation_id, :created_at
                )
                """
            ),
            {
                "id": decision.id,
                "proposal_id": decision.proposal_id,
                "actor_id": decision.actor_id,
                "action": decision.action.value,
                "rationale": decision.rationale,
                "edited_payload": json.dumps(decision.edited_payload)
                if decision.edited_payload
                else None,
                "correlation_id": decision.correlation_id,
                "created_at": decision.created_at,
            },
        )
        return decision


class PostgresKnowledgeVersionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_versions_pending_knowledge(self, *, limit: int) -> list[dict[str, object]]:
        result = await self._session.execute(
            text(
                """
                SELECT sov.id AS version_id, so.source_id, s.owner_id,
                       s.default_project_id, so.external_id
                FROM source_object_versions sov
                JOIN source_objects so ON so.id = sov.source_object_id
                JOIN sources s ON s.id = so.source_id
                WHERE sov.extraction_status = 'completed'
                  AND sov.knowledge_status = 'pending'
                ORDER BY sov.observed_at
                LIMIT :limit
                """
            ),
            {"limit": limit},
        )
        return [dict(row._mapping) for row in result.fetchall()]

    async def update_knowledge_status(self, version_id: UUID, status: str) -> None:
        await self._session.execute(
            text("UPDATE source_object_versions SET knowledge_status = :status WHERE id = :id"),
            {"id": version_id, "status": status},
        )

    async def get_version_context(self, version_id: UUID) -> dict[str, object] | None:
        result = await self._session.execute(
            text(
                """
                SELECT sov.id AS version_id, so.source_id, s.owner_id,
                       s.default_project_id, so.external_id
                FROM source_object_versions sov
                JOIN source_objects so ON so.id = sov.source_object_id
                JOIN sources s ON s.id = so.source_id
                WHERE sov.id = :id
                """
            ),
            {"id": version_id},
        )
        row = result.first()
        return dict(row._mapping) if row else None
