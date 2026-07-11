import json
from datetime import UTC, datetime
from uuid import UUID

from domain.report import (
    ProjectReportArtifact,
    ProjectReportRequest,
    ProjectReportStatus,
)
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


def _parse_job(row: object, mapping: dict[str, object]) -> ProjectReportArtifact:
    citations_raw = mapping.get("citations") or []
    if isinstance(citations_raw, str):
        try:
            citations_raw = json.loads(citations_raw)
        except json.JSONDecodeError:
            citations_raw = []
    citations = [str(item) for item in citations_raw] if isinstance(citations_raw, list) else []

    provenance_raw = mapping.get("provenance") or {}
    if isinstance(provenance_raw, str):
        try:
            provenance_raw = json.loads(provenance_raw)
        except json.JSONDecodeError:
            provenance_raw = {}
    provenance = dict(provenance_raw) if isinstance(provenance_raw, dict) else {}

    return ProjectReportArtifact(
        id=mapping["id"],  # type: ignore[arg-type]
        owner_id=mapping["owner_id"],  # type: ignore[arg-type]
        project_entity_id=mapping["project_entity_id"],  # type: ignore[arg-type]
        status=ProjectReportStatus(str(mapping["status"])),
        title=str(mapping.get("title") or ""),
        markdown=str(mapping["markdown"]) if mapping.get("markdown") else None,
        citations=citations,
        provenance=provenance,
        period_start=mapping.get("period_start"),  # type: ignore[arg-type]
        period_end=mapping.get("period_end"),  # type: ignore[arg-type]
        error_summary=str(mapping["error_summary"]) if mapping.get("error_summary") else None,
        created_at=mapping["created_at"],  # type: ignore[arg-type]
        completed_at=mapping.get("completed_at"),  # type: ignore[arg-type]
    )


class PostgresProjectReportRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_job(
        self,
        *,
        job_id: UUID,
        owner_id: UUID,
        request: ProjectReportRequest,
        title: str,
    ) -> ProjectReportArtifact:
        now = datetime.now(UTC)
        await self._session.execute(
            text(
                """
                INSERT INTO project_reports (
                    id, owner_id, project_entity_id, status, title,
                    period_start, period_end, created_at
                ) VALUES (
                    :id, :owner_id, :project_entity_id, :status, :title,
                    :period_start, :period_end, :created_at
                )
                """
            ),
            {
                "id": job_id,
                "owner_id": owner_id,
                "project_entity_id": request.project_entity_id,
                "status": ProjectReportStatus.PENDING.value,
                "title": title,
                "period_start": request.start_at,
                "period_end": request.end_at,
                "created_at": now,
            },
        )
        return ProjectReportArtifact(
            id=job_id,
            owner_id=owner_id,
            project_entity_id=request.project_entity_id,
            status=ProjectReportStatus.PENDING,
            title=title,
            period_start=request.start_at,
            period_end=request.end_at,
            created_at=now,
        )

    async def get_job(self, job_id: UUID, owner_id: UUID) -> ProjectReportArtifact | None:
        result = await self._session.execute(
            text(
                """
                SELECT * FROM project_reports
                WHERE id = :id AND owner_id = :owner_id
                """
            ),
            {"id": job_id, "owner_id": owner_id},
        )
        row = result.first()
        if row is None:
            return None
        return _parse_job(row, dict(row._mapping))

    async def mark_running(self, job_id: UUID) -> None:
        await self._session.execute(
            text("UPDATE project_reports SET status = :status WHERE id = :id"),
            {"id": job_id, "status": ProjectReportStatus.RUNNING.value},
        )

    async def complete_job(
        self,
        job_id: UUID,
        *,
        title: str,
        markdown: str,
        citations: list[str],
        provenance: dict[str, object],
    ) -> None:
        now = datetime.now(UTC)
        await self._session.execute(
            text(
                """
                UPDATE project_reports
                SET status = :status,
                    title = :title,
                    markdown = :markdown,
                    citations = CAST(:citations AS jsonb),
                    provenance = CAST(:provenance AS jsonb),
                    completed_at = :completed_at
                WHERE id = :id
                """
            ),
            {
                "id": job_id,
                "status": ProjectReportStatus.COMPLETED.value,
                "title": title,
                "markdown": markdown,
                "citations": json.dumps(citations),
                "provenance": json.dumps(provenance),
                "completed_at": now,
            },
        )

    async def fail_job(self, job_id: UUID, *, error_summary: str) -> None:
        now = datetime.now(UTC)
        await self._session.execute(
            text(
                """
                UPDATE project_reports
                SET status = :status,
                    error_summary = :error_summary,
                    completed_at = :completed_at
                WHERE id = :id
                """
            ),
            {
                "id": job_id,
                "status": ProjectReportStatus.FAILED.value,
                "error_summary": error_summary,
                "completed_at": now,
            },
        )
