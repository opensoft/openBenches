# Feature Specification: Shared Opensoft Codex projects

**Feature Branch**: `171-shared-codex-projects`
**Created**: 2026-11-10
**Status**: Approved for implementation by the user's request

## User Scenarios & Testing

### User Story 1 - Preserve organization during profile rotation (P1)

An Opensoft user can launch with another login and retain the same local project set and chat grouping.

**Independent Test**: Seed one account, prepare another, add/rename/remove a project and move or ungroup a chat, then prepare the first account again. All shared changes match and unrelated settings remain intact.

### User Story 2 - Separate desktop runtimes (P1)

Windows regular Codex and Beta/WSL keep independent project catalogs.

**Independent Test**: Attempt to use a catalog with the other runtime or another home. It refuses without writes. Launch selection targets only the explicit package.

### User Story 3 - Recover the current account (P1)

Restore the preserved project set to the currently selected Opensoft account with backups.

**Independent Test**: Inspect the app project and thread APIs after restoration; existing project IDs, names, and membership are present.

### Edge Cases

Unknown identities; malformed state; cloud-backed records; projectless chats; stale inactive copies; concurrent writers; repeated synchronization; removed projects; wrong package paths; active desktop processes.

## Requirements

- FR-001: Share native local projects, order, appearance, and memberships only among explicitly enrolled Opensoft identities.
- FR-002: Capture additions, renames, deletion, regrouping, and explicit projectless state without stale resurrection.
- FR-003: Preserve credentials, cloud ownership, all unrelated preferences, and other families.
- FR-004: Reject runtime/home mismatch and live-owned state; back up changed files and replace atomically after checking input freshness.
- FR-005: Provide workBenches desktop preparation/launch tooling and a reversible current-account restoration.

## Success Criteria

- SC-001: All shared project IDs and saved local memberships match across two synchronized profiles.
- SC-002: Repeated synchronization with no edits changes no files.
- SC-003: Every cross-runtime, unknown-identity, and concurrent-write fixture refuses without losing input.
- SC-004: Restored current-account projects are visible through the app API.

## Assumptions

Local project sharing is authorized for the Opensoft family. Normal desktop exit/relaunch is the synchronization boundary; in-app switching cannot invoke an external helper by itself. The Windows and Beta/WSL package configurations must remain independent.
