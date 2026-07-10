from datetime import UTC, datetime
from uuid import UUID, uuid4

from application.ports.content import ChunkRepository, EmbeddingProvider, VersionContentRepository
from application.ports.content_loader import ContentLoader
from application.ports.parsers import DocumentParser
from domain.chunking import chunk_markdown, chunk_text, estimate_token_count
from domain.content import ContentChunk, ParserType
from domain.content_hash import compute_content_hash


class DocumentProcessingService:
    """Phase 2 — parse, chunk, embed, and persist content derivatives."""

    PIPELINE_VERSION = "0.1.0"

    def __init__(
        self,
        versions: VersionContentRepository,
        chunks: ChunkRepository,
        embeddings: EmbeddingProvider,
        parser: DocumentParser,
        loader: ContentLoader,
    ) -> None:
        self._versions = versions
        self._chunks = chunks
        self._embeddings = embeddings
        self._parser = parser
        self._loader = loader

    async def process_pending(self, *, batch_size: int = 20) -> int:
        pending = await self._versions.get_pending_versions(limit=batch_size)
        processed = 0
        for row in pending:
            version_id = UUID(str(row["version_id"]))
            try:
                await self.process_version(version_id)
                processed += 1
            except Exception:  # noqa: BLE001 — FR-ING-004 partial failure
                await self._versions.update_extraction_status(version_id, "failed")
        return processed

    async def process_version(self, version_id: UUID) -> int:
        record = await self._versions.get_version_with_source(version_id)
        if record is None:
            msg = f"Version not found: {version_id}"
            raise ValueError(msg)

        raw = await self._loader.load(version_id, record)
        parsed = self._parser.parse(
            raw,
            str(record.get("mime_type")) if record.get("mime_type") else None,
            str(record["external_id"]),
        )

        if parsed.parser_type == ParserType.MARKDOWN:
            segments = chunk_markdown(parsed.text)
        else:
            segments = chunk_text(parsed.text)

        if not segments:
            await self._versions.update_extraction_status(version_id, "skipped")
            return 0

        owner_id = UUID(str(record["owner_id"]))
        source_id = UUID(str(record["source_id"]))
        now = datetime.now(UTC)

        chunk_models: list[ContentChunk] = []
        texts: list[str] = []
        for index, segment in enumerate(segments):
            chunk_models.append(
                ContentChunk(
                    id=uuid4(),
                    source_object_version_id=version_id,
                    source_id=source_id,
                    owner_id=owner_id,
                    chunk_index=index,
                    text=segment.text,
                    token_count=estimate_token_count(segment.text),
                    embedding_model=self._embeddings.model,
                    embedding_dimension=self._embeddings.dimension,
                    content_hash=compute_content_hash(segment.text.encode("utf-8")),
                    anchor_start=segment.anchor_start,
                    anchor_end=segment.anchor_end,
                    created_at=now,
                )
            )
            texts.append(segment.text)

        await self._chunks.delete_for_version(version_id)
        vectors = await self._embeddings.embed(texts)
        await self._chunks.insert_chunks(chunk_models, vectors)
        await self._versions.update_extraction_status(version_id, "completed")
        return len(chunk_models)
