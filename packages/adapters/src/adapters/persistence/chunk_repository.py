import json
from uuid import UUID

from domain.content import ChunkSearchHit, ContentChunk
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class PostgresChunkRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def delete_for_version(self, source_object_version_id: UUID) -> None:
        await self._session.execute(
            text("DELETE FROM content_chunks WHERE source_object_version_id = :vid"),
            {"vid": source_object_version_id},
        )

    async def insert_chunks(
        self, chunks: list[ContentChunk], embeddings: list[list[float]]
    ) -> None:
        for chunk, embedding in zip(chunks, embeddings, strict=True):
            await self._session.execute(
                text(
                    """
                    INSERT INTO content_chunks (
                        id, source_object_version_id, source_id, owner_id,
                        chunk_index, text, token_count, embedding_model,
                        embedding_dimension, embedding, content_hash,
                        anchor_start, anchor_end, created_at
                    ) VALUES (
                        :id, :source_object_version_id, :source_id, :owner_id,
                        :chunk_index, :text, :token_count, :embedding_model,
                        :embedding_dimension, CAST(:embedding AS vector), :content_hash,
                        :anchor_start, :anchor_end, :created_at
                    )
                    ON CONFLICT (source_object_version_id, chunk_index, embedding_model)
                    DO UPDATE SET
                        text = EXCLUDED.text,
                        embedding = EXCLUDED.embedding,
                        content_hash = EXCLUDED.content_hash
                    """
                ),
                {
                    "id": chunk.id,
                    "source_object_version_id": chunk.source_object_version_id,
                    "source_id": chunk.source_id,
                    "owner_id": chunk.owner_id,
                    "chunk_index": chunk.chunk_index,
                    "text": chunk.text,
                    "token_count": chunk.token_count,
                    "embedding_model": chunk.embedding_model,
                    "embedding_dimension": chunk.embedding_dimension,
                    "embedding": json.dumps(embedding),
                    "content_hash": chunk.content_hash,
                    "anchor_start": chunk.anchor_start,
                    "anchor_end": chunk.anchor_end,
                    "created_at": chunk.created_at,
                },
            )

    async def list_by_version(self, source_object_version_id: UUID) -> list[ContentChunk]:
        result = await self._session.execute(
            text(
                """
                SELECT id, source_object_version_id, source_id, owner_id, chunk_index,
                       text, token_count, embedding_model, embedding_dimension,
                       content_hash, anchor_start, anchor_end, created_at
                FROM content_chunks
                WHERE source_object_version_id = :vid
                ORDER BY chunk_index
                """
            ),
            {"vid": source_object_version_id},
        )
        return [_row_to_chunk(row) for row in result.fetchall()]

    async def keyword_search(
        self, owner_id: UUID, query: str, *, limit: int
    ) -> list[ChunkSearchHit]:
        result = await self._session.execute(
            text(
                """
                SELECT c.id AS chunk_id, c.source_id, c.source_object_version_id,
                       so.external_id, c.text, c.anchor_start, c.anchor_end,
                        ts_rank(
                            to_tsvector('english', c.text),
                            plainto_tsquery('english', :q)
                        ) AS score
                FROM content_chunks c
                JOIN source_object_versions sov ON sov.id = c.source_object_version_id
                JOIN source_objects so ON so.id = sov.source_object_id
                WHERE c.owner_id = :owner_id
                  AND to_tsvector('english', c.text) @@ plainto_tsquery('english', :q)
                ORDER BY score DESC
                LIMIT :limit
                """
            ),
            {"owner_id": owner_id, "q": query, "limit": limit},
        )
        return [
            ChunkSearchHit(
                chunk_id=row.chunk_id,
                source_id=row.source_id,
                source_object_version_id=row.source_object_version_id,
                external_id=row.external_id,
                text=row.text,
                score=float(row.score),
                match_type="keyword",
                anchor_start=row.anchor_start,
                anchor_end=row.anchor_end,
            )
            for row in result.fetchall()
        ]

    async def semantic_search(
        self, owner_id: UUID, query_embedding: list[float], *, limit: int
    ) -> list[ChunkSearchHit]:
        result = await self._session.execute(
            text(
                """
                SELECT c.id AS chunk_id, c.source_id, c.source_object_version_id,
                       so.external_id, c.text, c.anchor_start, c.anchor_end,
                       1 - (c.embedding <=> CAST(:embedding AS vector)) AS score
                FROM content_chunks c
                JOIN source_object_versions sov ON sov.id = c.source_object_version_id
                JOIN source_objects so ON so.id = sov.source_object_id
                WHERE c.owner_id = :owner_id
                  AND c.embedding IS NOT NULL
                ORDER BY c.embedding <=> CAST(:embedding AS vector)
                LIMIT :limit
                """
            ),
            {
                "owner_id": owner_id,
                "embedding": json.dumps(query_embedding),
                "limit": limit,
            },
        )
        return [
            ChunkSearchHit(
                chunk_id=row.chunk_id,
                source_id=row.source_id,
                source_object_version_id=row.source_object_version_id,
                external_id=row.external_id,
                text=row.text,
                score=float(row.score),
                match_type="semantic",
                anchor_start=row.anchor_start,
                anchor_end=row.anchor_end,
            )
            for row in result.fetchall()
        ]


