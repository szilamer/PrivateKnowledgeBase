from pydantic import BaseModel, Field


class PipelineHealthSnapshot(BaseModel):
    extraction_pending: int = 0
    extraction_failed: int = 0
    knowledge_pending: int = 0
    triage_pending: int = 0
    embedding_model_mismatch_versions: int = 0


class MaintenanceActionResult(BaseModel):
    pipeline_recovery_enqueued: bool = False
    embedding_mismatch_flagged: int = 0


class OperationsStatus(BaseModel):
    pending_outbox_events: int = 0
    failed_outbox_events: int = 0
    processed_outbox_events: int = 0
    canonical_entities: int = 0
    canonical_claims: int = 0
    projection_rebuild_recommended: bool = False
    pipeline: PipelineHealthSnapshot = Field(default_factory=PipelineHealthSnapshot)
    maintenance_recommended: bool = False
    status_summary_hu: str = ""


class ProjectionRebuildResult(BaseModel):
    entities_projected: int = 0
    relationships_projected: int = 0
    claims_projected: int = 0
    contradictions_projected: int = 0
    cleared_nodes: bool = False
