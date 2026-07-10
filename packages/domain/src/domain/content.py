from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field


class ParserType(StrEnum):
    MARKDOWN = "markdown"
    TEXT = "text"
    PDF = "pdf"


class ParsedDocument(BaseModel):
    text: str
    parser_type: ParserType
    parser_version: str


class ContentChunk(BaseModel):
    id: UUID
    source_object_version_id: UUID
    source_id: UUID
    owner_id: UUID
    chunk_index: int
    text: str
    token_count: int
    embedding_model: str
    embedding_dimension: int
    content_hash: str
    anchor_start: int | None = None
    anchor_end: int | None = None
    created_at: datetime


class ChunkSearchHit(BaseModel):
    chunk_id: UUID
    source_id: UUID
    source_object_version_id: UUID
    external_id: str
    text: str
    score: float
    match_type: str
    anchor_start: int | None = None
    anchor_end: int | None = None


class SearchRequest(BaseModel):
    query: str
    mode: str = "hybrid"  # keyword | semantic | hybrid
    limit: int = Field(default=20, ge=1, le=100)


class SearchResponse(BaseModel):
    query: str
    mode: str
    hits: list[ChunkSearchHit] = Field(default_factory=list)


class SourcePreview(BaseModel):
    source_object_version_id: UUID
    external_id: str
    mime_type: str | None
    text: str
    chunks: list[ContentChunk] = Field(default_factory=list)
