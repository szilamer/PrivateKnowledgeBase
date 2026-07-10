# Source Connection UI — Specification Supplement

**Version:** 0.1  
**Status:** Draft — implementation input for Phase 7  
**Related documents:**

- `docs/03-functional-specification.md`
- `docs/08-ai-development-contract.md`
- `docs/adr/ADR-008-frontend.md`
- `docs/13-personal-source-connectors-supplement.md`

## 1. Purpose

Define an **intuitive, non-technical UI** for connecting and managing personal data sources. The user MUST complete source setup without:

- editing `docker-compose.yml`
- knowing container paths
- constructing REST JSON manually
- reading operator documentation

Target user: single technical owner who manages multiple projects and expects consumer-grade setup flows (comparable to connecting Google account in Notion, Obsidian Sync, or Raycast).

## 2. Design principles

| Principle | Requirement |
|---|---|
| **Plain language** | Use „Mappa”, „Google Drive”, „Email”, „Naptár” — not „connector”, „mount”, „sync run” in primary UI |
| **Progressive disclosure** | Simple defaults first; advanced filters hidden behind „Több beállítás” |
| **Immediate feedback** | Every action shows success, progress, or actionable error |
| **Safe defaults** | Read-only access, sensible horizons (12 months email, 90 days future calendar) |
| **Reversibility** | Disconnect, pause, and re-sync without data loss on source side |
| **One home** | All source management lives under `/sources` — not scattered across settings |

## 3. Information architecture

```text
/sources                    → Overview (cards + status)
/sources/connect            → Choose source type (wizard entry)
/sources/connect/local      → Local folder wizard
/sources/connect/google     → Google account + pick Drive/Gmail/Calendar
/sources/{id}               → Source detail (status, history, settings)
/sources/{id}/sync-runs     → Run log (optional sub-view)
```

Replace the current MVP form (name + raw path only) with this structure. Existing API endpoints remain; UI becomes a guided layer.

## 4. Primary screen: Sources overview

### 4.1 Layout

**Header:** „Forrásaim” + primary button **„Forrás hozzáadása”**

**Connected accounts strip** (if Google connected):

- Google account avatar + email
- Status: „Csatlakoztatva” / „Újra bejelentkezés szükséges”
- Action: „Kapcsolat bontása”

**Source cards** (one per registered source):

Each card shows:

| Element | Content |
|---|---|
| Icon + name | e.g. 📁 Projektek, ☁️ Munka Drive, ✉️ Fontos emailek |
| Type label | Helyi mappa / Google Drive / Gmail / Google Naptár |
| Status pill | Aktív · Szinkronizálás… · Hiba · Szüneteltetve |
| Last sync | Relatív idő („12 perce”) |
| Stats | „128 fájl feldolgozva” / „3 hiba” |
| Actions | „Szinkronizálás most”, „Beállítások”, „Szüneteltetés” |

**Empty state:**

> Még nincs csatlakoztatott forrás. Add meg, honnan gyűjtse a rendszer a tudásodat — mappák, Drive, email vagy naptár.

CTA: **„Első forrás hozzáadása”**

### 4.2 Processing feedback

When sync is running, card shows determinate or indeterminate progress:

- „Felfedezés…” → „Feldolgozás (42/128)…” → „Kész”
- Link: „Részletek” opens run log with correlation ID (advanced)

## 5. Add source wizard

### 5.1 Step 0 — Choose type

Four large tiles:

| Tile | Subtitle |
|---|---|
| **Helyi mappa** | Fájlok a gépeden |
| **Google Drive** | Mappák a Drive-odban |
| **Email** | Gmail fontos levelek |
| **Naptár** | Google Naptár események |

Each tile one click → type-specific wizard.

### 5.2 Local folder wizard

**Step 1 — Name**

- Input: „Megjelenő név” (default: folder basename)
- Helper: „Ezt a nevet látod a forráslistában.”

**Step 2 — Choose folders**

- **Primary:** embedded **folder browser** backed by `GET /api/v1/sources/local/browse`
- Breadcrumb navigation (`~` → `Projects` → …) and folder list; user opens subfolders by click
- **„Ezen a mappán kiválasztása”** adds the current directory to the selection
- Support **multiple folders** per source; selected paths shown as removable chips
- **Secondary (collapsed):** „Több beállítás — útvonal kézi megadása” for power users only
- Optional future enhancement: native `showDirectoryPicker()` where the browser supports it
- Validation: path exists, readable, not system directory

