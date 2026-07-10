# MVP Scope and Product Requirements

**Version:** 0.1  
**Status:** Draft  
**Related document:** `01-project-vision-and-concept.md`

## 1. Purpose

This document defines the objective, boundaries, and success criteria of the first working product version. The MVP is not the complete knowledge operations system; it is the smallest independently valuable version.

## 2. Product hypothesis

A single user can process documents and GitHub data from several projects through one knowledge layer and obtain reliable natural-language answers, with citations, about project status, decisions, tasks, technologies, and related information.

## 3. Primary user

- One technically capable owner-user.
- Manages multiple projects in parallel.
- Needs to connect documents, repositories, tasks, and decisions.
- Accepts manual review of uncertain AI-generated proposals.

## 4. Included sources

1. Local Markdown, TXT, and PDF documents.
2. One or more GitHub repositories, including repository metadata, issues, pull requests, commit metadata, README files, and selected documentation.
3. Manual entry through the web UI for projects, people, decisions, tasks, and notes.

## 5. Excluded from the MVP

- Continuous email monitoring (Phase 7 introduces user-scoped Gmail sync runs — see `docs/13-personal-source-connectors-supplement.md`).
- Slack or Teams integration.
- Automatic two-way modification of external systems.
- Multi-user organizational authorization.
- Full agent-to-agent protocol.
- Audio and video processing.
- Mobile application.
- Unrestricted autonomous ontology expansion.

## 6. Required capabilities

### MVP-01 — Register a source
The user can register a local folder or GitHub repository.

### MVP-02 — Start synchronization
The user can start a full or incremental synchronization manually.

### MVP-03 — Extract entities and knowledge
The system recognizes at least project, person, document, repository, decision, task, event, technology, and concept.

### MVP-04 — Approval queue
Uncertain or high-impact changes enter an approval queue.

### MVP-05 — Hybrid search
Keyword, vector, and graph signals are combined.

### MVP-06 — Source-backed question answering
Every material answer claim is linked to supporting evidence.

### MVP-07 — Project overview
The system shows a project's documents, repositories, decisions, open tasks, and recent events.

### MVP-08 — Graph browser
The user can visually traverse entities and relationships to a bounded depth.

### MVP-09 — Audit log
Every knowledge change is traceable.

## 7. Success criteria

The MVP is successful when:

1. sources from at least three real projects can be processed;
2. at least 80% of the agreed evaluation questions receive relevant answers;
3. at least 95% of material answer claims have a source reference;
4. high-uncertainty claims are not finalized without human control;
5. changed documents can be processed incrementally;
6. a user can understand the current state of an unfamiliar project within ten minutes.

## 8. Non-functional requirements

- Deployable locally or on self-controlled infrastructure.
- Secrets MUST NOT be committed to source control.
- Data can be exported in standard formats.
- Components are containerized.
- Failure MUST NOT modify or delete original sources.
- LLM and embedding providers are replaceable through interfaces.

## 9. Product decisions resolved by ADRs

Runtime, backend, stores, graph database, queue, orchestration, provider strategy, frontend, authentication, document processing, ontology storage, and observability are defined by the accepted ADR package.
