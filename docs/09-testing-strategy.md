# Testing and Quality Assurance Strategy

**Version:** 0.1  
**Status:** Draft

## 1. Objectives

Testing must establish functional correctness, data integrity, authorization safety, provenance completeness, repeatable AI behavior, and operational recoverability.

## 2. Test layers

### Unit tests
Domain entities, validation rules, policy decisions, temporal logic, deduplication, parsers, ranking functions, and deterministic graph transformations.

### Integration tests
PostgreSQL, pgvector, Neo4j projection, Redis/Celery, local connectors, GitHub adapter, parser adapters, and provider adapters using controlled fixtures.

### Contract tests
OpenAPI compatibility, connector interfaces, LLM structured-output schemas, repository interfaces, and event schemas.

### End-to-end tests
Register source, synchronize, review proposals, search, ask a question, inspect citations, and browse the graph.

### Evaluation tests
Golden questions and source corpora measure relevance, citation correctness, unsupported-claim rate, extraction precision/recall, entity-resolution accuracy, and contradiction detection.

## 3. Required quality targets

- 100% schema-valid canonical writes.
- 100% provenance presence for approved claims.
- At least 95% source coverage for material answer claims in the MVP evaluation set.
- No unauthorized result in retrieval security tests.
- Idempotent reprocessing of identical source versions.
- Rebuildable Neo4j projection.

## 4. AI regression

Prompts, models, schemas, and ontology versions are recorded. Any change to them runs the relevant evaluation suite and compares results with the approved baseline.

## 5. Security tests

Include path traversal, malicious document content, prompt injection, cross-project access, secret leakage, unsafe file types, query injection, denial-of-service limits, and dependency scanning.

## 6. Recovery tests

Verify worker restart, retry behavior, dead-letter handling, PostgreSQL restore, projection rebuild, and interrupted synchronization recovery.