**Step 3 — File types**

- Checkboxes (default on): Markdown, Szöveg, PDF
- Collapsed advanced: kizárt mappák (`node_modules`, `.git` pre-filled)

**Step 4 — Confirm**

- Summary card
- Toggle: „Szinkronizálás azonnal” (default on)
- Button: **„Forrás hozzáadása”**

**Error examples (human-readable):**

- „A mappa nem található: ~/Projektek. Ellenőrizd az elérési utat.”
- „Nincs olvasási jogosultság. Adj hozzáférést a Cursor/Docker számára a macOS Privacy beállításokban.” (link to help)

### 5.3 Google wizard (Drive, Gmail, Calendar)

**Step 1 — Connect Google**

If no account connected:

- Explanation: „Csak olvasási hozzáférés. A rendszer nem módosítja a fájljaidat vagy leveleidet.”
- Button: **„Bejelentkezés Google-lel”**
- OAuth popup/redirect

If already connected: skip to Step 2.

**Step 2 — What to connect**

Checkbox list (multi-select):

- [ ] Google Drive mappák
- [ ] Gmail
- [ ] Google Naptár

User may select one or more in a single wizard session.

**Step 3a — Drive (if selected)**

- Embedded folder browser (Drive API)
- Breadcrumb navigation
- Multi-select folders
- Option: „Google Dokumentumok is” (default on)

**Step 3b — Gmail (if selected)**

- Preset chips:
  - „Fontos levelek (ajánlott)”
  - „Bejövő, elmúlt 12 hónap”
  - „Egyéni szűrés”
- Custom query field hidden unless „Egyéni”
- Toggle: „Mellékletek (.pdf, .txt, .md)” (default on)

**Step 3c — Calendar (if selected)**

- Calendar checklist (primary + named calendars)
- Horizon sliders:
  - Múlt: 30 / 90 / 365 nap (default 365)
  - Jövő: 30 / 90 nap (default 90)

**Step 4 — Name and confirm**

- Default names suggested per type
- „Szinkronizálás azonnal” toggle
- **„Forrás hozzáadása”**

### 5.4 Success state

Confetti-free, clear confirmation:

> ✓ **Projektek** hozzáadva. A szinkronizálás elindult — kb. 1–3 perc múlva megjelennek a javaslatok.

Actions:

- „Javaslatok megtekintése” → `/proposals`
- „További forrás hozzáadása”
- „Vissza a forrásokhoz”

## 6. Source detail screen

Route: `/sources/{id}`

**Sections:**

1. **Áttekintés** — type, status, last sync, next scheduled sync
2. **Beállítások** — edit name, pause/resume, scopes (folders, query, calendars)
3. **Szinkronizálási előzmények** — table: idő, állapot, feldolgozott, hiba
4. **Hibák** — actionable list (“Gmail token lejárt → Újracsatlakozás”)
5. **Veszélyzóna** — Szüneteltetés, Forrás eltávolítása (with impact preview per FR-SRC-004)

**Impact preview copy (remove source):**

> A forrás leáll, de a már jóváhagyott tudás megmarad. 48 jóváhagyott állítás származik ebből a forrásból.

## 7. Functional requirements (UI)

### FR-UI-SRC-001 Source hub

A single `/sources` area lists all source types with consistent status presentation.

**Acceptance:** User identifies failing Gmail connector within 5 seconds on overview screen.

### FR-UI-SRC-002 Add-source wizard

A guided wizard exists for each of the four personal source types defined in doc 13.

**Acceptance:** User adds a local folder using only picker UI — no typing of `~/` paths required (picker preferred; manual path optional in advanced).

### FR-UI-SRC-003 Google OAuth UX

Google connection uses clear read-only messaging and shows account status on overview.

**Acceptance:** Expired token shows „Újra bejelentkezés szükséges” with one-click reconnect.

### FR-UI-SRC-004 Human-readable errors

API `code` values map to localized user messages; raw JSON never shown to user.

**Acceptance:** Drive quota error displays remediation steps, not stack trace.

### FR-UI-SRC-005 Config file parity

Every setting available in `config/sources.yaml` is editable in UI and vice versa.

**Acceptance:** Edit Gmail query in UI → exported config matches; manual YAML edit reflected in UI after reload.

### FR-UI-SRC-006 Accessibility

