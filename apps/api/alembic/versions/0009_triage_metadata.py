"""Add triage_status and triage_metadata to source_object_versions (Phase B)."""

from collections.abc import Sequence

from alembic import op

revision: str = "0009_triage_metadata"
down_revision: str | None = "0008_contradiction_evidence"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE source_object_versions
        ADD COLUMN IF NOT EXISTS triage_status TEXT NOT NULL DEFAULT 'pending'
        """
    )
    op.execute(
        """
        ALTER TABLE source_object_versions
        ADD COLUMN IF NOT EXISTS triage_metadata JSONB NOT NULL DEFAULT '{}'
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_source_object_versions_triage_status "
        "ON source_object_versions (triage_status)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_source_object_versions_triage_status")
    op.execute("ALTER TABLE source_object_versions DROP COLUMN IF EXISTS triage_metadata")
    op.execute("ALTER TABLE source_object_versions DROP COLUMN IF EXISTS triage_status")
