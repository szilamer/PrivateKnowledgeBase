import json
import time
from datetime import UTC, datetime
from uuid import UUID, uuid4

from domain.audit import AuditAction, AuditEvent
from domain.entity_resolution import requires_review
from domain.entity_resolution_outcome import EntityResolutionProposalSpec
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
from domain.extraction_outcome import ExtractionLLMResult, ExtractionOutcome
from domain.proposals import (
    EvidenceSpan,
    KnowledgeProposal,
    ProposalStatus,
    ProposalType,
    RiskLevel,
)
from domain.triage import triage_floor_risk, triage_requires_review

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
        *,
        use_langgraph: bool = True,
    ) -> None:
        self._versions = versions
        self._chunks = chunks
        self._proposals = proposals
        self._runs = runs
        self._entities = entities
        self._llm = llm
        self._heuristic = heuristic
        self._audit = audit
        self._use_langgraph = use_langgraph

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
        triage_metadata = self._parse_triage_metadata(context)

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

        graph_meta: dict[str, object] = {}
        if self._use_langgraph:
            created, graph_meta = await self._extract_via_langgraph(
                version_id=version_id,
                owner_id=owner_id,
                source_id=source_id,
                project_id=project_id,
                run_id=run_id,
                triage_metadata=triage_metadata,
            )
        else:
            full_text = "\n\n".join(chunk.text for chunk in chunk_models)
            chunk_pairs = [(chunk.id, chunk.text) for chunk in chunk_models]
            outcome = await self._run_extraction_outcome(full_text, chunk_pairs)
            created, review_count = await self._persist_proposals_with_review_count(
                result=outcome.result,
                run_id=run_id,
                version_id=version_id,
                owner_id=owner_id,
                source_id=source_id,
                project_id=project_id,
                triage_metadata=triage_metadata,
            )
            graph_meta = {
                "provider": outcome.provider,
                "fallback_used": outcome.fallback_used,
                "token_usage": outcome.token_usage,
                "requires_review_count": review_count,
            }

        if graph_meta.get("validation_failed"):
            latency_ms = int((time.monotonic() - started) * 1000)
            error_summary = str(graph_meta.get("error") or "validation failed")
            await self._runs.complete_run(
                run_id,
                status=ExtractionRunStatus.FAILED,
                latency_ms=latency_ms,
                error_summary=error_summary,
                token_usage=graph_meta.get("token_usage"),  # type: ignore[arg-type]
            )
            await self._versions.update_knowledge_status(version_id, "failed")
            await self._record_audit(
                owner_id,
                AuditAction.EXTRACTION_COMPLETED,
                run_id,
                correlation_id or str(run_id),
                {
                    "version_id": str(version_id),
                    "status": "failed",
                    "error": error_summary,
                    **{k: v for k, v in graph_meta.items() if k != "token_usage"},
                },
            )
            return 0

        latency_ms = int((time.monotonic() - started) * 1000)
        token_usage = graph_meta.get("token_usage")
        await self._runs.complete_run(
            run_id,
            status=ExtractionRunStatus.COMPLETED,
            latency_ms=latency_ms,
            token_usage=token_usage if isinstance(token_usage, dict) else None,
        )
        await self._versions.update_knowledge_status(version_id, "completed")
        await self._record_audit(
            owner_id,
            AuditAction.EXTRACTION_COMPLETED,
            run_id,
            correlation_id or str(run_id),
            {
                "version_id": str(version_id),
                "proposals": created,
                "provider": graph_meta.get("provider"),
                "fallback_used": graph_meta.get("fallback_used"),
                "requires_review_count": graph_meta.get("requires_review_count", 0),
            },
        )
        return created

    async def _extract_via_langgraph(
        self,
        *,
        version_id: UUID,
        owner_id: UUID,
        source_id: UUID,
        project_id: UUID | None,
        run_id: UUID,
        triage_metadata: dict[str, object] | None = None,
    ) -> tuple[int, dict[str, object]]:
        from agents.extraction.graph import build_extraction_graph
        from agents.extraction.state import ExtractionState

        async def load_chunks(vid: UUID) -> list[tuple[UUID, str]]:
            chunk_models = await self._chunks.list_by_version(vid)
            return [(chunk.id, chunk.text) for chunk in chunk_models]

        async def try_llm(
            text: str, chunk_pairs: list[tuple[UUID, str]]
        ) -> ExtractionLLMResult | None:
            if self._llm is None:
                return None
            try:
                return await self._llm.extract_knowledge(text, EXTRACTION_SCHEMA_VERSION)
            except Exception as exc:  # noqa: BLE001
                _ = chunk_pairs
                return None if "unavailable" in str(exc).lower() else None

        async def persist_proposals(
            state: ExtractionState, extraction: ExtractionResult
        ) -> tuple[int, int]:
            return await self._persist_proposals_with_review_count(
                result=extraction,
                run_id=run_id,
                version_id=state["version_id"],
                owner_id=state["owner_id"],
                source_id=state["source_id"],
                project_id=state.get("project_id"),
                triage_metadata=triage_metadata,
            )

        graph = build_extraction_graph(
            load_chunks=load_chunks,
            try_llm_extraction=try_llm,
            run_heuristic_extraction=self._heuristic.extract,
            persist_proposals=persist_proposals,
            llm_available=self._llm is not None,
        )
        final = await graph.ainvoke(
            {
                "version_id": version_id,
                "owner_id": owner_id,
                "source_id": source_id,
                "project_id": project_id,
            }
        )

        validation_passed = bool(final.get("validation_passed"))
        meta: dict[str, object] = {
            "provider": final.get("provider"),
            "fallback_used": final.get("fallback_used", False),
            "token_usage": final.get("token_usage"),
            "requires_review_count": final.get("requires_review_count", 0),
            "validation_errors": final.get("validation_errors", []),
        }
        if not validation_passed:
            meta["validation_failed"] = True
            meta["error"] = final.get("error") or "validation failed"
            return 0, meta

        return int(final.get("proposal_count", 0)), meta

    async def _run_extraction_outcome(
        self, text: str, chunk_pairs: list[tuple[UUID, str]]
    ) -> ExtractionOutcome:
        if self._llm is not None:
            try:
                llm_result = await self._llm.extract_knowledge(text, EXTRACTION_SCHEMA_VERSION)
                return ExtractionOutcome(
                    result=llm_result.result,
                    provider="llm",
                    fallback_used=False,
                    token_usage=llm_result.token_usage,
                )
            except Exception as exc:  # noqa: BLE001
                return ExtractionOutcome(
                    result=self._heuristic.extract(text, chunk_pairs),
                    provider="heuristic",
                    fallback_used=True,
                    llm_error=str(exc)[:200],
                )
        return ExtractionOutcome(
            result=self._heuristic.extract(text, chunk_pairs),
            provider="heuristic",
            fallback_used=False,
        )

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
        created, _ = await self._persist_proposals_with_review_count(
            result=result,
            run_id=run_id,
            version_id=version_id,
            owner_id=owner_id,
            source_id=source_id,
            project_id=project_id,
        )
        return created

    async def _persist_proposals_with_review_count(
        self,
        *,
        result: ExtractionResult,
        run_id: UUID,
        version_id: UUID,
        owner_id: UUID,
        source_id: UUID,
        project_id: UUID | None,
        triage_metadata: dict[str, object] | None = None,
    ) -> tuple[int, int]:
        now = datetime.now(UTC)
        created = 0
        review_count = 0
        triage_meta = triage_metadata or {}

        for entity in result.entities:
            spec = await self._resolve_entity_via_graph(entity, owner_id)
            risk, needs_review_flag = self._apply_triage_policy(
                spec.risk_level,
                spec.needs_review,
                triage_meta,
            )
            proposal = KnowledgeProposal(
                id=uuid4(),
                owner_id=owner_id,
                extraction_run_id=run_id,
                proposal_type=spec.proposal_type,
                status=ProposalStatus.PENDING,
                risk_level=RiskLevel(risk),
                confidence=entity.confidence,
                title=entity.name,
                payload=spec.payload,
                project_id=project_id,
                source_id=source_id,
                requires_review=needs_review_flag,
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
            if needs_review_flag:
                review_count += 1

        for task in result.tasks:
            created, review_count = await self._append_typed_proposal(
                entry=task,
                proposal_type=ProposalType.TASK,
                title_key="title",
                run_id=run_id,
                version_id=version_id,
                owner_id=owner_id,
                source_id=source_id,
                project_id=project_id,
                now=now,
                created=created,
                review_count=review_count,
                triage_metadata=triage_meta,
            )
        for decision in result.decisions:
            created, review_count = await self._append_typed_proposal(
                entry=decision,
                proposal_type=ProposalType.DECISION,
                title_key="title",
                run_id=run_id,
                version_id=version_id,
                owner_id=owner_id,
                source_id=source_id,
                project_id=project_id,
                now=now,
                created=created,
                review_count=review_count,
                triage_metadata=triage_meta,
            )
        for event in result.events:
            created, review_count = await self._append_typed_proposal(
                entry=event,
                proposal_type=ProposalType.EVENT,
                title_key="title",
                run_id=run_id,
                version_id=version_id,
                owner_id=owner_id,
                source_id=source_id,
                project_id=project_id,
                now=now,
                created=created,
                review_count=review_count,
                triage_metadata=triage_meta,
            )
        for claim in result.claims:
            created, review_count = await self._append_typed_proposal(
                entry=claim,
                proposal_type=ProposalType.CLAIM,
                title_key="predicate",
                run_id=run_id,
                version_id=version_id,
                owner_id=owner_id,
                source_id=source_id,
                project_id=project_id,
                now=now,
                created=created,
                review_count=review_count,
                triage_metadata=triage_meta,
            )
        for relationship in result.relationships:
            created, review_count = await self._append_typed_proposal(
                entry=relationship,
                proposal_type=ProposalType.RELATIONSHIP,
                title_key="relationship_type",
                run_id=run_id,
                version_id=version_id,
                owner_id=owner_id,
                source_id=source_id,
                project_id=project_id,
                now=now,
                created=created,
                review_count=review_count,
                triage_metadata=triage_meta,
            )

        return created, review_count

    async def _append_typed_proposal(
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
        created: int,
        review_count: int,
        triage_metadata: dict[str, object] | None = None,
    ) -> tuple[int, int]:
        added, needs_review_flag = await self._create_typed_proposal(
            entry=entry,
            proposal_type=proposal_type,
            title_key=title_key,
            run_id=run_id,
            version_id=version_id,
            owner_id=owner_id,
            source_id=source_id,
            project_id=project_id,
            now=now,
            triage_metadata=triage_metadata or {},
        )
        if added and needs_review_flag:
            review_count += 1
        return created + added, review_count

    @staticmethod
    def _risk_for_entry(
        entry: ExtractedTask
        | ExtractedDecision
        | ExtractedEvent
        | ExtractedClaim
        | ExtractedRelationship,
    ) -> str:
        confidence = float(entry.confidence)
        if confidence < 0.6:
            return "high"
        if confidence >= 0.85:
            return "low"
        return "medium"

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
        triage_metadata: dict[str, object] | None = None,
    ) -> tuple[int, bool]:
        confidence = float(entry.confidence)
        base_risk = self._risk_for_entry(entry)
        base_review = requires_review(base_risk, proposal_type.value, confidence=confidence)
        risk, needs_review_flag = self._apply_triage_policy(
            base_risk,
            base_review,
            triage_metadata or {},
        )
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
            requires_review=needs_review_flag,
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
        return 1, needs_review_flag

    async def _resolve_entity_via_graph(
        self,
        entity: object,
        owner_id: UUID,
    ) -> EntityResolutionProposalSpec:
        from agents.entity_resolution.graph import build_entity_resolution_graph
        from domain.extraction import ExtractedEntity

        assert isinstance(entity, ExtractedEntity)
        graph = build_entity_resolution_graph(find_matches=self._entities.find_matches)
        final = await graph.ainvoke({"entity": entity, "owner_id": owner_id})
        return EntityResolutionProposalSpec(
            entity=entity,
            resolution_action=str(final.get("resolution_action", "new")),
            proposal_type=ProposalType(str(final.get("proposal_type", ProposalType.ENTITY.value))),
            payload=dict(final.get("payload", {})),
            needs_review=bool(final.get("needs_review", True)),
            risk_level=str(final.get("risk_level", RiskLevel.MEDIUM.value)),
            candidates=list(final.get("resolution_matches", [])),
        )

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

    @staticmethod
    def _parse_triage_metadata(context: dict[str, object]) -> dict[str, object]:
        raw = context.get("triage_metadata")
        if raw is None:
            return {}
        if isinstance(raw, str):
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError:
                return {}
            return dict(parsed) if isinstance(parsed, dict) else {}
        if isinstance(raw, dict):
            return dict(raw)
        return {}

    @staticmethod
    def _apply_triage_policy(
        risk: str,
        needs_review: bool,
        triage_metadata: dict[str, object],
    ) -> tuple[str, bool]:
        floored = triage_floor_risk(risk, triage_metadata)
        flagged = needs_review or triage_requires_review(triage_metadata)
        return floored, flagged
