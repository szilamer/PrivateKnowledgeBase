from datetime import datetime

from pydantic import BaseModel, Field


class OntologyProposalResponse(BaseModel):
    id: str
    kind: str
    status: str
    title: str
    rationale: str
    proposed_definition: dict[str, object]
    evidence: dict[str, object]
    ontology_version: str
    decision_rationale: str | None = None
    created_at: datetime
    updated_at: datetime
    decided_at: datetime | None = None


class OntologyProposalListResponse(BaseModel):
    items: list[OntologyProposalResponse] = Field(default_factory=list)


class OntologyScanResponse(BaseModel):
    created_count: int
    items: list[OntologyProposalResponse] = Field(default_factory=list)


class OntologyDecisionRequest(BaseModel):
    rationale: str | None = None
