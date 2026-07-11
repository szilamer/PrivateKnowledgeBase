"""Add maintenance_flags JSONB to source_object_versions (Phase I)."""

from alembic import op

revision: str = "0012_maintenance_flags"
down_revision: str | None = "0011_ontology_proposals"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE source_object_versions
        ADD COLUMN IF NOT EXISTS maintenance_flags JSONB NOT NULL DEFAULT '{}'
        """
    )


def downgrade() -> None:
    op.execute("ALTER TABLE source_object_versions DROP COLUMN IF EXISTS maintenance_flags")
