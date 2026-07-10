# ADR-009: Authentication and Authorization

**Status:** Accepted  
**Decision date:** 2026-07-10

## Decision

The MVP is a local single-user deployment but does not assume unrestricted implicit admin access. It includes a local user record and session, secure password hashing, HTTP-only session cookie, object-level `owner_id`, `visibility`, and `sensitivity`, a policy service before every search or retrieval, and a future service-account model.

## Consequences

Multi-user OIDC is outside the MVP, but provider interfaces and the authorization model are prepared for it. Post-retrieval filtering alone is insufficient; constraints should be included in queries whenever possible.
