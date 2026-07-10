export type SearchHit = {
  chunk_id: string;
  source_id: string;
  source_object_version_id: string;
  external_id: string;
  text: string;
  score: number;
  match_type: string;
};

export async function searchKnowledge(
  query: string,
  mode: "keyword" | "semantic" | "hybrid" = "hybrid"
): Promise<SearchHit[]> {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
  const response = await fetch(`${apiUrl}/api/v1/search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, mode, limit: 20 }),
  });
  if (!response.ok) return [];
  const data = await response.json();
  return data.hits ?? [];
}
