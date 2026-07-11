from typing import Protocol
from uuid import UUID

from domain.approval import ApprovalDecision
from domain.audit import AuditEvent  # noqa: F401 — used in AuditWriter Protocol
from domain.entities import EntityIndexEntry, EntityMatch
from domain.extraction import ExtractionResult, ExtractionRunStatus
from domain.extraction_outcome import ExtractionLLMResult
from domain.proposals import KnowledgeProposal, ProposalFilter


class KnowledgeExtractorPort(Protocol):
    def extract(self, text: str, chunks: list[tuple[UUID, str]]) -> ExtractionResult: ...


class AuditWriter(Protocol):
    async def append(self, event: AuditEvent) -> None: ...


class LLMProvider(Protocol):
    model: str
    provider: str

    async def extract_knowledge(self, text: str, schema_version: str) -> ExtractionLLMResult: ...


class ProposalRepository(Protocol):
    async def create_proposal(self, proposal: KnowledgeProposal) -> KnowledgeProposal: ...

    async def get_by_id(self, proposal_id: UUID, owner_id: UUID) -> KnowledgeProposal | None: ...

    async def list_proposals(
        self, owner_id: UUID, filters: ProposalFilter
    ) -> tuple[list[KnowledgeProposal], UUID | None]: ...

    async def update_status(
        self,
        proposal_id: UUID,
        owner_id: UUID,
        status: str,
        *,
        payload: dict[str, object] | None = None,
        original_payload: dict[str, object] | None = None,
    ) -> KnowledgeProposal | None: ...

    async def create_evidence(
        self,
        proposal_id: UUID,
        *,
        source_object_version_id: UUID,
        content_chunk_id: UUID | None,
        anchor_start: int | None,
        anchor_end: int | None,
        excerpt: str | None,
    ) -> None: ...


class ExtractionRunRepository(Protocol):
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
    ) -> None: ...

    async def complete_run(
        self,
        run_id: UUID,
        *,
        status: ExtractionRunStatus,
        token_usage: dict[str, object] | None = None,
        latency_ms: int | None = None,
        error_summary: str | None = None,
    ) -> None: ...


class EntityIndexRepository(Protocol):
    async def find_matches(
        self, owner_id: UUID, name: str, entity_type: str, *, limit: int = 5
    ) -> list[EntityMatch]: ...

    async def upsert_from_proposal(
        self, entry: EntityIndexEntry, *, source_proposal_id: UUID
    ) -> EntityIndexEntry: ...

    async def append_alias(
        self,
        owner_id: UUID,
        entity_id: UUID,
        alias: str,
        *,
        source_proposal_id: UUID,
    ) -> None: ...


class ApprovalRepository(Protocol):
    async def record_decision(self, decision: ApprovalDecision) -> ApprovalDecision: ...


class KnowledgeVersionRepository(Protocol):
    async def get_versions_pending_knowledge(self, *, limit: int) -> list[dict[str, object]]: ...

    async def count_pending_knowledge(self) -> int: ...

    async def update_knowledge_status(self, version_id: UUID, status: str) -> None: ...

    async def get_version_context(self, version_id: UUID) -> dict[str, object] | None: ...
