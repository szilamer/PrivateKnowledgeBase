from typing import Protocol
from uuid import UUID

from domain.report import ProjectReportArtifact, ProjectReportRequest


class ProjectReportRepository(Protocol):
    async def create_job(
        self,
        *,
        job_id: UUID,
        owner_id: UUID,
        request: ProjectReportRequest,
        title: str,
    ) -> ProjectReportArtifact: ...

    async def get_job(self, job_id: UUID, owner_id: UUID) -> ProjectReportArtifact | None: ...

    async def mark_running(self, job_id: UUID) -> None: ...

    async def complete_job(
        self,
        job_id: UUID,
        *,
        title: str,
        markdown: str,
        citations: list[str],
        provenance: dict[str, object],
    ) -> None: ...

    async def fail_job(self, job_id: UUID, *, error_summary: str) -> None: ...
