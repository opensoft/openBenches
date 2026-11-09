# Feature Specification: Shared helper stack pilot

**Feature Branch**: `168-shared-helper-pilot`

**Created**: 2026-11-09

**Status**: Draft

**Input**: Widen the docs-only canary to one non-release shared helper after the
sandbox failure-and-recovery replay passes.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Pilot a small shared-helper stack (Priority: P1)

A maintainer can admit two or three reviewed changes to the last-worktree
helper and its regression suite without enabling the queue for other work.

**Why this priority**: A green docs canary does not prove that shared code was tested.

**Independent Test**: Review a two-member helper stack and compare its approved
members, combined test result and landed tree.

**Acceptance Scenarios**:

1. **Given** two eligible reviewed members, **When** the combined check passes,
   **Then** the stack can land through the existing protections.
2. **Given** an altered head, base or stack, **When** the candidate is checked,
   **Then** it is rejected until the maintainer revalidates the new inputs.

### Edge Cases

- A missing approval, unexpected member, mixed docs/code batch or unrelated
  path is not admitted to the helper pilot.
- If a stack only partly lands, stop and check the target before retrying.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Limit manual admission to the named helper and regression suite.
- **FR-002**: Require focused fast tests and applicable review on each member's
  exact head and immediate base.
- **FR-003**: Verify ordered membership and review inputs before one combined
  integration run on the exact candidate.
- **FR-004**: Leave the docs queue, existing checks, app access, release
  workflows and GitHub protections unchanged.

### Key Entities

- **Approval receipt**: The reviewed head, immediate base, and ordered PR numbers.
- **Candidate**: The exact combined revision and tree tested before landing.

## Success Criteria *(mandatory)*

- **SC-001**: One real two- or three-member helper stack lands after exactly
  one successful combined run on the unchanged candidate.
- **SC-002**: Missing or stale approval and incorrect batch membership each
  prevent a candidate from authorizing a merge.
- **SC-003**: The landed tree equals the tested tree, and no release checks or
  other existing checks were removed.

## Assumptions

The already-enabled queue is used by a maintainer, with one stack in flight.
The config PR does not itself authorize live admission.
