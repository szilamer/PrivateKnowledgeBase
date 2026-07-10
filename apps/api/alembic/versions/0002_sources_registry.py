"""Initial schema: sources registry, sync runs, and audit foundation (MVP-01, MVP-02)."""

from collections.abc import Sequence

from alembic import op

revision: str = "0002_sources_registry"
down_revision: str | None = "0001_outbox_foundation"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

DEFAULT_OWNER = "00000000-0000-4000-8000-000000000001"


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            username TEXT NOT NULL UNIQUE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )
    op.execute(
        f"""
        INSERT INTO users (id, username)
        VALUES ('{DEFAULT_OWNER}'::uuid, 'owner')
        ON CONFLICT (username) DO NOTHING
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS sources (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            type TEXT NOT NULL,
            name TEXT NOT NULL,
            owner_id UUID NOT NULL REFERENCES users(id),
            configuration JSONB NOT NULL DEFAULT '{}',
            enabled BOOLEAN NOT NULL DEFAULT TRUE,
            default_project_id UUID,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            version INTEGER NOT NULL DEFAULT 1
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_sources_owner ON sources (owner_id)")
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS sync_runs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            source_id UUID NOT NULL REFERENCES sources(id),
            mode TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            correlation_id TEXT NOT NULL,
            idempotency_key TEXT,
            objects_discovered INTEGER NOT NULL DEFAULT 0,
            objects_processed INTEGER NOT NULL DEFAULT 0,
            objects_failed INTEGER NOT NULL DEFAULT 0,
            error_summary TEXT,
            started_at TIMESTAMPTZ,
            completed_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_sync_runs_idempotency "
        "ON sync_runs (source_id, idempotency_key) WHERE idempotency_key IS NOT NULL"
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS source_objects (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            source_id UUID NOT NULL REFERENCES sources(id),
            external_id TEXT NOT NULL,
            object_type TEXT NOT NULL DEFAULT 'file',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE (source_id, external_id)
        )
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS source_object_versions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            source_object_id UUID NOT NULL REFERENCES source_objects(id),
            content_hash TEXT NOT NULL,
            mime_type TEXT,
            observed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            extraction_status TEXT NOT NULL DEFAULT 'pending',
            content_ref TEXT,
            pipeline_version TEXT NOT NULL DEFAULT '0.1.0',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE (source_object_id, content_hash, pipeline_version)
        )
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS audit_events (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            actor_id UUID NOT NULL,
            action TEXT NOT NULL,
            object_type TEXT NOT NULL,
            object_id UUID NOT NULL,
            correlation_id TEXT NOT NULL,
            metadata JSONB NOT NULL DEFAULT '{}',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_audit_events_object "
        "ON audit_events (object_type, object_id)"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS audit_events")
    op.execute("DROP TABLE IF EXISTS source_object_versions")
    op.execute("DROP TABLE IF EXISTS source_objects")
    op.execute("DROP TABLE IF EXISTS sync_runs")
    op.execute("DROP TABLE IF EXISTS sources")
    op.execute("DELETE FROM users WHERE id = '00000000-0000-4000-8000-000000000001'::uuid")
    op.execute("DROP TABLE IF EXISTS users")
