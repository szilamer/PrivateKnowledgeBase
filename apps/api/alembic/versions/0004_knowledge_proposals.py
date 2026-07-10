"""Initial schema: knowledge proposals, extraction runs, entity index (Phase 3)."""

from collections.abc import Sequence

from alembic import op

revision: str = "0004_knowledge_proposals"
down_revision: str | None = "0003_content_chunks"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE source_object_versions
        ADD COLUMN IF NOT EXISTS knowledge_status TEXT NOT NULL DEFAULT 'pending'
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS extraction_runs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            source_object_version_id UUID NOT NULL
                REFERENCES source_object_versions(id) ON DELETE CASCADE,
            owner_id UUID NOT NULL REFERENCES users(id),
            status TEXT NOT NULL DEFAULT 'running',
            model TEXT,
            provider TEXT,
            prompt_version TEXT NOT NULL,
            schema_version TEXT NOT NULL,
            pipeline_version TEXT NOT NULL,
            token_usage JSONB,
            latency_ms INTEGER,
            correlation_id TEXT,
            error_summary TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            completed_at TIMESTAMPTZ
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_extraction_runs_version "
        "ON extraction_runs (source_object_version_id)"
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS knowledge_proposals (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_id UUID NOT NULL REFERENCES users(id),
            extraction_run_id UUID REFERENCES extraction_runs(id) ON DELETE SET NULL,
            proposal_type TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            risk_level TEXT NOT NULL DEFAULT 'medium',
            confidence DOUBLE PRECISION NOT NULL,
            title TEXT NOT NULL,
            payload JSONB NOT NULL,
            project_id UUID,
            source_id UUID REFERENCES sources(id) ON DELETE SET NULL,
            requires_review BOOLEAN NOT NULL DEFAULT TRUE,
            original_payload JSONB,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_knowledge_proposals_owner_status "
        "ON knowledge_proposals (owner_id, status, created_at)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_knowledge_proposals_type "
        "ON knowledge_proposals (proposal_type)"
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS proposal_evidence (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            proposal_id UUID NOT NULL
                REFERENCES knowledge_proposals(id) ON DELETE CASCADE,
            source_object_version_id UUID NOT NULL
                REFERENCES source_object_versions(id) ON DELETE CASCADE,
            content_chunk_id UUID REFERENCES content_chunks(id) ON DELETE SET NULL,
            anchor_start INTEGER,
            anchor_end INTEGER,
            excerpt TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_proposal_evidence_proposal "
        "ON proposal_evidence (proposal_id)"
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS entity_index (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_id UUID NOT NULL REFERENCES users(id),
            entity_type TEXT NOT NULL,
            canonical_name TEXT NOT NULL,
            aliases JSONB NOT NULL DEFAULT '[]',
            status TEXT NOT NULL DEFAULT 'proposed',
            source_proposal_id UUID REFERENCES knowledge_proposals(id) ON DELETE SET NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE (owner_id, entity_type, canonical_name)
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_entity_index_owner_name "
        "ON entity_index (owner_id, canonical_name)"
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS approval_decisions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            proposal_id UUID NOT NULL
                REFERENCES knowledge_proposals(id) ON DELETE CASCADE,
            actor_id UUID NOT NULL REFERENCES users(id),
            action TEXT NOT NULL,
            rationale TEXT,
            edited_payload JSONB,
            correlation_id TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_approval_decisions_proposal "
        "ON approval_decisions (proposal_id)"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS approval_decisions")
    op.execute("DROP TABLE IF EXISTS entity_index")
    op.execute("DROP TABLE IF EXISTS proposal_evidence")
    op.execute("DROP TABLE IF EXISTS knowledge_proposals")
    op.execute("DROP TABLE IF EXISTS extraction_runs")
    op.execute("ALTER TABLE source_object_versions DROP COLUMN IF EXISTS knowledge_status")
