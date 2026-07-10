---
name: add-celery-task
description: Add a Celery background task with correct queue, idempotency, retry, and dead-letter handling. Use for ingestion, extraction, embedding, graph_projection, or maintenance work.
---

# Add Celery Task

## Queue assignment

| Domain | Queue |
|---|---|
| Source sync, connectors | `ingestion` |
| Knowledge extraction | `extraction` |
| Embedding generation | `embedding` |
| Neo4j projection | `graph_projection` |
| Health, cleanup, reprocess | `maintenance` |

## Task template

1. Place in `apps/worker/src/worker/tasks/<queue_area>.py`
2. Task name: `worker.tasks.<area>.<task_name>`
3. Call application service — not DB client
4. Log with correlation ID via `observability.logging`
5. Idempotent: safe to retry on same input
6. Transient errors: `autoretry_for` with exponential backoff (bounded)
7. Permanent errors: mark dead-letter state in PostgreSQL, do not infinite retry

## Register

- Add to `celery_app.autodiscover_tasks` if new module
- Verify `task_routes` in `celery_app.py` maps to correct queue

## Tests

Integration test with Redis/Celery fixture or task unit test with mocked application service.
