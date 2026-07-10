---
name: phase-1-source-ingestion
description: Implement Phase 1 source registry and ingestion — local folders, GitHub repos, sync runs, source object versions. Use for MVP-01 and MVP-02 work.
---

# Phase 1 — Source Registry and Ingestion

Per `docs/11-implementation-plan-and-backlog.md` §3 and MVP requirements.

## Scope

- **MVP-01** — Register local folder or GitHub repository as a source
- **MVP-02** — Manual full/incremental synchronization

## Domain objects

- `Source` — type, name, owner, configuration, enabled, default_project_id
- `SourceObject` — stable `(source_id, external_id)`
- `SourceObjectVersion` — immutable; content hash, MIME, extraction status
- Sync run aggregate with status, errors, retry state

## Implementation order

1. Alembic: `sources`, `source_objects`, `source_object_versions`, `sync_runs` tables
2. Domain models and validation
3. `SourceRegistry` use cases (register, list, enable/disable)
4. `LocalFolderConnector` adapter (path traversal protection — security tests)
5. `GitHubConnector` adapter (token from secrets, scoped permissions)
6. API: `POST/GET /api/v1/sources`, `POST /api/v1/sync-runs`
7. Celery `ingestion` queue tasks: idempotent sync, incremental via content hash
8. Worker retry + dead-letter for permanent failures
9. Minimal UI: source list, register form, sync trigger, error display
10. Tests: unit (hash, identity), integration (connectors), e2e (register → sync)

## Security

- Path traversal tests for local folder connector
- GitHub token in secrets only
- Authorization before listing source content

## EPIC reference

EPIC-02 Source connectors
