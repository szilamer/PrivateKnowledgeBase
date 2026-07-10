const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type ProjectDashboard = {
  summary: string;
  projects: Array<{ id: string; name: string }>;
  repositories: Array<{ id: string; name: string }>;
  technologies: Array<{ id: string; name: string }>;
  decisions: string[];
  open_tasks: string[];
  recent_events: string[];
  processing_health: {
    sources_total: number;
    sources_enabled: number;
    open_contradictions: number;
    pending_outbox_events: number;
  };
};

export type StatusReport = {
  title: string;
  summary: string;
  decisions: string[];
  tasks: string[];
  events: string[];
  technologies: string[];
  citations: string[];
};

export async function fetchProjectOverview(): Promise<ProjectDashboard | null> {
  const response = await fetch(`${API_URL}/api/v1/projects/overview`, { cache: "no-store" });
  if (!response.ok) return null;
  return response.json();
}

export async function generateStatusReport(): Promise<StatusReport | null> {
  const response = await fetch(`${API_URL}/api/v1/projects/status-report`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  });
  if (!response.ok) return null;
  return response.json();
}
