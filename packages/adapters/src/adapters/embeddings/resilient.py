from adapters.embeddings.hash_embedding import HashEmbeddingProvider
from application.ports.content import EmbeddingProvider
from observability.logging import get_logger

logger = get_logger("adapters.embeddings.resilient")


class ResilientEmbeddingProvider:
    """Try API embeddings first; fall back to hash on connectivity or provider errors."""

    model: str
    dimension: int

    def __init__(
        self,
        primary: EmbeddingProvider,
        fallback: HashEmbeddingProvider,
    ) -> None:
        self._primary = primary
        self._fallback = fallback
        self._using_fallback = False
        self.model = primary.model
        self.dimension = primary.dimension

    async def embed(self, texts: list[str]) -> list[list[float]]:
        if self._using_fallback:
            return await self._fallback.embed(texts)
        try:
            return await self._primary.embed(texts)
        except Exception as exc:  # noqa: BLE001 — degrade to hash embeddings
            logger.warning(
                "embedding_provider_fallback",
                error=str(exc),
                primary_model=self._primary.model,
            )
            self._using_fallback = True
            self.model = self._fallback.model
            self.dimension = self._fallback.dimension
            return await self._fallback.embed(texts)
