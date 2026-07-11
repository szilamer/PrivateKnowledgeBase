from typing import Protocol
from uuid import UUID

from domain.content import ChunkSearchHit, ContentChunk


class EmbeddingProvider(Protocol):
    model: str
    dimension: int

    async def embed(self, texts: list[str]) -> list[list[float]]: ...


class ChunkRepository(Protocol):
    async def delete_for_version(self, source_object_version_id: UUID) -> None: ...

    async def insert_chunks(
        self, chunks: list[ContentChunk], embeddings: list[list[float]]
    ) -> None: ...

    async def list_by_version(self, source_object_version_id: UUID) -> list[ContentChunk]: ...

    async def keyword_search(
        self, owner_id: UUID, query: str, *, limit: int
    ) -> list[ChunkSearchHit]: ...

    async def semantic_search(
        self, owner_id: UUID, query_embedding: list[float], *, limit: int
    ) -> list[ChunkSearchHit]: ...


class VersionContentRepository(Protocol):
    async def get_pending_versions(self, *, limit: int = 50) -> list[dict[str, object]]: ...

    async def count_pending_extractions(self) -> int: ...

    async def update_extraction_status(
        self, version_id: UUID, status: str, *, error: str | None = None
    ) -> None: ...

    async def get_version_with_source(self, version_id: UUID) -> dict[str, object] | None: ...
