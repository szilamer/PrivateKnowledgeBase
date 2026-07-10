# ADR-005: Background Jobs and Event Processing

**Status:** Accepted  
**Decision date:** 2026-07-10

## Decision

Redis is the broker and short-lived coordination store; Celery workers perform background jobs. Required queues are `ingestion`, `extraction`, `embedding`, `graph_projection`, and `maintenance`.

## Rules

Every task is idempotent. Retries apply only to classified transient errors. Dead-letter state and operator-triggered retry are required. Durable business state must not exist only in Redis.

## Consequences

Celery-specific calls remain behind a `TaskDispatcher` adapter.
