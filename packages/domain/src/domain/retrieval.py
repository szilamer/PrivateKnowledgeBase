from domain.content import ChunkSearchHit
from domain.questions import Citation, RetrievalSignal


def add_chunk_citation(
    citations: dict[str, Citation],
    hit: ChunkSearchHit,
    *,
    signal: RetrievalSignal,
) -> None:
    cite_id = f"chunk-{hit.chunk_id}"
    citations[cite_id] = Citation(
        citation_id=cite_id,
        chunk_id=hit.chunk_id,
        source_id=hit.source_id,
        source_object_version_id=hit.source_object_version_id,
        external_id=hit.external_id,
        excerpt=hit.text[:500],
        score=hit.score,
        signal=signal,
    )
