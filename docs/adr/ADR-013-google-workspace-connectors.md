# ADR-013: Google Workspace Connectors

**Status:** Proposed  
**Date:** 2026-07-10  
**Deciders:** Product owner, system architect  
**Related:** `docs/13-personal-source-connectors-supplement.md`

## Context

Phase 7 requires Google Drive folders, Gmail, and Google Calendar as first-class personal sources. The MVP includes only local folders and GitHub. Users expect a single Google sign-in comparable to consumer productivity tools.

## Decision drivers

- Minimize OAuth consent friction (one account, multiple services).
- Read-only access to reduce security and trust barriers.
- Reuse existing ingestion pipeline (`DiscoveredObject` → version → chunk → extract).
- Local-first deployment must work with Docker Compose and stored refresh tokens.
- Provider policy must gate LLM submission of email/calendar content.

## Decision

1. Implement **three connectors** backed by one `GoogleOAuthService`:
   - `GoogleDriveConnector`
   - `GmailConnector`
   - `GoogleCalendarConnector`

2. Use **OAuth 2.0 authorization code flow** with offline access (`access_type=offline`, `prompt=consent` on first connect).

3. Request **read-only scopes** only:
   - `https://www.googleapis.com/auth/drive.readonly`
   - `https://www.googleapis.com/auth/gmail.readonly`
   - `https://www.googleapis.com/auth/calendar.readonly`

4. Store refresh tokens in PostgreSQL table `connector_credentials`, encrypted at rest, referenced by alias (`google:primary`) from `sources.yaml` and UI config.

5. Use **incremental sync** APIs:
   - Drive: `changes.list` with `pageToken`
   - Gmail: `users.history.list` with `historyId`
   - Calendar: `events.list` with `syncToken`

6. **Google Docs** are ingested via export (`text/plain` or `text/html` then normalized).

7. Sync is triggered by **sync runs** (manual + scheduled), not push webhooks, in the first release.

## Alternatives considered

| Alternative | Rejected because |
|---|---|
| Service account + domain-wide delegation | Requires Google Workspace admin; poor fit for personal single-user MVP |
| Separate OAuth per connector | Worse UX; triple consent prompts |
| IMAP for Gmail | Does not cover Drive/Calendar; harder OAuth story on Google |
| Full mailbox push via Pub/Sub | Operational complexity exceeds Phase 7 needs |
| Store tokens in flat `.env` | Violates secret handling policy |

## Consequences

### Positive

- Unified Google connection UX.
- Incremental sync reduces API quota and processing cost.
- Clear alignment with product vision for personal knowledge sources.

### Negative

- Google API quota and rate limits require retry/backoff tuning.
- Token rotation and revocation flows add operational surface.
- Calendar recurring event expansion adds parsing complexity.

### Neutral

- New migrations for `connector_credentials` and extended `SourceType` enum.
- New Celery task parameters for per-account rate limiting.

## Compliance

- Tokens MUST NOT appear in logs or audit payloads.
- Revocation MUST mark sources disabled and surface UI reconnect banner.
- Email/calendar content MUST pass provider policy before external LLM calls.

## Migration

Existing sources unaffected. New enum values added via Alembic migration. GitHub and local folder connectors unchanged.

## Rollback

Disable Google sources via feature flag `PKB_GOOGLE_CONNECTORS_ENABLED=false`. Canonical knowledge from prior syncs remains; sync stops.
