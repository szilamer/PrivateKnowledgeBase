# Operator Guide

**Version:** 0.1  
**Audience:** Single-user MVP operators

## Overview

PostgreSQL is the source of truth. Neo4j is a derived projection rebuilt from canonical tables and the outbox pipeline.

## Daily operations

```bash
make up
curl http://localhost:8000/api/v1/health
curl http://localhost:8000/api/v1/operations/status
```

Key status fields:

- `pending_outbox_events` — events waiting for graph projection
- `failed_outbox_events` — projection failures requiring attention
- `projection_rebuild_recommended` — true when failed events exist or backlog is high

## Backup

```bash
make backup
```

Creates a timestamped directory under `backups/` with:

- `postgres.sql` — full PostgreSQL dump
- `manifest.json` — metadata

Neo4j is not backed up separately in MVP. After restore, rebuild the graph from PostgreSQL.

## Restore

```bash
make restore BACKUP=backups/20260101T120000Z
make rebuild-projection
```

## Projection rebuild

Rebuild clears owner-scoped Neo4j nodes and repopulates from canonical PostgreSQL:

```bash
# Synchronous (API must be running)
make rebuild-projection

# Asynchronous (worker queue)
curl -X POST "http://localhost:8000/api/v1/operations/projection/rebuild?async=true"
```

Use rebuild after:

- PostgreSQL restore
- suspected Neo4j drift
- repeated outbox projection failures

## Load smoke

With the stack running:

```bash
make load-smoke
```

Runs 50 health-check requests against the API.

## Troubleshooting

| Symptom | Action |
|---|---|
| Health 503 on neo4j | `make logs`, verify Neo4j container healthy |
| Rising `failed_outbox_events` | Inspect worker logs, run projection rebuild |
| Empty graph after restore | Run `make rebuild-projection` |
| Stale search results | Confirm ingestion worker processed latest sync |

## Security notes (MVP)

- Single default owner (`DEFAULT_OWNER_ID`); no multi-tenant auth yet
- Change default passwords in `.env` before any network exposure
- Do not expose Docker ports publicly without TLS and authentication
