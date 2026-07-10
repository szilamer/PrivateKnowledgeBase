"""Initial schema: canonical knowledge, provenance, contradictions (Phase 4)."""

from collections.abc import Sequence

from alembic import op

revision: str = "0005_canonical_knowledge"
down_revision: str | None = "0004_knowledge_proposals"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS canonical_entities (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_id UUID NOT NULL REFERENCES users(id),
            entity_type TEXT NOT NULL,
            canonical_name TEXT NOT NULL,
            aliases JSONB NOT NULL DEFAULT '[]',
            description TEXT,
            status TEXT NOT NULL DEFAULT 'active',
            source_proposal_id UUID REFERENCES knowledge_proposals(id) ON DELETE SET NULL,
            ontology_version TEXT NOT NULL DEFAULT '0.1.0',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE (owner_id, entity_type, canonical_name)
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_canonical_entities_owner "
        "ON canonical_entities (owner_id, entity_type)"
    )

    op.execute(
        """
        ALTER TABLE entity_index
        ADD COLUMN IF NOT EXISTS canonical_entity_id UUID
            REFERENCES canonical_entities(id) ON DELETE SET NULL
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS canonical_claims (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_id UUID NOT NULL REFERENCES users(id),
            subject_entity_id UUID REFERENCES canonical_entities(id) ON DELETE SET NULL,
            predicate TEXT NOT NULL,
            object_value TEXT NOT NULL,
            object_entity_id UUID REFERENCES canonical_entities(id) ON DELETE SET NULL,
            status TEXT NOT NULL DEFAULT 'active',
            confidence DOUBLE PRECISION NOT NULL,
            valid_from TIMESTAMPTZ,
            valid_to TIMESTAMPTZ,
            observed_at TIMESTAMPTZ,
            source_proposal_id UUID REFERENCES knowledge_proposals(id) ON DELETE SET NULL,
            superseded_by UUID REFERENCES canonical_claims(id) ON DELETE SET NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_canonical_claims_subject "
        "ON canonical_claims (owner_id, subject_entity_id, predicate, status)"
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS claim_provenance (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            claim_id UUID NOT NULL REFERENCES canonical_claims(id) ON DELETE CASCADE,
            source_object_version_id UUID
                REFERENCES source_object_versions(id) ON DELETE SET NULL,
            content_chunk_id UUID REFERENCES content_chunks(id) ON DELETE SET NULL,
            proposal_id UUID REFERENCES knowledge_proposals(id) ON DELETE SET NULL,
            extraction_run_id UUID REFERENCES extraction_runs(id) ON DELETE SET NULL,
            model TEXT,
            confidence DOUBLE PRECISION,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS canonical_relationships (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_id UUID NOT NULL REFERENCES users(id),
            source_entity_id UUID NOT NULL
                REFERENCES canonical_entities(id) ON DELETE CASCADE,
            target_entity_id UUID NOT NULL
                REFERENCES canonical_entities(id) ON DELETE CASCADE,
            relationship_type TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            valid_from TIMESTAMPTZ,
            valid_to TIMESTAMPTZ,
            source_proposal_id UUID REFERENCES knowledge_proposals(id) ON DELETE SET NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_canonical_relationships_source "
        "ON canonical_relationships (source_entity_id)"
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS contradiction_findings (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_id UUID NOT NULL REFERENCES users(id),
            existing_claim_id UUID NOT NULL
                REFERENCES canonical_claims(id) ON DELETE CASCADE,
            conflicting_claim_id UUID
                REFERENCES canonical_claims(id) ON DELETE SET NULL,
            conflicting_proposal_id UUID
                REFERENCES knowledge_proposals(id) ON DELETE SET NULL,
            status TEXT NOT NULL DEFAULT 'open',
            summary TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_contradiction_findings_owner_status "
        "ON contradiction_findings (owner_id, status)"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS contradiction_findings")
    op.execute("DROP TABLE IF EXISTS canonical_relationships")
    op.execute("DROP TABLE IF EXISTS claim_provenance")
    op.execute("DROP TABLE IF EXISTS canonical_claims")
    op.execute("ALTER TABLE entity_index DROP COLUMN IF EXISTS canonical_entity_id")
    op.execute("DROP TABLE IF EXISTS canonical_entities")
