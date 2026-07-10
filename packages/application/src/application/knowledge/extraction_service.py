import time
from datetime import UTC, datetime
from uuid import UUID, uuid4

from domain.audit import AuditAction, AuditEvent
from domain.entity_resolution import classify_risk, requires_review, resolve_entity
from domain.extraction import (
    EXTRACTION_PIPELINE_VERSION,
    EXTRACTION_PROMPT_VERSION,
    EXTRACTION_SCHEMA_VERSION,
    ExtractedClaim,
    ExtractedDecision,
    ExtractedEvent,
    ExtractedRelationship,
    ExtractedTask,
    ExtractionResult,
    ExtractionRunStatus,
)
from domain.proposals import (
    EvidenceSpan,
    KnowledgeProposal,
    ProposalStatus,
    ProposalType,
    RiskLevel,
)

from application.ports.content import ChunkRepository
from application.ports.knowledge import (
    AuditWriter,
    EntityIndexRepository,
    ExtractionRunRepository,
    KnowledgeExtractorPort,
    KnowledgeVersionRepository,
    LLMProvider,
    ProposalRepository,
)


class KnowledgeExtractionService:
    """Phase 3 — structured extraction, entity resolution, proposal creation."""

    def __init__(
        self,
        versions: KnowledgeVersionRepository,
        chunks: ChunkRepository,
        proposals: ProposalRepository,
        runs: ExtractionRunRepository,
        entities: EntityIndexRepository,
        llm: LLMProvider | None,
        heuristic: KnowledgeExtractorPort,
        audit: AuditWriter,
    ) -> None:
        self._versions = versions
        self._chunks = chunks
        self._proposals = proposals
        self._runs = runs
        self._entities = entities
        self._llm = llm
        self._heuristic = heuristic
        self._audit = audit

    async def process_pending(self, *, batch_size: int = 10) -> int:
        pending = await self._versions.get_versions_pending_knowledge(limit=batch_size)
        processed = 0
        for row in pending:
            version_id = UUID(str(row["version_id"]))
            try:
                await self.extract_version(version_id)
                processed += 1
            except Exception:  # noqa: BLE001
                await self._versions.update_knowledge_status(version_id, "failed")
        return processed

    async def extract_version(self, version_id: UUID, *, correlation_id: str | None = None) -> int:
        context = await self._versions.get_version_context(version_id)
        if context is None:
            msg = f"Version not found: {version_id}"
            raise ValueError(msg)

        owner_id = UUID(str(context["owner_id"]))
        source_id = UUID(str(context["source_id"]))
        project_id = (
            UUID(str(context["default_project_id"])) if context.get("default_project_id") else None
        )

        await self._versions.update_knowledge_status(version_id, "processing")
        run_id = uuid4()
        model = self._llm.model if self._llm else None
        provider = self._llm.provider if self._llm else "heuristic"

        await self._runs.create_run(
            run_id=run_id,
            source_object_version_id=version_id,
            owner_id=owner_id,
            model=model,
            provider=provider,
            prompt_version=EXTRACTION_PROMPT_VERSION,
            schema_version=EXTRACTION_SCHEMA_VERSION,
            pipeline_version=EXTRACTION_PIPELINE_VERSION,
            correlation_id=correlation_id,
        )

        started = time.monotonic()
        chunk_models = await self._chunks.list_by_version(version_id)
        if not chunk_models:
            await self._versions.update_knowledge_status(version_id, "skipped")
            await self._runs.complete_run(run_id, status=ExtractionRunStatus.COMPLETED)
            return 0

        full_text = "\n\n".join(chunk.text for chunk in chunk_models)
        chunk_pairs = [(chunk.id, chunk.text) for chunk in chunk_models]

        result = await self._run_extraction(full_text, chunk_pairs)
        created = await self._persist_proposals(
            result=result,
            run_id=run_id,
            version_id=version_id,
            owner_id=owner_id,
            source_id=source_id,
            project_id=project_id,
        )

        latency_ms = int((time.monotonic() - started) * 1000)
        await self._runs.complete_run(
            run_id,
            status=ExtractionRunStatus.COMPLETED,
            latency_ms=latency_ms,
        )
        await self._versions.update_knowledge_status(version_id, "completed")
        await self._record_audit(
            owner_id,
            AuditAction.EXTRACTION_COMPLETED,
            run_id,
            correlation_id or str(run_id),
            {"version_id": str(version_id), "proposals": created},
        )
        return created

    async def _run_extraction(
        self, text: str, chunk_pairs: list[tuple[UUID, str]]
    ) -> ExtractionResult:
        if self._llm is not None:
            try:
                return await self._llm.extract_knowledge(text, EXTRACTION_SCHEMA_VERSION)
            except Exception:  # noqa: BLE001 — fallback to heuristic
                pass
        return self._heuristic.extract(text, chunk_pairs)

    async def _persist_proposals(
        self,
        *,
        result: ExtractionResult,
        run_id: UUID,
        version_id: UUID,
        owner_id: UUID,
        source_id: UUID,
        project_id: UUID | None,
    ) -> int:
        now = datetime.now(UTC)
        created = 0

        for entity in result.entities:
            matches = await self._entities.find_matches(
                owner_id, entity.name, entity.entity_type.value
            )
            action, resolution_matches = resolve_entity(entity, matches)
            risk = classify_risk(entity.entity_type, entity.confidence)
            proposal_type = (
                ProposalType.ENTITY_RESOLUTION if action == "ambiguous" else ProposalType.ENTITY
            )
            payload: dict[str, object] = entity.model_dump(mode="json")
            if action == "link" and resolution_matches:
                payload["resolved_entity_id"] = str(resolution_matches[0].entity_id)
            if action == "ambiguous":
                payload["candidates"] = [
                    match.model_dump(mode="json") for match in resolution_matches
                ]

            proposal = KnowledgeProposal(
                id=uuid4(),
                owner_id=owner_id,
                extraction_run_id=run_id,
                proposal_type=proposal_type,
                status=ProposalStatus.PENDING,
                risk_level=RiskLevel(risk),
                confidence=entity.confidence,
                title=entity.name,
                payload=payload,
                project_id=project_id,
                source_id=source_id,
                requires_review=requires_review(risk, proposal_type.value),
                created_at=now,
                updated_at=now,
                evidence=[
                    EvidenceSpan(
                        id=uuid4(),
                        proposal_id=uuid4(),
                        source_object_version_id=version_id,
                        content_chunk_id=entity.chunk_id,
                        anchor_start=entity.anchor_start,
                        anchor_end=entity.anchor_end,
                        excerpt=entity.name,
                    )
                ],
            )
            proposal.evidence[0].proposal_id = proposal.id
            await self._proposals.create_proposal(proposal)
            created += 1

        for task in result.tasks:
            created += await self._create_typed_proposal(
                entry=task,
                proposal_type=ProposalType.TASK,
                title_key="title",
                run_id=run_id,
                version_id=version_id,
                owner_id=owner_id,
                source_id=source_id,
                project_id=project_id,
                now=now,
            )
        for decision in result.decisions:
            created += await self._create_typed_proposal(
                entry=decision,
                proposal_type=ProposalType.DECISION,
                title_key="title",
                run_id=run_id,
                version_id=version_id,
                owner_id=owner_id,
                source_id=source_id,
                project_id=project_id,
                now=now,
            )
        for event in result.events:
            created += await self._create_typed_proposal(
                entry=event,
                proposal_type=ProposalType.EVENT,
                title_key="title",
                run_id=run_id,
                version_id=version_id,
                owner_id=owner_id,
                source_id=source_id,
                project_id=project_id,
                now=now,
            )
        for claim in result.claims:
            created += await self._create_typed_proposal(
                entry=claim,
                proposal_type=ProposalType.CLAIM,
                title_key="predicate",
                run_id=run_id,
                version_id=version_id,
                owner_id=owner_id,
                source_id=source_id,
                project_id=project_id,
                now=now,
            )
        for relationship in result.relationships:
            created += await self._create_typed_proposal(
                entry=relationship,
                proposal_type=ProposalType.RELATIONSHIP,
                title_key="relationship_type",
                run_id=run_id,
                version_id=version_id,
                owner_id=owner_id,
                source_id=source_id,
                project_id=project_id,
                now=now,
            )

        return created

    async def _create_typed_proposal(
        self,
        *,
        entry: ExtractedTask
        | ExtractedDecision
        | ExtractedEvent
        | ExtractedClaim
        | ExtractedRelationship,
        proposal_type: ProposalType,
        title_key: str,
        run_id: UUID,
        version_id: UUID,
        owner_id: UUID,
        source_id: UUID,
        project_id: UUID | None,
        now: datetime,
    ) -> int:
        confidence = float(entry.confidence)
        if confidence < 0.6:
            risk = "high"
        elif confidence >= 0.85:
            risk = "low"
        else:
            risk = "medium"
        title = str(getattr(entry, title_key, proposal_type.value))
        proposal = KnowledgeProposal(
            id=uuid4(),
            owner_id=owner_id,
            extraction_run_id=run_id,
            proposal_type=proposal_type,
            status=ProposalStatus.PENDING,
            risk_level=RiskLevel(risk),
            confidence=entry.confidence,
            title=title,
            payload=entry.model_dump(mode="json"),
            project_id=project_id,
            source_id=source_id,
            requires_review=requires_review(risk, proposal_type.value),
            created_at=now,
            updated_at=now,
            evidence=[
                EvidenceSpan(
                    id=uuid4(),
                    proposal_id=uuid4(),
                    source_object_version_id=version_id,
                    content_chunk_id=getattr(entry, "chunk_id", None),
                    anchor_start=getattr(entry, "anchor_start", None),
                    anchor_end=getattr(entry, "anchor_end", None),
                    excerpt=title,
                )
            ],
        )
        proposal.evidence[0].proposal_id = proposal.id
        await self._proposals.create_proposal(proposal)
        return 1

    async def _record_audit(
        self,
        actor_id: UUID,
        action: AuditAction,
        object_id: UUID,
        correlation_id: str,
        metadata: dict[str, object],
    ) -> None:
        if hasattr(self._audit, "append"):
            event = AuditEvent(
                id=uuid4(),
                actor_id=actor_id,
                action=action,
                object_type="extraction_run",
                object_id=object_id,
                correlation_id=correlation_id,
                metadata=metadata,
                created_at=datetime.now(UTC),
            )
            await self._audit.append(event)
