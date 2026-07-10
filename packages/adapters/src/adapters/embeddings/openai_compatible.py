import os
from typing import Protocol

import httpx


class EmbeddingSettings(Protocol):
    llm_base_url: str
    llm_api_key: str
    embedding_model: str
    embedding_dimension: int


class OpenAICompatibleEmbeddingProvider:
    """ADR-007 — OpenAI-compatible embedding endpoint."""

    def __init__(self, settings: EmbeddingSettings) -> None:
        self.model = settings.embedding_model or "text-embedding-3-small"
        self.dimension = settings.embedding_dimension
        self._base_url = settings.llm_base_url.rstrip("/")
        self._api_key = settings.llm_api_key or os.environ.get("LLM_API_KEY", "")

    async def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self._base_url}/embeddings",
                headers=headers,
                json={"input": texts, "model": self.model},
            )
            response.raise_for_status()
            payload = response.json()
            data = sorted(payload["data"], key=lambda item: item["index"])
            return [item["embedding"] for item in data]
