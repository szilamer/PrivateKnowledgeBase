# ADR-008: Frontend

**Status:** Accepted  
**Decision date:** 2026-07-10

## Decision

The web client uses Next.js and TypeScript. MVP surfaces cover sources and synchronization, processing status, proposal approval, hybrid search and Q&A, entity and graph views, audit, and errors. Components use an accessible design system based on headless primitives.

## Consequences

The API client may be generated from OpenAPI. Business logic does not live in React components. Graph visualization remains behind an adapter component.
