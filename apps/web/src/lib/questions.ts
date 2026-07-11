const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type QuestionAnswer = {
  question: string;
  answer: string;
  confidence: number;
  insufficient_evidence: boolean;
  citations: Array<{
    citation_id: string;
    excerpt: string;
    external_id?: string | null;
    score: number;
    signal: string;
  }>;
  claims: Array<{
    text: string;
    confidence: number;
    citation_ids: string[];
  }>;
  warnings: string[];
  conflicts: string[];
  model?: string | null;
};

export async function askQuestion(
  question: string,
  mode: "hybrid" | "keyword" | "semantic" = "hybrid",
): Promise<QuestionAnswer | null> {
  const response = await fetch(`${API_URL}/api/v1/questions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, mode }),
  });
  if (!response.ok) return null;
  const data = await response.json();
  return {
    ...data,
    warnings: data.warnings ?? [],
    conflicts: data.conflicts ?? [],
  };
}
