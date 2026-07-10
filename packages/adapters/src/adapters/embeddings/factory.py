from typing import Protocol

from adapters.embeddings.hash_embedding import HashEmbeddingProvider
from adapters.embeddings.openai_compatible import OpenAICompatibleEmbeddingProvider


class EmbeddingSettings(Protocol):
    llm_api_key: str
    embedding_dimension: int


def build_embedding_provider(
    settings: EmbeddingSettings,
) -> HashEmbeddingProvider | OpenAICompatibleEmbeddingProvider:
    if settings.llm_api_key:
        return OpenAICompatibleEmbeddingProvider(settings)  # type: ignore[arg-type]
    return HashEmbeddingProvider(dimension=settings.embedding_dimension)
