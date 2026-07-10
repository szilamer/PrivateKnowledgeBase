# Personal AI-Powered Knowledge Operations System

## Concept and Architecture Document

**Purpose:** summarize the concept of a personal knowledge system that can later support teams and can be operated by AI agents. This document is the conceptual basis for the functional specification.

**Version:** 0.1  
**Status:** Concept  
**Language:** English

---

## 1. Starting point

The user manages several projects in parallel. Information is distributed across documents, email, chat, meeting notes, Git repositories, source code, issues, task managers, cloud storage, local files, notes, images, audio, and video.

The main problem is not only the amount of information, but the fact that relationships between individual pieces of information are usually implicit. A decision may appear in an email, belong to a project, affect several repositories, change a deadline, and later be referenced in a meeting. Traditional folder structures and document search engines do not represent these relationships reliably.

The objective is therefore not another document repository, but an AI-powered knowledge layer that:

1. recognizes the meaning of information;
2. identifies relationships between items;
3. tracks provenance and temporal change;
4. can be queried and used by agents;
5. can later expose selected knowledge to other people and their agents under explicit authorization.

## 2. Vision

The system acts as a personal knowledge operations system. It does not merely store or index files; it builds a continuously updated, context-aware knowledge layer over existing source systems.

It should behave like a persistent AI coworker that can:

- understand active projects;
- remember previous decisions;
- locate relevant evidence;
- connect information across systems;
- detect contradictions and missing context;
- produce summaries and status reports;
- identify tasks and decision points;
- provide structured context to other agents.

Existing applications remain authoritative sources. Gmail, Google Drive, GitHub, Slack, Teams, Notion, Obsidian, Jira, and the local file system do not need to be replaced.

## 3. Core principles

### 3.1 Sources remain authoritative

Original content stays in the source system. The knowledge layer stores references, processing representations, metadata, extracted assertions, and relationships.

### 3.2 The graph is a semantic and relationship layer

The graph primarily stores entities, claims, events, typed relationships, source references, temporal states, and authorization metadata. It points the system toward relevant evidence; retrieval components fetch the actual text or file fragment.

### 3.3 Every claim is traceable

Each knowledge claim MUST record its source, source object, creation time, author when available, processing agent, confidence, pipeline version, and approval state.

### 3.4 AI writes through controlled proposals

AI may propose entities, relationships, claims, or ontology changes. High-impact or uncertain changes MUST pass validation or human approval before becoming canonical knowledge.

### 3.5 Knowledge is temporal

The system records not only what is considered true, but when it was valid. Replaced values remain available as historical states rather than being silently overwritten.

### 3.6 Components are replaceable

Graph storage, vector search, LLM provider, embedding model, workflow engine, agent framework, UI, and authorization implementation MUST be isolated behind stable interfaces.

## 4. High-level architecture

1. Source layer
2. Connector and event layer
3. Triage and processing layer
4. Knowledge-model and graph layer
5. Search and retrieval layer
6. Agent and service layer
7. User interfaces
8. Authorization and security layer
9. Monitoring, audit, and versioning layer

```text
Sources
  ↓
Connectors and events
  ↓
Triage and extraction
  ↓
Proposed knowledge changes
  ↓
Rules / validation / human approval
  ↓
Knowledge graph + vector index + metadata store
  ↓
Agents, search, chat, reports, and automations
```

## 5. Source layer

Potential sources include Gmail, Outlook, Google Drive, OneDrive, Dropbox, local folders, GitHub, GitLab, Bitbucket, Slack, Teams, Discord, Jira, Linear, Trello, Asana, Notion, Obsidian, calendars, meeting transcripts, CRM systems, databases, and internal web applications.

Obsidian may be used either as a source of notes or as a browsing/editing interface. Its built-in graph view is not the canonical knowledge graph because it does not provide a governed typed ontology, provenance, temporal semantics, or reliable query behavior.

## 6. Event-driven ingestion

Connectors detect new or changed content, retain the source identifier, collect required metadata, emit an event, and pass content to the processing pipeline. Incremental processing is preferred over repeated full reindexing.

Typical events include new email, updated document, new commit or pull request, changed issue, completed meeting transcript, new chat message, or changed task deadline.

## 7. Triage and processing

The triage layer determines project relevance, people and organizations involved, decisions, tasks, deadlines, references, contradictions, sensitivity, and approval requirements.

The processing pipeline includes source identification, format parsing, text extraction, language detection, chunking, entity recognition, relationship extraction, claim extraction, temporal interpretation, confidence estimation, deduplication, contradiction detection, and proposal creation.

## 8. Knowledge units

A **knowledge item** is an independently meaningful unit derived from one or more sources. Core types include:

- Entity
- Claim
- Event
- Decision
- Task
- Source object
- Document version
- Content chunk
- Relationship
- Ontology proposal

Each object receives a stable identifier. Source objects may change or be versioned while logical entities keep their identity.

## 9. Hybrid retrieval

The graph answers relationship questions; keyword and vector retrieval locate evidence. Query execution combines access-control filtering, entity resolution, graph expansion, semantic retrieval, ranking, context assembly, and source-backed answer generation.

## 10. Agent layer

Initial agent roles include triage, extraction, entity resolution, contradiction detection, ontology proposal, retrieval planning, answer synthesis, project reporting, and maintenance. Agents MUST use structured outputs and MUST NOT bypass domain services or authorization policies.

## 11. Governance and future sharing

The first release is personal and local-first. The model nevertheless includes ownership, visibility, sensitivity, and service-account concepts so that selected subgraphs can later be exposed to other users or agents without exposing the entire knowledge base.

## 12. Success definition

The system succeeds when the user can ask project-level questions, receive evidence-backed answers, inspect how the answer was derived, approve uncertain changes, and obtain a reliable overview without manually searching multiple systems.
