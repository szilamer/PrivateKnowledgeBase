const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type OperationsStatus = {
  pending_outbox_events: number;
  failed_outbox_events: number;
  processed_outbox_events: number;
  canonical_entities: number;
  canonical_claims: number;
  projection_rebuild_recommended: boolean;
  pipeline: {
    extraction_pending: number;
    extraction_failed: number;
    knowledge_pending: number;
    triage_pending: number;
    embedding_model_mismatch_versions: number;
  };
  maintenance_recommended: boolean;
  status_summary_hu: string;
};

export type MaintenanceRunResult = {
  pipeline_recovery_enqueued: boolean;
  embedding_mismatch_flagged: number;
  status_summary_hu: string;
};

export async function fetchOperationsStatus(): Promise<OperationsStatus | null> {
  const response = await fetch(`${API_URL}/api/v1/operations/status`, { cache: "no-store" });
  if (!response.ok) return null;
  return response.json();
}

export async function runMaintenanceRecovery(): Promise<MaintenanceRunResult | null> {
  const response = await fetch(`${API_URL}/api/v1/operations/maintenance/run`, {
    method: "POST",
  });
  if (!response.ok) return null;
  return response.json();
}

export async function rebuildProjection(asyncMode = true): Promise<boolean> {
  const response = await fetch(
    `${API_URL}/api/v1/operations/projection/rebuild?async=${asyncMode ? "true" : "false"}`,
    { method: "POST" },
  );
  return response.ok;
}
