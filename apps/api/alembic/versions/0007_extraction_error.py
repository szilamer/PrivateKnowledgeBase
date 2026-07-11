"""Add extraction_error column for per-version failure diagnostics."""

from collections.abc import Sequence

from alembic import op

revision: str = "0007_extraction_error"
down_revision: str | None = "0006_connector_credentials"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE source_object_versions
        ADD COLUMN IF NOT EXISTS extraction_error TEXT
        """
    )


def downgrade() -> None:
    op.execute("ALTER TABLE source_object_versions DROP COLUMN IF EXISTS extraction_error")
