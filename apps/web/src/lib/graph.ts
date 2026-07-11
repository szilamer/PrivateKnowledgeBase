const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type CanonicalEntity = {
  id: string;
  entity_type: string;
  canonical_name: string;
  aliases: string[];
  status: string;
};

export type GraphNode = {
  id: string;
  label: string;
  node_type: string;
  properties: Record<string, unknown>;
};

export type GraphEdge = {
  id: string;
  source_id: string;
  target_id: string;
  edge_type: string;
};

export type GraphView = {
  root_id: string | null;
  depth: number;
  nodes: GraphNode[];
  edges: GraphEdge[];
  truncated: boolean;
};

export async function listEntities(): Promise<CanonicalEntity[]> {
  const response = await fetch(`${API_URL}/api/v1/entities`, { cache: "no-store" });
  if (!response.ok) return [];
  const data = await response.json();
  return data.items ?? [];
}

export async function fetchNeighborhood(entityId: string): Promise<GraphView | null> {
  const response = await fetch(
    `${API_URL}/api/v1/graph/neighborhood/${entityId}?depth=1&limit=50`,
    { cache: "no-store" },
  );
  if (!response.ok) return null;
  return response.json();
}

export type Contradiction = {
  id: string;
  summary: string;
  status: string;
  predicate: string | null;
  existing_value: string | null;
  conflicting_value: string | null;
  existing_claim_id: string;
  conflicting_claim_id: string | null;
  conflicting_proposal_id: string | null;
  subject_entity_id: string | null;
  created_at: string;
};

export async function listContradictions(): Promise<Contradiction[]> {
  const response = await fetch(`${API_URL}/api/v1/contradictions?status=open`, {
    cache: "no-store",
  });
  if (!response.ok) return [];
  const data = await response.json();
  return data.items ?? [];
}
