from datetime import datetime
from typing import TypedDict
from uuid import UUID

from domain.report import ProjectSubgraphData


class ReportState(TypedDict, total=False):
    owner_id: UUID
    project_entity_id: UUID
    start_at: datetime | None
    end_at: datetime | None
    subgraph: ProjectSubgraphData
    summary: str
    markdown: str
    title: str
    pipeline_version: str
    error: str | None
