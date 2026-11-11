## Purpose

Keep OpenBenches shared delivery instructions discoverable from clean source without workstation-local bootstrap state.

## ADDED Requirements

### Requirement: Self-contained discovery

A clean OpenBenches checkout SHALL contain matching Claude and Codex skill
assets and instruction pointers resolving entirely within the repository.

#### Scenario: Fresh checkout with no user-global delivery skill

- **WHEN** Claude or Codex discovers repository instructions
- **THEN** the shared delivery skill is available without local bootstrap copies

### Requirement: Preserve unrelated planning and authority

Adoption MUST preserve the existing active-plan block and MUST NOT grant new
queue eligibility, review waivers, merge authority or release authority.

#### Scenario: Delivery adoption is refreshed

- **WHEN** the delivery updater runs against the adopted checkout
- **THEN** the active-plan block remains unchanged and repeated updates are stable

### Requirement: Detect source adoption drift

Source checks SHALL reject a missing skill copy, divergent bytes or a broken
repository instruction pointer.

#### Scenario: One tracked copy changes independently

- **WHEN** only one agent's delivery asset differs from the packaged source
- **THEN** ordinary source CI fails without altering any efficiency-queue policy
