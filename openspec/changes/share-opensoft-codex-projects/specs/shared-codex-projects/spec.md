# Shared local Codex projects

## Purpose

Preserve a company's local project catalog and conversation grouping when its users rotate login profiles, without crossing desktop runtime or account ownership boundaries.

## ADDED Requirements

### Requirement: Family project organization
Enrolled Opensoft profiles SHALL share local project registrations and chat grouping within a runtime. Credentials, cloud project ownership, and unrelated account preferences MUST remain separate.

#### Scenario: Rotate Opensoft profile
- **WHEN** an enrolled Opensoft account is prepared for desktop launch
- **THEN** it has the latest shared local projects and grouping, including retained project identities
- **AND** its unrelated account state is preserved

### Requirement: Runtime separation
Windows and Beta/WSL SHALL use distinct catalog files, homes, and process selection. A catalog from another runtime MUST be rejected before mutation.

#### Scenario: Wrong runtime catalog
- **WHEN** Windows sharing is supplied a Beta/WSL catalog or home
- **THEN** it refuses without modifying either runtime

### Requirement: Reversible, race-safe restoration
Restoration MUST preserve original state backups, reject changed input, and avoid editing state owned by a running desktop process.

#### Scenario: Active desktop
- **WHEN** the desktop is running during an offline restore
- **THEN** restoration refuses until the desktop has exited cleanly

### Requirement: Changes persist across profiles
Project additions, renames, deletion, explicit projectless chats, and membership changes SHALL propagate from enrolled accounts' actual changes since their last preparation, including changes saved in inactive accounts, without reviving unchanged stale copies. The active account SHALL win simultaneous conflicting edits.

#### Scenario: Remove a shared project
- **WHEN** a synchronized account removes a project and its state is captured
- **THEN** another enrolled account no longer lists that project
- **AND** stale inactive snapshots do not recreate it
