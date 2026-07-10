from uuid import UUID

from application.ports import PolicyService
from application.ports.content import ChunkRepository, VersionContentRepository
from application.ports.content_loader import ContentLoader
from application.ports.parsers import DocumentParser
from domain.content import SourcePreview
from domain.errors import DomainError
from domain.identity import DEFAULT_OWNER_ID, OwnerContext


class PreviewService:
    """FR-RET-005 — source preview with citation anchors."""

    def __init__(
        self,
        versions: VersionContentRepository,
        chunks: ChunkRepository,
        parser: DocumentParser,
        loader: ContentLoader,
        policy: PolicyService,
    ) -> None:
        self._versions = versions
        self._chunks = chunks
        self._parser = parser
        self._loader = loader
        self._policy = policy

    async def get_preview(self, ctx: OwnerContext, version_id: UUID) -> SourcePreview:
        self._policy.authorize_owner(ctx, DEFAULT_OWNER_ID)
        record = await self._versions.get_version_with_source(version_id)
        if record is None:
            raise DomainError(f"Version not found: {version_id}")

        raw = await self._loader.load(version_id, record)
        parsed = self._parser.parse(
            raw,
            str(record.get("mime_type")) if record.get("mime_type") else None,
            str(record["external_id"]),
        )
        chunk_list = await self._chunks.list_by_version(version_id)
        return SourcePreview(
            source_object_version_id=version_id,
            external_id=str(record["external_id"]),
            mime_type=str(record.get("mime_type")) if record.get("mime_type") else None,
            text=parsed.text[:8000],
            chunks=chunk_list,
        )
