# Share Opensoft local Codex projects

## Why

Switching Opensoft accounts hides the local project registry and chat grouping even though the shared conversation files and project database remain present. Account rotation must preserve the local work organization within each desktop runtime.

## What Changes

- Maintain a shared local project catalog and chat membership map for enrolled Opensoft identities.
- Integrate synchronization into workBenches desktop launch/switch tooling with backups and running-app protection.
- Restore the current Windows account from the explicitly selected preserved account snapshot.
- Keep Windows and Beta/WSL catalogs, homes, process selection, and configuration separate.

## Capabilities

### New Capabilities

- `shared-codex-projects`: Family-scoped local projects and chat grouping, with explicit identity enrollment and runtime isolation.

### Modified Capabilities

None.

## Impact

Desktop profile helpers, local catalog files, account-scoped project metadata, documentation, and fixture tests. No credential synchronization, cloud project ownership changes, app-bundle patching, or database reconstruction.

## Authority and handoff

Authorized by the user's request to implement sharing and restore this profile while separating Windows and Beta/WSL. Implementation tasks live only in `specs/171-shared-codex-projects/tasks.md`.
