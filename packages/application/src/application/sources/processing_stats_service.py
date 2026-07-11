from typing import Protocol
from uuid import UUID

from application.policy import LocalPolicyService
from domain.identity import OwnerContext
from domain.processing_stats import ProcessingErrorSample, SourceProcessingStats, TriageSample


class SourceProcessingStatsReader(Protocol):
    async def get_stats_for_source(
        self, source_id: UUID, owner_id: UUID
    ) -> dict[str, object] | None: ...


class SourceProcessingStatsService:
    """FR-ING / doc 15 A-6 — operator visibility for pipeline progress."""

    def __init__(
        self,
        stats: SourceProcessingStatsReader,
        policy: LocalPolicyService,
    ) -> None:
        self._stats = stats
        self._policy = policy

    async def get_stats(self, owner: OwnerContext, source_id: UUID) -> SourceProcessingStats | None:
        self._policy.authorize_owner(owner, owner.owner_id)
        raw = await self._stats.get_stats_for_source(source_id, owner.owner_id)
        if raw is None:
            return None

        extraction = raw.get("extraction") or {}
        knowledge = raw.get("knowledge") or {}
        if not isinstance(extraction, dict):
            extraction = {}
        if not isinstance(knowledge, dict):
            knowledge = {}

        errors_raw = raw.get("recent_extraction_errors") or []
        errors: list[ProcessingErrorSample] = []
        if isinstance(errors_raw, list):
            for item in errors_raw:
                if isinstance(item, dict):
                    errors.append(
                        ProcessingErrorSample(
                            external_id=str(item.get("external_id", "")),
                            error=str(item.get("error", "")),
                        )
                    )

        triage_raw = raw.get("recent_triage_samples") or []
        triage_samples: list[TriageSample] = []
        if isinstance(triage_raw, list):
            for item in triage_raw:
                if isinstance(item, dict):
                    triage_samples.append(
                        TriageSample(
                            external_id=str(item.get("external_id", "")),
                            sensitivity=str(item.get("sensitivity", "low")),
                            relevance=float(item.get("relevance", 0.5)),
                            review_risk=str(item.get("review_risk", "medium")),
                            extractor_hint=str(item.get("extractor_hint", "structured")),
                        )
                    )

        extraction_counts = {str(k): int(v) for k, v in extraction.items()}
        knowledge_counts = {str(k): int(v) for k, v in knowledge.items()}
        triage_counts = raw.get("triage") or {}
        if not isinstance(triage_counts, dict):
            triage_counts = {}
        triage_status_counts = {str(k): int(v) for k, v in triage_counts.items()}
        chunks_raw = raw.get("content_chunks", 0)

        return SourceProcessingStats(
            source_id=source_id,
            extraction_pending=extraction_counts.get("pending", 0),
            extraction_completed=extraction_counts.get("completed", 0),
            extraction_failed=extraction_counts.get("failed", 0),
            extraction_skipped=extraction_counts.get("skipped", 0),
            knowledge_pending=knowledge_counts.get("pending", 0),
            knowledge_completed=knowledge_counts.get("completed", 0),
            knowledge_failed=knowledge_counts.get("failed", 0),
            knowledge_skipped=knowledge_counts.get("skipped", 0),
            triage_pending=triage_status_counts.get("pending", 0),
            triage_completed=triage_status_counts.get("completed", 0),
            content_chunks=int(chunks_raw) if isinstance(chunks_raw, (int, float, str)) else 0,
            recent_extraction_errors=errors,
            recent_triage_samples=triage_samples,
        )
