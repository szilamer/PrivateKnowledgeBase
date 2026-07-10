# ADR-001: Runtime and Deployment Model

**Status:** Accepted  
**Decision date:** 2026-07-10

## Decision

The MVP is a **local-first**, Docker Compose-based system. Separate containers run the web client, API, worker, PostgreSQL, Redis, and Neo4j. Persistent data remains in Docker volumes or explicit host mounts. Services should be stateless where practical to allow later migration to Kubernetes or a managed container platform.

## Consequences

- The development environment starts with one documented command.
- Cloud deployment is not an MVP requirement.
- Connectors and model adapters have explicit network and secret configuration.
- Backup and restore are documented in the MVP.
