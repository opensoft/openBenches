## Purpose

Make the proven task-set delivery process discoverable to Claude and Codex without changing repository or workstation authority boundaries.

## ADDED Requirements

### Requirement: Explicit cross-agent adoption

Bootstrap SHALL offer opt-in repository-local discovery of the same delivery
skill for Claude and Codex, preserve handwritten context, and be idempotent.

#### Scenario: Repository adopts the preview

- **WHEN** bootstrap is invoked with task-set delivery enabled
- **THEN** both agents receive the same skill and planning/task templates name one PR per task set

#### Scenario: Repository does not opt in

- **WHEN** bootstrap is invoked without delivery adoption
- **THEN** it does not add delivery instructions or install the delivery skill

### Requirement: Bounded tool installation

The pinned gh-stack tool SHALL be installed only by explicit request and a
different existing version MUST NOT be replaced automatically.

#### Scenario: Explicit installation with no extension

- **WHEN** the user requests stack tool installation and gh-stack is absent
- **THEN** bootstrap installs github/gh-stack pinned to v0.3.0 and verifies its version

### Requirement: Preserve delivery gates

The shared workflow MUST retain one PR per task set, current-head checks and
review, ordinary dependent PRs, and Mergify merging. It SHALL retain full CI
unless the target repository explicitly qualifies the complete stack scope.

#### Scenario: Unqualified current development project

- **WHEN** either agent plans a stack outside approved CI scope
- **THEN** it retains full checks and does not infer queue access or a review waiver
