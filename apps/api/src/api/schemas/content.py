from uuid import UUID

from pydantic import BaseModel, Field


class SearchHitResponse(BaseModel):
    chunk_id: UUID
    source_id: UUID
    source_object_version_id: UUID
    external_id: str
    text: str
    score: float
    match_type: str
    anchor_start: int | None = None
    anchor_end: int | None = None


class SearchResultResponse(BaseModel):
    query: str
    mode: str
    hits: list[SearchHitResponse] = Field(default_factory=list)
