from typing import Protocol

from adapters.embeddings.hash_embedding import HashEmbeddingProvider
from adapters.embeddings.openai_compatible import OpenAICompatibleEmbeddingProvider
from adapters.settings.resolver import ResolvedLlmSettings


class EmbeddingSettings(Protocol):
    llm_api_key: str
    embedding_dimension: int


def build_embedding_provider(
    settings: ResolvedLlmSettings | EmbeddingSettings,
) -> HashEmbeddingProvider | OpenAICompatibleEmbeddingProvider:
    if isinstance(settings, ResolvedLlmSettings):
        if settings.use_hash_embeddings:
            return HashEmbeddingProvider(dimension=settings.embedding_dimension)
        return OpenAICompatibleEmbeddingProvider(settings)
    if settings.llm_api_key:
        return OpenAICompatibleEmbeddingProvider(settings)  # type: ignore[arg-type]
    return HashEmbeddingProvider(dimension=settings.embedding_dimension)
