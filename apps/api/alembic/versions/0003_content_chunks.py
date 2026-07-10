"""Initial schema: content chunks with pgvector embeddings (Phase 2)."""

from collections.abc import Sequence

from alembic import op

revision: str = "0003_content_chunks"
down_revision: str | None = "0002_sources_registry"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS content_chunks (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            source_object_version_id UUID NOT NULL
                REFERENCES source_object_versions(id) ON DELETE CASCADE,
            source_id UUID NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
            owner_id UUID NOT NULL REFERENCES users(id),
            chunk_index INTEGER NOT NULL,
            text TEXT NOT NULL,
            token_count INTEGER NOT NULL DEFAULT 0,
            embedding_model TEXT NOT NULL,
            embedding_dimension INTEGER NOT NULL,
            embedding vector(1536),
            content_hash TEXT NOT NULL,
            anchor_start INTEGER,
            anchor_end INTEGER,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE (source_object_version_id, chunk_index, embedding_model)
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_content_chunks_source ON content_chunks (source_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_content_chunks_owner ON content_chunks (owner_id)")
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_content_chunks_fts
        ON content_chunks USING gin (to_tsvector('english', text))
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_content_chunks_embedding
        ON content_chunks USING hnsw (embedding vector_cosine_ops)
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS content_chunks")
