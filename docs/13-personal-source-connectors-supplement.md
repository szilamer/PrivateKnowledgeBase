# Personal Source Connectors — Specification Supplement

**Version:** 0.1  
**Status:** Draft — implementation input for Phase 7  
**Related documents:**

- `docs/02-mvp-scope-and-product-requirements.md`
- `docs/03-functional-specification.md`
- `docs/04-domain-model-and-ontology.md`
- `docs/06-system-architecture.md`
- `docs/07-technical-specification.md`
- `docs/14-source-connection-ui-supplement.md`
- `docs/adr/ADR-013-google-workspace-connectors.md`

## 1. Purpose

This supplement extends the MVP source model so a single owner user can connect **personal knowledge locations** without Docker, mount paths, or API expertise.

After implementation, the user MUST be able to configure:

1. **Local folders** on the host machine
2. **Google Drive folders**
3. **Email** (Gmail in the first slice)
4. **Google Calendar**

GitHub and manual entry remain supported from the MVP. This supplement does not remove existing connectors.

## 2. Problem statement

The MVP implemented source registration as a developer-oriented flow (raw paths, container visibility, REST payloads). That is insufficient for the product vision in `docs/01-project-vision-and-concept.md`, where information lives across local files, cloud storage, email, and calendars.

Phase 7 closes this gap with:

- a **declarative source configuration** model the user can edit without infrastructure knowledge;
- **connector adapters** with identical ingestion semantics to existing local-folder sync;
- a **connection UI** defined in `docs/14-source-connection-ui-supplement.md`.

## 3. Scope

### 3.1 In scope

| Source type | First implementation target | Sync model |
|---|---|---|
| Local folder | macOS host paths | Manual + scheduled full/incremental |
| Google Drive folder | One or more selected Drive folders | Incremental via Drive Changes API |
| Gmail | Labels / search query scope | Incremental via Gmail History API |
| Google Calendar | One or more calendars | Incremental via Calendar syncToken |

### 3.2 Out of scope (Phase 7)

- Outlook / Microsoft 365
- Slack, Teams, Notion, Obsidian sync
- Continuous sub-second push webhooks (polling/sync-run model is sufficient initially)
- Two-way write-back to external systems
- Attachment OCR beyond PDF/text already supported by document processing
- Multi-user organizational authorization

## 4. User configuration model

### 4.1 Principle

The user edits **one configuration file** or uses the **Source Connection UI**. The system MUST NOT require the user to understand Docker volumes, container paths, or internal mount points.

### 4.2 Declarative configuration file

**Path:** `config/sources.yaml` (repository-local, gitignored secrets referenced by name only)

```yaml
version: "1"

# Optional: auto-sync on startup and on a schedule
sync:
  on_startup: true
  interval_minutes: 60

sources:
  - id: projects-local
    type: local_folder
    name: Projektek
    enabled: true
    paths:
      - ~/Projects
      - ~/Documents/Projektek
    include_extensions: [".md", ".txt", ".pdf"]
    exclude_globs:
      - "**/node_modules/**"
      - "**/.git/**"

  - id: work-drive
    type: google_drive
    name: Munka Google Drive
    enabled: true
    account: google:primary          # OAuth account reference
    folder_ids:
      - "1A2B3C..."                   # or selected via UI picker
    include_google_docs: true
    include_extensions: [".md", ".txt", ".pdf"]

  - id: gmail-inbox
    type: gmail
    name: Fontos emailek
    enabled: true
    account: google:primary
    query: "label:important newer_than:365d"
    include_attachments: true
    attachment_extensions: [".pdf", ".txt", ".md"]

  - id: personal-calendar
    type: google_calendar
    name: Saját naptár
    enabled: true
    account: google:primary
    calendar_ids:
      - primary
    horizon_past_days: 365
    horizon_future_days: 90
```

### 4.3 Environment override (optional)

For Docker deployments, host paths MAY be listed in `.env`:

```env
PKB_SOURCE_DIRS=/Users/me/Projects,/Users/me/Documents
```

The bootstrap service MUST translate host paths to container-visible paths automatically. The user MUST NOT specify container-internal paths.

### 4.4 Bootstrap behaviour

On API startup (and on `sources.yaml` change when hot-reload is enabled):

