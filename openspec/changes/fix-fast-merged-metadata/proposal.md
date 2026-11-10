# Proposal

## Why

The helper efficiency canary landed correctly, but a delayed retarget event
referenced an old test merge and failed Fast CI after the PR had merged.

## What Changes

- Add a trusted-main preflight for edited events to already-merged scoped PRs.
- Reuse the existing same-head, same-repository and complete-file-scope proof.
- Keep exact merge-parent validation and all policy tests for other events.

## Capabilities

### New Capabilities

- `fast-merged-metadata`: distinguish delayed merged metadata from real PR validation.

### Modified Capabilities

None.

## Impact

Only Stack PR fast CI, its policy helper and regression tests. No heavy-job,
release, app-access, ruleset or queue changes. Implementation: Spec Kit 179.