Wizard is keyboard-navigable, screens have landmarks, status pills have text labels not color-only.

**Acceptance:** WCAG 2.1 AA checklist pass for `/sources/connect` flow.

### FR-UI-SRC-007 Localization

Primary UI language: **Hungarian** for labels and helper text. Error codes and API remain English.

**Acceptance:** All wizard steps display Hungarian copy per table in section 5.

## 8. Frontend technical notes

### 8.1 Stack (per ADR-008)

- Next.js App Router, TypeScript
- Server components for overview lists; client components for wizards and OAuth redirect handling
- API client in `apps/web/src/lib/sources/` (split from legacy `api.ts`)

### 8.2 Key components

| Component | Responsibility |
|---|---|
| `SourceCard` | Status, actions, progress |
| `AddSourceWizard` | Multi-step state machine |
| `LocalFolderPicker` | Native path selection bridge |
| `GoogleConnectButton` | OAuth initiation |
| `DriveFolderBrowser` | Folder tree + selection |
| `GmailScopePresets` | Query presets |
| `CalendarPicker` | Calendar multi-select |
| `SyncRunTimeline` | History visualization |
| `ErrorBanner` | Mapped error display |

### 8.3 Server vs client API URL

Fix Docker SSR issue: server-side fetches use `API_INTERNAL_URL=http://api:8000`; browser fetches use `NEXT_PUBLIC_API_URL=http://localhost:8000`. Document in `.env.example`.

### 8.4 State management

Wizard state in React; persisted on final submit to API (`PUT /sources/config` or `POST /sources/{type}`). Optimistic UI on sync trigger with polling `GET /sync-runs/{id}`.

## 9. Wireframe references (low-fidelity)

### Sources overview

```text
┌─────────────────────────────────────────────────────────┐
│ Forrásaim                          [+ Forrás hozzáadása]│
├─────────────────────────────────────────────────────────┤
│ Google: user@gmail.com  ● Csatlakoztatva                 │
├─────────────────────────────────────────────────────────┤
│ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐      │
│ │ 📁 Projektek │ │ ☁️ Munka     │ │ ✉️ Fontos    │      │
│ │ Helyi mappa  │ │ Drive        │ │ emailek      │      │
│ │ ● Aktív      │ │ ⟳ Sync...    │ │ ● Aktív      │      │
│ │ 12 perce     │ │ 42/128       │ │ tegnap       │      │
│ │[Sync][⚙️]    │ │[Sync][⚙️]    │ │[Sync][⚙️]    │      │
│ └──────────────┘ └──────────────┘ └──────────────┘      │
└─────────────────────────────────────────────────────────┘
```

### Add source — type selection

```text
┌─────────────────────────────────────────────────────────┐
│ ← Vissza          Milyen forrást adsz hozzá?            │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐                       │
│  │ 📁 Helyi    │  │ ☁️ Google   │                       │
│  │   mappa     │  │   Drive     │                       │
│  └─────────────┘  └─────────────┘                       │
│  ┌─────────────┐  ┌─────────────┐                       │
│  │ ✉️ Email    │  │ 📅 Naptár   │                       │
│  │   (Gmail)   │  │  (Google)   │                       │
│  └─────────────┘  └─────────────┘                       │
└─────────────────────────────────────────────────────────┘
```

## 10. Implementation slices

| Slice | Deliverable |
|---|---|
| UI-7a | Redesigned `/sources` overview + cards + empty state |
| UI-7b | Local folder wizard with **API-backed folder browser** (browse + select; manual path advanced only) |
| UI-7c | Google OAuth + account strip |
| UI-7d | Drive folder browser step |
| UI-7e | Gmail preset step |
| UI-7f | Calendar picker step |
| UI-7g | Source detail + error mapping + impact preview |
| UI-7h | Hungarian copy pass + accessibility audit |

## 11. Acceptance criteria (UX)

1. A new user connects **one local folder and one Google service** in under 5 minutes without documentation.
2. Zero user-facing occurrences of „Docker”, „mount”, „container”, or „correlation ID” in primary flows.
3. Sync errors offer **one obvious next action** (retry, reconnect, check path).
4. Mobile viewport (375px) remains usable for overview and wizard steps.

## 12. Out of scope for UI-7

- Mobile native app
- Dark-mode redesign beyond existing theme tokens
- Bulk source import from CSV
- Admin multi-tenant source management
