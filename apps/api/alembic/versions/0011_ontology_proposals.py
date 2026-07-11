"""Add ontology_proposals table for Phase E curator agent."""

from alembic import op

revision: str = "0011_ontology_proposals"
down_revision: str | None = "0010_project_reports"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS ontology_proposals (
            id UUID PRIMARY KEY,
            owner_id UUID NOT NULL,
            kind TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            title TEXT NOT NULL,
            rationale TEXT NOT NULL,
            proposed_definition JSONB NOT NULL,
            evidence JSONB NOT NULL DEFAULT '{}',
            ontology_version TEXT NOT NULL,
            decision_rationale TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            decided_at TIMESTAMPTZ
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_ontology_proposals_owner_status "
        "ON ontology_proposals (owner_id, status)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_ontology_proposals_owner_status")
    op.execute("DROP TABLE IF EXISTS ontology_proposals")
