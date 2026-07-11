-- Pending migrations 0008 through 0012 (applied manually when Docker registry unavailable)

ALTER TABLE contradiction_findings
ADD COLUMN IF NOT EXISTS evidence JSONB NOT NULL DEFAULT '{}';

ALTER TABLE source_object_versions
ADD COLUMN IF NOT EXISTS triage_status TEXT NOT NULL DEFAULT 'pending';

ALTER TABLE source_object_versions
ADD COLUMN IF NOT EXISTS triage_metadata JSONB NOT NULL DEFAULT '{}';

CREATE INDEX IF NOT EXISTS idx_source_object_versions_triage_status
ON source_object_versions (triage_status);

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
);

CREATE INDEX IF NOT EXISTS idx_project_reports_owner
ON project_reports (owner_id, project_entity_id);

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
);

CREATE INDEX IF NOT EXISTS idx_ontology_proposals_owner_status
ON ontology_proposals (owner_id, status);

ALTER TABLE source_object_versions
ADD COLUMN IF NOT EXISTS maintenance_flags JSONB NOT NULL DEFAULT '{}';

UPDATE alembic_version SET version_num = '0012_maintenance_flags';