1. Parse and validate `config/sources.yaml`.
2. Upsert entries into the source registry.
3. If `sync.on_startup` is true, enqueue incremental sync runs per enabled source.
4. Surface validation errors in `/sources` UI and `GET /api/v1/sources/health`.

## 5. Functional requirements

### FR-SRC-010 Declarative source configuration

The user can define all personal sources in `config/sources.yaml` without using REST payloads or Docker commands.

**Acceptance:** Given a valid file with two local paths and one Gmail scope, after `make up` the source registry contains three enabled sources and at least one sync run completes per source.

### FR-SRC-011 Local folder host paths

The system accepts tilde-expanded host paths (`~/Projects`) and MUST make them visible to ingestion workers without user-supplied mount configuration.

**Acceptance:** Registering `~/Projects` indexes a new `.md` file placed there after sync without editing `docker-compose.yml`.

### FR-SRC-012 Google account connection

The user connects one Google account granting scoped OAuth access for Drive, Gmail, and Calendar through a single consent flow where possible.

**Acceptance:** After OAuth, the UI shows connected account status and allows adding Drive folders, Gmail scopes, and calendars without re-authenticating for each.

### FR-SRC-013 Google Drive folder source

The user selects one or more Drive folders. The connector discovers files recursively, exports Google Docs to text, and records stable `external_id` per Drive file revision.

**Acceptance:** A Google Doc edit triggers a new source object version on the next sync; canonical knowledge is not duplicated (FR-ING-003).

### FR-SRC-014 Gmail source

The user defines a mailbox scope by label, query, or predefined preset (e.g. Important, Last 12 months). Each message is a source object with immutable `message_id`.

**Acceptance:** Email body text is searchable; citations link to the stored message reference and subject line.

### FR-SRC-015 Google Calendar source

The user selects calendars and a time horizon. Each event is a source object; extraction proposes `event` entities and temporal claims.

**Acceptance:** A calendar event title and description appear in search results after sync and approval.

### FR-SRC-016 Unified sync status

All connector types expose the same sync-run model: discovered, processed, failed, error summary, correlation ID.

**Acceptance:** `/sources` UI displays identical status components for local, Drive, Gmail, and Calendar sources.

### FR-SRC-017 Credential safety

OAuth refresh tokens and API secrets MUST be stored outside git-tracked files using the existing secret mechanism. `sources.yaml` references accounts by alias only.

**Acceptance:** No refresh token appears in logs, audit exports, or repository files.

## 6. Domain model extensions

### 6.1 Source types

Extend `SourceType`:

| Value | Description |
|---|---|
| `local_folder` | Existing — host paths via bootstrap |
| `github` | Existing |
| `google_drive` | New |
| `gmail` | New |
| `google_calendar` | New |

### 6.2 Source object identity

| Source type | `external_id` | `object_type` |
|---|---|---|
| Local file | Relative path from source root | `file` |
| Drive file | Drive file ID + revision | `file` |
| Gmail message | Gmail message ID | `email` |
| Calendar event | Calendar ID + event ID + etag | `calendar_event` |

### 6.3 Configuration schema (per type)

Stored in `sources.configuration` JSONB:

**`google_drive`:** `account`, `folder_ids[]`, `include_google_docs`, `include_extensions[]`

**`gmail`:** `account`, `query`, `label_ids[]`, `include_attachments`, `attachment_extensions[]`

**`google_calendar`:** `account`, `calendar_ids[]`, `horizon_past_days`, `horizon_future_days`

## 7. Architecture

### 7.1 Connector factory

`ConnectorFactory` dispatches by `SourceType`:

```text
LocalFolderConnector       (existing)
GitHubConnector            (existing)
GoogleDriveConnector       (new)
GmailConnector             (new)
GoogleCalendarConnector    (new)
```

Each connector implements:

- `discover(source) -> list[DiscoveredObject]`
- `fetch_metadata(source, external_id)` when needed for incremental sync

### 7.2 OAuth and token storage

- New adapter: `GoogleOAuthService` (authorization URL, callback, token refresh)
- Tokens stored encrypted in PostgreSQL `connector_credentials` table or existing secrets store
- Scopes (minimum):
  - Drive: `drive.readonly`
  - Gmail: `gmail.readonly`
  - Calendar: `calendar.readonly`

