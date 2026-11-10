## Purpose

Prevent obsolete post-merge metadata events from falsely failing source validation while retaining checks for real changes.

## ADDED Requirements

### Requirement: Trusted proof before metadata-only success

Fast CI SHALL classify only edited events as metadata-only when trusted code
and live GitHub readback prove the same head of an opted-in helper, project or
Wave PR has merged into main and all changed files remain in that scope.

#### Scenario: Retarget event carries an obsolete merge

- **WHEN** the event base no longer matches its test merge but the same scoped head is now merged
- **THEN** Fast CI reports metadata-only handling without claiming to test that merge

### Requirement: Preserve validation on uncertainty

Fast CI MUST retain exact event checkout, parent validation and policy tests
for open, unmerged, changed-head, mixed-scope, non-edited or unverifiable events.

#### Scenario: An open PR is retargeted

- **WHEN** live readback still shows an open PR or readback fails
- **THEN** Fast CI retains source validation, including rejection of mismatched parents
