"""Add evidence JSONB to contradiction_findings (Phase D)."""

from collections.abc import Sequence

from alembic import op

revision: str = "0008_contradiction_evidence"
down_revision: str | None = "0007_extraction_error"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE contradiction_findings
        ADD COLUMN IF NOT EXISTS evidence JSONB NOT NULL DEFAULT '{}'
        """
    )


def downgrade() -> None:
    op.execute("ALTER TABLE contradiction_findings DROP COLUMN IF EXISTS evidence")
