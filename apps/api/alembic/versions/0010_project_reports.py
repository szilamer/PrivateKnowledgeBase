"""Add project_reports table for async Phase H report jobs."""

from alembic import op

revision: str = "0010_project_reports"
down_revision: str | None = "0009_triage_metadata"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS project_reports (
            id UUID PRIMARY KEY,
            owner_id UUID NOT NULL,
            project_entity_id UUID NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            title TEXT NOT NULL DEFAULT '',
            markdown TEXT,
            citations JSONB NOT NULL DEFAULT '[]',
            provenance JSONB NOT NULL DEFAULT '{}',
            period_start TIMESTAMPTZ,
            period_end TIMESTAMPTZ,
            error_summary TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            completed_at TIMESTAMPTZ
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_project_reports_owner "
        "ON project_reports (owner_id, project_entity_id)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_project_reports_owner")
    op.execute("DROP TABLE IF EXISTS project_reports")
