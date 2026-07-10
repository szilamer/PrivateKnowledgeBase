"""Initial schema: pgvector extension and transactional outbox foundation."""

from collections.abc import Sequence

from alembic import op

revision: str = "0001_outbox_foundation"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS outbox_events (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            aggregate_type TEXT NOT NULL,
            aggregate_id TEXT NOT NULL,
            event_type TEXT NOT NULL,
            payload JSONB NOT NULL DEFAULT '{}',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            processed_at TIMESTAMPTZ,
            retry_count INTEGER NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'pending'
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_outbox_events_status_created "
        "ON outbox_events (status, created_at)"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS outbox_events")
    op.execute("DROP EXTENSION IF EXISTS vector")
