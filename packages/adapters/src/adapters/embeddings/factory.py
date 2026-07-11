from typing import Protocol

from adapters.embeddings.hash_embedding import HashEmbeddingProvider
from adapters.embeddings.openai_compatible import OpenAICompatibleEmbeddingProvider
from adapters.embeddings.resilient import ResilientEmbeddingProvider
from adapters.settings.resolver import ResolvedLlmSettings


class EmbeddingSettings(Protocol):
    llm_api_key: str
    embedding_dimension: int


def build_embedding_provider(
    settings: ResolvedLlmSettings | EmbeddingSettings,
) -> HashEmbeddingProvider | OpenAICompatibleEmbeddingProvider | ResilientEmbeddingProvider:
    dimension = (
        settings.embedding_dimension
        if isinstance(settings, ResolvedLlmSettings)
        else settings.embedding_dimension
    )
    fallback = HashEmbeddingProvider(dimension=dimension)
    if isinstance(settings, ResolvedLlmSettings):
        if settings.use_hash_embeddings:
            return fallback
        primary = OpenAICompatibleEmbeddingProvider(settings)
        return ResilientEmbeddingProvider(primary, fallback)
    if settings.llm_api_key:
        primary = OpenAICompatibleEmbeddingProvider(settings)  # type: ignore[arg-type]
        return ResilientEmbeddingProvider(primary, fallback)
    return fallback
