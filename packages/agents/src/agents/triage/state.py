from typing import TypedDict
from uuid import UUID

from domain.triage import TriageClassification


class TriageState(TypedDict, total=False):
    version_id: UUID
    external_id: str
    mime_type: str | None
    source_configuration: dict[str, object]
    classification: TriageClassification
    pipeline_version: str
    error: str | None
