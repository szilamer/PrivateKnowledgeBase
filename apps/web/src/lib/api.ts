import { getBrowserApiUrl } from "./api-url";

export type SourceType =
  | "local_folder"
  | "github"
  | "google_drive"
  | "gmail"
  | "google_calendar";

export type Source = {
  id: string;
  type: SourceType;
  name: string;
  enabled: boolean;
  configuration: Record<string, unknown>;
};

export type SyncRun = {
  id: string;
  source_id: string;
  mode: string;
  status: string;
  objects_discovered: number;
  objects_processed: number;
  objects_failed: number;
  error_summary: string | null;
  completed_at?: string | null;
  started_at?: string | null;
};

export type GoogleAccount = {
  id: string;
  provider: string;
  account_alias: string;
  email: string | null;
};

export type SourcesHealth = {
  status: string;
  config_loaded: boolean;
  source_count: number;
  errors: string[];
  google_connectors_enabled: boolean;
};

const API_URL = getBrowserApiUrl();

export type LocalBrowseEntry = {
  name: string;
  path: string;
  has_children: boolean;
};

export type LocalBrowseResult = {
  path: string;
  parent_path: string | null;
  entries: LocalBrowseEntry[];
  can_select: boolean;
  readable: boolean;
  error: string | null;
};

export async function browseLocalFolder(path: string = "~"): Promise<LocalBrowseResult | null> {
  const params = new URLSearchParams({ path });
  const response = await fetch(`${API_URL}/api/v1/sources/local/browse?${params.toString()}`, {
    cache: "no-store",
  });
  if (!response.ok) return null;
  return response.json();
}

export async function listSources(): Promise<Source[]> {
  const response = await fetch(`${API_URL}/api/v1/sources`, { cache: "no-store" });
  if (!response.ok) return [];
  const data = await response.json();
  return data.items ?? [];
}

export async function registerLocalSource(input: {
  name: string;
  paths: string[];
  file_extensions?: string[];
  exclude_globs?: string[];
}): Promise<Source | null> {
  const response = await fetch(`${API_URL}/api/v1/sources/local`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  if (!response.ok) return null;
  return response.json();
}

export async function putSourcesConfig(config: Record<string, unknown>): Promise<boolean> {
  const response = await fetch(`${API_URL}/api/v1/sources/config`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ config }),
  });
  return response.ok;
}

export async function getSourcesHealth(): Promise<SourcesHealth | null> {
  const response = await fetch(`${API_URL}/api/v1/sources/health`, { cache: "no-store" });
  if (!response.ok) return null;
  return response.json();
}

export type TriageSample = {
  external_id: string;
  sensitivity: string;
  relevance: number;
  review_risk: string;
  extractor_hint: string;
};

export type SourceProcessingStats = {
  source_id: string;
  extraction_pending: number;
  extraction_completed: number;
  extraction_failed: number;
  extraction_skipped: number;
  knowledge_pending: number;
  knowledge_completed: number;
  knowledge_failed: number;
  knowledge_skipped: number;
  triage_pending: number;
  triage_completed: number;
  content_chunks: number;
  recent_extraction_errors: { external_id: string; error: string }[];
  recent_triage_samples: TriageSample[];
};

export async function getSourceProcessingStats(
  sourceId: string,
): Promise<SourceProcessingStats | null> {
  const response = await fetch(`${API_URL}/api/v1/sources/${sourceId}/processing`, {
    cache: "no-store",
  });
  if (!response.ok) return null;
  return response.json();
}

export function formatProcessingSummary(stats: SourceProcessingStats): string {
  const done = stats.extraction_completed;
  const total =
    stats.extraction_pending +
    stats.extraction_completed +
    stats.extraction_failed +
    stats.extraction_skipped;
  const knowledge = stats.knowledge_completed;
  const chunks = stats.content_chunks;
  const triage = stats.triage_completed;
  if (total === 0) return "Még nincs feldolgozandó fájl.";
  const triagePart = triage > 0 ? ` · Besorolás: ${triage}` : "";
  return `Feldolgozás: ${done}/${total} fájl · Tudás: ${knowledge} · Chunkok: ${chunks}${triagePart}`;
}

export function triageSensitivityLabel(value: string): string {
  switch (value) {
    case "high":
      return "Magas érzékenység";
    case "medium":
      return "Közepes érzékenység";
    default:
      return "Alacsony érzékenység";
  }
}

