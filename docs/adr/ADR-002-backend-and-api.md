# ADR-002: Backend and API Technology

**Status:** Accepted  
**Decision date:** 2026-07-10

## Decision

- Python 3.12+
- FastAPI
- Pydantic v2
- SQLAlchemy 2.x
- Alembic
- REST/JSON API with OpenAPI specification

Domain logic lives in framework-independent Python modules. FastAPI routes perform validation, authorization checks, and use-case invocation only.

## Rationale

This stack aligns with the Python ecosystem for AI, document processing, and agent libraries while providing a machine-readable API contract.

## Consequences

Static type checking is mandatory. External integrations are accessed through adapters. The API version prefix is `/api/v1`.
