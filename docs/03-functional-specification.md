# Functional Specification

**Version:** 0.1  
**Status:** Draft  
**Scope:** MVP

## 1. Actors

- **Owner user:** configures sources, reviews proposals, searches knowledge, and administers the local deployment.
- **Connector:** reads authorized external or local sources.
- **Processing worker:** parses and transforms source objects.
- **Knowledge agent:** proposes structured entities, claims, and relationships.
- **System administrator:** operates the deployment; initially identical to the owner user.

## 2. Source management

### FR-SRC-001 Register local source
The user can register a permitted local path, choose supported file types, assign a default project, and enable or disable processing.

### FR-SRC-002 Register GitHub source
The user can register a repository using an access token stored through the secret mechanism. Repository identity, default branch, and selected content scopes are recorded.

### FR-SRC-003 Source status
The UI displays last synchronization, current state, processed-object count, warnings, and errors.

### FR-SRC-004 Remove source
Removing a source stops future ingestion. Canonical knowledge is not silently deleted; the user receives an impact preview and may archive or explicitly remove derived records.

### FR-SRC-010 … FR-SRC-017 Personal source connectors

See `docs/13-personal-source-connectors-supplement.md` for declarative configuration, local host paths, Google Drive, Gmail, and Google Calendar requirements.

### FR-UI-SRC-001 … FR-UI-SRC-007 Source connection UI

See `docs/14-source-connection-ui-supplement.md` for the intuitive wizard-based source management interface.

## 3. Ingestion and processing

### FR-ING-001 Full synchronization
A full run enumerates eligible objects and compares source identities and content hashes.

### FR-ING-002 Incremental synchronization
Only new, changed, or deleted source versions are processed.

### FR-ING-003 Idempotency
Reprocessing the same source version with the same pipeline version MUST NOT create duplicate canonical objects.

### FR-ING-004 Partial failure
A failed object is recorded independently and does not invalidate successful objects in the same run.

### FR-ING-005 Processing visibility
Each run exposes stage, progress, timing, warnings, retry state, and correlation ID.

## 4. Extraction and proposals

### FR-KNW-001 Structured extraction
The extraction service produces schema-valid proposals for entities, claims, relationships, tasks, decisions, events, and source links.

### FR-KNW-002 Confidence
Every AI-generated proposal includes confidence, model identifier, prompt version, schema version, pipeline version, and evidence span.

### FR-KNW-003 Entity resolution
The system matches proposed entities against existing entities and presents ambiguous matches for review.

### FR-KNW-004 Contradictions
Potential contradictions are stored as reviewable findings; the system does not silently overwrite an existing claim.

### FR-KNW-005 Temporal validity
Claims may include `valid_from`, `valid_to`, `observed_at`, and status.

## 5. Approval workflow

### FR-APR-001 Queue
The queue can be filtered by project, proposal type, confidence, risk, source, and age.

### FR-APR-002 Decision
The user can approve, reject, edit-and-approve, merge, or defer a proposal.

### FR-APR-003 Batch approval
Only low-risk proposals of the same validated type may be batch approved.

### FR-APR-004 Audit
The original proposal and the final approved form are both retained.

## 6. Search and question answering

### FR-RET-001 Search modes
The user can perform keyword, semantic, entity, relationship, and hybrid search.

### FR-RET-002 Access control
Authorization filtering is applied before or during retrieval, not only after generation.

### FR-RET-003 Answer generation
The system assembles a bounded context and returns an answer, citations, confidence indicators, and relevant related entities.

### FR-RET-004 Insufficient evidence
When evidence is insufficient or conflicting, the answer MUST state this rather than fabricate certainty.

### FR-RET-005 Explainability
The user can inspect retrieved chunks, graph paths, and source objects used for the answer.

## 7. Project overview

### FR-PRJ-001 Dashboard
The project view contains summary, source coverage, people, repositories, decisions, open tasks, technologies, recent events, unresolved contradictions, and processing health.

### FR-PRJ-002 Status report
The user can generate a source-backed report for a selected time range.

## 8. Graph browsing

### FR-GRF-001 Entity view
The user can inspect entity attributes, aliases, relationships, claims, sources, and history.

### FR-GRF-002 Traversal limits
The UI and API enforce depth, node-count, and time limits.

### FR-GRF-003 Provenance path
A claim can be traced to the exact source object and evidence span.

## 9. Ontology governance

### FR-ONT-001 Ontology proposal
AI may propose a new type, relationship, field, alias, or deprecation.

### FR-ONT-002 Human approval
Ontology proposals cannot directly alter the normative ontology.

### FR-ONT-003 Versioning
Accepted changes require a reviewed YAML change and ontology version increment.

## 10. Administration

The system provides health checks, configuration visibility without revealing secrets, failed-job management, retry controls, export, backup guidance, and audit search.

## 11. Error behavior

Errors use stable machine-readable codes and a human-readable message. External-source failures, parser failures, provider failures, schema validation failures, authorization failures, and projection lag are distinguishable.
