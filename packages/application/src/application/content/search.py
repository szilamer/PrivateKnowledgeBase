from application.ports import PolicyService
from application.ports.content import ChunkRepository, EmbeddingProvider
from domain.content import ChunkSearchHit, SearchRequest, SearchResponse
from domain.identity import DEFAULT_OWNER_ID, OwnerContext


class SearchService:
    """FR-RET-001/002 — keyword, semantic, and hybrid search with owner filter."""

    def __init__(
        self,
        chunks: ChunkRepository,
        embeddings: EmbeddingProvider,
        policy: PolicyService,
    ) -> None:
        self._chunks = chunks
        self._embeddings = embeddings
        self._policy = policy

    async def search(self, ctx: OwnerContext, request: SearchRequest) -> SearchResponse:
        self._policy.authorize_owner(ctx, DEFAULT_OWNER_ID)

        if request.mode == "keyword":
            hits = await self._chunks.keyword_search(
                DEFAULT_OWNER_ID, request.query, limit=request.limit
            )
        elif request.mode == "semantic":
            vector = (await self._embeddings.embed([request.query]))[0]
            hits = await self._chunks.semantic_search(DEFAULT_OWNER_ID, vector, limit=request.limit)
        else:
            keyword_hits = await self._chunks.keyword_search(
                DEFAULT_OWNER_ID, request.query, limit=request.limit
            )
            vector = (await self._embeddings.embed([request.query]))[0]
            semantic_hits = await self._chunks.semantic_search(
                DEFAULT_OWNER_ID, vector, limit=request.limit
            )
            hits = _merge_hits(keyword_hits, semantic_hits, limit=request.limit)

        return SearchResponse(query=request.query, mode=request.mode, hits=hits)


def _merge_hits(
    keyword: list[ChunkSearchHit], semantic: list[ChunkSearchHit], *, limit: int
) -> list[ChunkSearchHit]:
    combined: dict[str, ChunkSearchHit] = {}
    for hit in keyword + semantic:
        key = str(hit.chunk_id)
        existing = combined.get(key)
        if existing is None or hit.score > existing.score:
            combined[key] = ChunkSearchHit(
                chunk_id=hit.chunk_id,
                source_id=hit.source_id,
                source_object_version_id=hit.source_object_version_id,
                external_id=hit.external_id,
                text=hit.text,
                score=hit.score,
                match_type="hybrid",
                anchor_start=hit.anchor_start,
                anchor_end=hit.anchor_end,
            )
    return sorted(combined.values(), key=lambda h: h.score, reverse=True)[:limit]
