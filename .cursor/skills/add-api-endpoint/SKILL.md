---
name: add-api-endpoint
description: Add a new REST endpoint under /api/v1 with OpenAPI, error envelope, auth, and tests. Use when adding sources, sync-runs, proposals, or other API resources.
---

# Add API Endpoint

## Checklist

1. **Resource** — confirm path in `docs/07-technical-specification.md` §3
2. **Domain + application** — use case exists before route
3. **Route** (`apps/api/src/api/routes/`) — thin handler only:
   - Pydantic request/response models
   - Authorization check
   - Use case invocation
   - Map domain errors to error envelope: `{ code, message, details, correlation_id }`
4. **Register router** in `main.py` under `/api/v1`
5. **OpenAPI** — verify at `/api/docs`
6. **Tests** — contract test for request/response shape; integration test for happy path
7. **Pagination** — cursor-based for list endpoints
8. **Idempotency** — `Idempotency-Key` header for long-running user triggers

## Error codes

Use stable `code` strings: `not_found`, `validation_error`, `unauthorized`, `conflict`, `internal_error`.

## Do not

- Put business logic in the route
- Access database directly from route
- Change existing response shapes without documenting breaking change
