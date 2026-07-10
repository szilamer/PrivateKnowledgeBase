from pydantic import BaseModel


class OperationsStatusResponse(BaseModel):
    pending_outbox_events: int
    failed_outbox_events: int
    processed_outbox_events: int
    canonical_entities: int
    canonical_claims: int
    projection_rebuild_recommended: bool


class ProjectionRebuildResponse(BaseModel):
    entities_projected: int
    relationships_projected: int
    claims_projected: int
    contradictions_projected: int
    cleared_nodes: bool


class ProjectionRebuildAcceptedResponse(BaseModel):
    status: str
    task: str
