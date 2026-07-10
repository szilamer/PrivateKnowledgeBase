import { getBrowserApiUrl } from "./api-url";

export type LlmSettingsConfig = {
  enabled: boolean;
  base_url: string;
  api_key_env: string;
  extraction_model: string;
  synthesis_model: string;
  embedding: {
    provider: "auto" | "hash" | "api";
    model: string;
    dimension: number;
  };
};

export type AppSettings = {
  version: string;
  llm: LlmSettingsConfig;
  effective?: {
    llm: {
      enabled: boolean;
      base_url: string;
      api_key_env: string;
      api_key_configured: boolean;
      extraction_model: string;
      synthesis_model: string;
      embedding: {
        provider: string;
        model: string;
        dimension: number;
      };
    };
  };
};

export type LlmHealth = {
  status: string;
  llm_enabled: boolean;
  api_key_configured: boolean;
  base_url: string;
  extraction_model: string;
  synthesis_model: string;
  embedding_provider: string;
  message: string | null;
};

const API_URL = getBrowserApiUrl();

export async function getAppSettings(): Promise<AppSettings | null> {
  const response = await fetch(`${API_URL}/api/v1/settings`, { cache: "no-store" });
  if (!response.ok) return null;
  const data = await response.json();
  return data.config ?? null;
}

export async function putAppSettings(config: AppSettings): Promise<boolean> {
  const response = await fetch(`${API_URL}/api/v1/settings`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ config }),
  });
  return response.ok;
}

export async function getLlmHealth(): Promise<LlmHealth | null> {
  const response = await fetch(`${API_URL}/api/v1/settings/llm/health`, { cache: "no-store" });
  if (!response.ok) return null;
  return response.json();
}