See `docs/adr/ADR-013-google-workspace-connectors.md`.

### 7.3 Parsers

| Object type | Parser |
|---|---|
| `file` | Existing Markdown/text/PDF pipeline |
| `email` | New `EmailParser` (HTML → text, headers metadata) per ADR-010 priority |
| `calendar_event` | New `CalendarEventParser` (structured text from VEVENT fields) |

### 7.4 Workers and queues

No new queue required. Connectors run in existing `ingestion` tasks. Google API rate limits use bounded retry with backoff (ADR-005).

### 7.5 Docker/host path bridging

New component: `HostPathBridge`

- Reads `PKB_SOURCE_DIRS` and `sources.yaml` local paths
- Ensures worker and API containers receive read-only bind mounts generated at compose up time
- Implementation option A: `make up` renders `infra/docker/docker-compose.override.generated.yml` from template
- Implementation option B: API runs on host in “simple mode” profile without path bridging

Preferred for local-first MVP+: **Option A** so the user still runs one `make up` command.

## 8. API extensions

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/v1/sources/config` | Return effective merged config (secrets redacted) |
| `PUT` | `/api/v1/sources/config` | Replace declarative config (validates schema) |
| `GET` | `/api/v1/connectors/google/auth-url` | Start OAuth |
| `GET` | `/api/v1/connectors/google/callback` | OAuth callback |
| `GET` | `/api/v1/connectors/google/accounts` | List connected accounts |
| `DELETE` | `/api/v1/connectors/google/accounts/{id}` | Revoke connection |
| `GET` | `/api/v1/connectors/google/drive/folders` | Browse folders for picker |
| `GET` | `/api/v1/connectors/google/calendars` | List calendars for picker |

Existing `/api/v1/sources/*` and `/api/v1/sync-runs` remain valid.

## 9. Security and privacy

- Google tokens are **read-only** scopes only in Phase 7.
- Email and calendar content inherit default sensitivity `internal`; the user may mark a source `confidential`.
- Before sending email/calendar text to an external LLM, existing provider policy checks apply (`docs/10-knowledge-management-and-security-policy.md`).
- Revoking Google access MUST disable dependent sources and stop future sync without deleting canonical knowledge.

## 10. Implementation phases

### Phase 7a — Local path simplicity

- `config/sources.yaml` schema and validation
- `HostPathBridge` + bootstrap upsert
- Remove requirement for manual Docker mounts in operator docs

### Phase 7b — Google OAuth foundation

- OAuth flow, credential storage, account status UI
- ADR-013 accepted

### Phase 7c — Google Drive connector

- Folder picker, discovery, incremental sync, Google Docs export

### Phase 7d — Gmail connector

- Query/label scope, message parsing, attachment ingestion

### Phase 7e — Google Calendar connector

- Calendar picker, event ingestion, event extraction tuning

Each slice includes: domain types, connector, API, worker, web UI section (per doc 14), tests, audit.

## 11. Acceptance tests

### AT-SRC-01 Local path bootstrap

User adds `~/Projects` to `sources.yaml`, runs `make up`, sync completes, search finds project README.

### AT-SRC-02 Drive folder sync

User selects a Drive folder via UI, sync indexes a Google Doc, edit creates new version.

### AT-SRC-03 Gmail scope sync

User connects Important emails, sync indexes messages, Q&A cites subject and body excerpt.

### AT-SRC-04 Calendar sync

User connects primary calendar, sync indexes upcoming meeting, dashboard shows event.

### AT-SRC-05 No infrastructure vocabulary

New user completes all four source types using only web UI + `sources.yaml` template without reading Docker documentation.

## 12. Relationship to MVP scope

`docs/02-mvp-scope-and-product-requirements.md` explicitly excluded continuous email monitoring. Phase 7 introduces **user-controlled mailbox and calendar scopes** via sync runs, not background inbox surveillance. Update MVP scope document when Phase 7 is approved.

## 13. Open decisions

| ID | Question | Default proposal |
|---|---|---|
| OD-01 | Single `sources.yaml` vs database-only config | Both: file for bootstrap, DB canonical after first import |
| OD-02 | Google Docs export format | `text/plain` export |
| OD-03 | Gmail attachment size limit | 10 MB per attachment |
| OD-04 | Calendar recurring events | Expand instances within horizon window |
