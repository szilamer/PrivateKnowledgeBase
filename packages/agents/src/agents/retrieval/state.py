from typing import TypedDict
from uuid import UUID

from domain.questions import Citation, RetrievalPlanStep


class RetrievalState(TypedDict, total=False):
    owner_id: UUID
    question: str
    mode: str
    limit: int
    citations: dict[str, Citation]
    plan: list[RetrievalPlanStep]
    related_entities: list[UUID]
    citation_ids: list[str]
    pipeline_version: str
    error: str | None
