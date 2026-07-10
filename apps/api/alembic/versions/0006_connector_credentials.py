"""Initial schema: connector credentials for Google OAuth (Phase 7, ADR-013)."""

from collections.abc import Sequence

from alembic import op

revision: str = "0006_connector_credentials"
down_revision: str | None = "0005_canonical_knowledge"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS connector_credentials (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_id UUID NOT NULL REFERENCES users(id),
            provider TEXT NOT NULL,
            account_alias TEXT NOT NULL,
            email TEXT,
            refresh_token_encrypted TEXT NOT NULL,
            scopes TEXT[] NOT NULL DEFAULT '{}',
            sync_state JSONB NOT NULL DEFAULT '{}',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE (owner_id, provider, account_alias)
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_connector_credentials_owner "
        "ON connector_credentials (owner_id)"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS connector_credentials")
