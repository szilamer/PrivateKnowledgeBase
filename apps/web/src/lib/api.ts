const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type Source = {
  id: string;
  type: "local_folder" | "github";
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
};

export async function listSources(): Promise<Source[]> {
  const response = await fetch(`${API_URL}/api/v1/sources`, { cache: "no-store" });
  if (!response.ok) return [];
  const data = await response.json();
  return data.items ?? [];
}

export async function registerLocalSource(name: string, path: string): Promise<Source | null> {
  const response = await fetch(`${API_URL}/api/v1/sources/local`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, path }),
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
