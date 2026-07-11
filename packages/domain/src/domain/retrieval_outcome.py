from dataclasses import dataclass
from uuid import UUID

from domain.questions import Citation, RetrievalPlanStep

RETRIEVAL_PIPELINE_VERSION = "v1"


@dataclass(frozen=True)
class RetrievalPlanningOutcome:
    citations: list[Citation]
    plan: list[RetrievalPlanStep]
    related_entity_ids: list[UUID]
    citation_ids: list[str]
    pipeline_version: str = RETRIEVAL_PIPELINE_VERSION
