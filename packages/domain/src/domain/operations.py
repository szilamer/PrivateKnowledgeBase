from pydantic import BaseModel


class OperationsStatus(BaseModel):
    pending_outbox_events: int = 0
    failed_outbox_events: int = 0
    processed_outbox_events: int = 0
    canonical_entities: int = 0
    canonical_claims: int = 0
    projection_rebuild_recommended: bool = False


class ProjectionRebuildResult(BaseModel):
    entities_projected: int = 0
    relationships_projected: int = 0
    claims_projected: int = 0
    contradictions_projected: int = 0
    cleared_nodes: bool = False
