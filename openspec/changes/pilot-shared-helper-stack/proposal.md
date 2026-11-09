# Proposal: Pilot shared-helper stack CI

## Why

The docs canary proved Mergify can test and land an ordered stack under the
current GitHub rules. The next step needs focused code verification and evidence
that the queue candidate is the exact stack a maintainer approved.

## What Changes

- Add a manual-only lane for one shared worktree helper and its regression test.
- Verify the current reviewed head, immediate base and ordered batch before
  running the existing combined integration checks.
- Preserve the docs queue, normal merge path, and all existing release gates.

## Capabilities

### New Capabilities

- `shared-helper-stack-pilot`: narrow admission and combined verification for the
  first non-release code stack.

### Modified Capabilities

None.

## Impact

The Mergify queue config, stack CI guard and non-release candidate workflow
gain an opt-in path. The helper itself, GitHub app access, rulesets and releases
do not change. Implementation: `specs/168-shared-helper-pilot/`.