export function triageReviewRiskLabel(value: string): string {
  switch (value) {
    case "high":
      return "Magas ellenőrzési kockázat";
    case "low":
      return "Alacsony ellenőrzési kockázat";
    default:
      return "Közepes ellenőrzési kockázat";
  }
}

export function formatTriageSample(sample: TriageSample): string {
  const name = sample.external_id.split("/").pop() ?? sample.external_id;
  return `${name} — ${triageSensitivityLabel(sample.sensitivity)}, ${triageReviewRiskLabel(sample.review_risk)}`;
}

export async function deleteSource(sourceId: string): Promise<boolean> {
  const response = await fetch(`${API_URL}/api/v1/sources/${sourceId}`, {
    method: "DELETE",
  });
  return response.status === 204;
}

export async function getSyncRun(syncRunId: string): Promise<SyncRun | null> {
  const response = await fetch(`${API_URL}/api/v1/sync-runs/${syncRunId}`, {
    cache: "no-store",
  });
  if (!response.ok) return null;
  return response.json();
}

export async function startSync(sourceId: string, mode: "full" | "incremental" = "incremental") {
  const response = await fetch(`${API_URL}/api/v1/sync-runs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ source_id: sourceId, mode }),
  });
  if (!response.ok) return null;
  return response.json() as Promise<SyncRun>;
}

export async function listSyncRuns(sourceId: string): Promise<SyncRun[]> {
  const response = await fetch(`${API_URL}/api/v1/sources/${sourceId}/sync-runs`, {
    cache: "no-store",
  });
  if (!response.ok) return [];
  const data = await response.json();
  return data.items ?? [];
}

export async function listGoogleAccounts(): Promise<GoogleAccount[]> {
  const response = await fetch(`${API_URL}/api/v1/connectors/google/accounts`, {
    cache: "no-store",
  });
  if (!response.ok) return [];
  const data = await response.json();
  return data.items ?? [];
}

export async function getGoogleAuthUrl(): Promise<string | null> {
  const response = await fetch(`${API_URL}/api/v1/connectors/google/auth-url`, {
    cache: "no-store",
  });
  if (!response.ok) return null;
  const data = await response.json();
  return data.auth_url ?? null;
}

export async function revokeGoogleAccount(accountAlias: string): Promise<boolean> {
  const response = await fetch(`${API_URL}/api/v1/connectors/google/accounts/${accountAlias}`, {
    method: "DELETE",
  });
  return response.ok;
}

export function sourceTypeLabel(type: SourceType): string {
  switch (type) {
    case "local_folder":
      return "Helyi mappa";
    case "google_drive":
      return "Google Drive";
    case "gmail":
      return "Gmail";
    case "google_calendar":
      return "Google Naptár";
    case "github":
      return "GitHub";
    default:
      return type;
  }
}

export function syncStatusLabel(status: string): string {
  switch (status) {
    case "completed":
      return "Kész";
    case "running":
      return "Szinkronizálás…";
    case "pending":
      return "Várakozás";
    case "failed":
      return "Hiba";
    case "partial":
      return "Részleges";
    default:
      return status;
  }
}

/** Prefer a finished run when the newest run is a stuck pending job (0 progress). */
export function pickDisplaySyncRun(runs: SyncRun[]): SyncRun | undefined {
  if (runs.length === 0) return undefined;
  const latest = runs[0];
  const stuckPending =
    (latest.status === "pending" || latest.status === "running") &&
    !latest.started_at &&
    latest.objects_processed === 0 &&
    latest.objects_discovered === 0;
  if (stuckPending) {
    const lastFinished = runs.find(
      (run) => run.status === "completed" || run.status === "partial" || run.status === "failed",
    );
    if (lastFinished) return lastFinished;
  }
  return latest;
}

export function hasStuckPendingSync(runs: SyncRun[]): boolean {
  if (runs.length === 0) return false;
  const latest = runs[0];
  return (
    latest.status === "pending" &&
    !latest.started_at &&
    latest.objects_processed === 0 &&
    runs.some((run) => run.status === "completed" || run.status === "partial")
  );
}

/** True only while a sync is actively executing — not for queued/stuck jobs. */
export function isSyncInFlight(runs: SyncRun[]): boolean {
  const newest = runs[0];
  if (!newest) return false;
  if (newest.status === "running") return true;
  return newest.status === "pending" && Boolean(newest.started_at);
}
