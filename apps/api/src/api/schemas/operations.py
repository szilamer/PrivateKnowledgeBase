from pydantic import BaseModel


class PipelineHealthResponse(BaseModel):
    extraction_pending: int
    extraction_failed: int
    knowledge_pending: int
    triage_pending: int
    embedding_model_mismatch_versions: int


class OperationsStatusResponse(BaseModel):
    pending_outbox_events: int
    failed_outbox_events: int
    processed_outbox_events: int
    canonical_entities: int
    canonical_claims: int
    projection_rebuild_recommended: bool
    pipeline: PipelineHealthResponse
    maintenance_recommended: bool
    status_summary_hu: str


class ProjectionRebuildResponse(BaseModel):
    entities_projected: int
    relationships_projected: int
    claims_projected: int
    contradictions_projected: int
    cleared_nodes: bool


class ProjectionRebuildAcceptedResponse(BaseModel):
    status: str
    task: str


class MaintenanceRunResponse(BaseModel):
    pipeline_recovery_enqueued: bool
    embedding_mismatch_flagged: int
    status_summary_hu: str
