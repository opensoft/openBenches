# Design

## Context

The desktop global state stores active account globals at the root and inactive account globals under `electron-account-renderer-state-v1.inactive`. The owner is SHA-256 of the compact JSON pair `[userId, accountId]`. Login email and family metadata establish enrollment; directory names alone do not establish identity. The local SQLite project registry is intact and is not rebuilt.

## Goals / Non-Goals

Share native local project organization. Preserve account-specific renderer state, credentials, cloud projects, model settings, and runtime configuration. Do not patch the installed application or write live-owned state.

## Decisions

- A standard-library Python helper maintains a versioned, per-runtime Opensoft catalog and explicit account bindings. It strips cloud ownership fields from shared records and preserves them on each destination account.
- Bootstrap uses an explicitly selected, identity-verified account snapshot. Subsequently each enrolled snapshot is compared with its last prepared baseline. Only actual changes contribute, including edits saved before an in-app account rotation; unchanged stale copies cannot revive deletions. The active account wins simultaneous conflicting edits. New profiles receive the catalog without replacing it with an empty registry.
- Per-account project registrations, ordering, membership maps, projectless markers, and the local host migration mapping are shared. Unrelated account atoms and globals are untouched.
- A PowerShell desktop wrapper captures/prepares state only while the selected package is stopped, then launches that package. Windows resolves only `OpenAI.Codex`; Beta/WSL has an independent entry point and catalog. There is no implicit path conversion or WSL shutdown.
- Atomic replacement, exclusive synchronization lock, input digest comparison, original-file backups, and unchanged-content no-ops protect state. Only selected keys enter the catalog.

## Risks / Trade-offs

- The desktop keeps global state in memory. Offline writes require a normal app restart; raw in-app account switching alone cannot run external workBenches hooks. The wrapper is the supported synchronization boundary and this limitation must be stated.
- Undocumented desktop storage can evolve. Unknown format/schema or identity mismatch refuses; fixture coverage records the supported shape.
- Existing duplicate project roots are retained with stable IDs rather than merged speculatively.

## Migration Plan

Validate fixtures in the declared bench and native Windows wrapper syntax. Back up current Windows state, enroll verified Opensoft identities, seed from the preserved max-002 snapshot, prepare team-004 and other enrolled snapshots, then relaunch and check the app project and thread APIs. Install the wrapper and helper as host-local workBenches tools. Rollback restores the pre-change global-state backup while the selected app is stopped. Beta/WSL support is tested separately and never seeded from Windows.