def _row_to_chunk(row: object) -> ContentChunk:
    return ContentChunk(
        id=row.id,  # type: ignore[attr-defined]
        source_object_version_id=row.source_object_version_id,  # type: ignore[attr-defined]
        source_id=row.source_id,  # type: ignore[attr-defined]
        owner_id=row.owner_id,  # type: ignore[attr-defined]
        chunk_index=row.chunk_index,  # type: ignore[attr-defined]
        text=row.text,  # type: ignore[attr-defined]
        token_count=row.token_count,  # type: ignore[attr-defined]
        embedding_model=row.embedding_model,  # type: ignore[attr-defined]
        embedding_dimension=row.embedding_dimension,  # type: ignore[attr-defined]
        content_hash=row.content_hash,  # type: ignore[attr-defined]
        anchor_start=row.anchor_start,  # type: ignore[attr-defined]
        anchor_end=row.anchor_end,  # type: ignore[attr-defined]
        created_at=row.created_at,  # type: ignore[attr-defined]
    )


class PostgresVersionContentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_pending_versions(self, *, limit: int = 50) -> list[dict[str, object]]:
        result = await self._session.execute(
            text(
                """
                SELECT sov.id AS version_id, sov.content_ref, sov.mime_type,
                       so.external_id, so.source_id, s.owner_id, s.configuration
                FROM source_object_versions sov
                JOIN source_objects so ON so.id = sov.source_object_id
                JOIN sources s ON s.id = so.source_id
                WHERE sov.extraction_status = 'pending'
                ORDER BY sov.observed_at
                LIMIT :limit
                """
            ),
            {"limit": limit},
        )
        return [dict(row._mapping) for row in result.fetchall()]

    async def update_extraction_status(
        self, version_id: UUID, status: str, *, error: str | None = None
    ) -> None:
        await self._session.execute(
            text("UPDATE source_object_versions SET extraction_status = :status WHERE id = :id"),
            {"id": version_id, "status": status},
        )
        _ = error

    async def get_version_with_source(self, version_id: UUID) -> dict[str, object] | None:
        result = await self._session.execute(
            text(
                """
                SELECT sov.id AS version_id, sov.content_ref, sov.mime_type, sov.content_hash,
                       so.external_id, so.source_id, s.owner_id, s.type AS source_type,
                       s.configuration
                FROM source_object_versions sov
                JOIN source_objects so ON so.id = sov.source_object_id
                JOIN sources s ON s.id = so.source_id
                WHERE sov.id = :id
                """
            ),
            {"id": version_id},
        )
        row = result.first()
        return dict(row._mapping) if row else None
