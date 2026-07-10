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
