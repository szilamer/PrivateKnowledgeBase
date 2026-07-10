const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type Proposal = {
  id: string;
  proposal_type: string;
  status: string;
  risk_level: string;
  confidence: number;
  title: string;
  payload: Record<string, unknown>;
  requires_review: boolean;
  created_at: string;
};

export async function listProposals(status = "pending"): Promise<Proposal[]> {
  const response = await fetch(`${API_URL}/api/v1/proposals?status=${status}`, {
    cache: "no-store",
  });
  if (!response.ok) return [];
  const data = await response.json();
  return data.items ?? [];
}

export async function approveProposal(id: string): Promise<Proposal | null> {
  const response = await fetch(`${API_URL}/api/v1/proposals/${id}/approve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  });
  if (!response.ok) return null;
  return response.json();
}

export async function rejectProposal(id: string): Promise<Proposal | null> {
  const response = await fetch(`${API_URL}/api/v1/proposals/${id}/reject`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  });
  if (!response.ok) return null;
  return response.json();
}

export async function deferProposal(id: string): Promise<Proposal | null> {
  const response = await fetch(`${API_URL}/api/v1/proposals/${id}/defer`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  });
  if (!response.ok) return null;
  return response.json();
}
