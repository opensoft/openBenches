# Proposal: Reduce duplicate CI for Wave-only stacks

## Why

Three Wave widget sync stacks passed the combined Ubuntu/macOS gate with
matching landed trees. Eligible Wave-only PRs still repeat unrelated Docker
bootstrap, credential-image, and lifecycle checks before entering that queue.

## What Changes

- Add trusted-main classification to the non-release Workstation Setup workflow.
- Keep focused fast CI for explicitly opted-in, same-repository Wave stacks
  with verified current heads/bases and only regular modifications to the three
  approved Wave files.
- Retain full workstation checks for all mixed, stale, ordinary, or uncertain
  inputs, including classification failures.
- Keep the queue's review receipts, full two-platform candidate checks, and
  aggregate merge gate unchanged. Do not run a live canary in this change.

## Capabilities

### New Capabilities

- `wave-stack-ci-efficiency`: fail-safe per-PR CI selection for Wave stacks.

### Modified Capabilities

None.

## Impact

Non-release Workstation Setup job selection, the stack policy helper and
its fixtures, and maintainer instructions. No Wave runtime, queue admission
rules, app access, rulesets, release workflows, release configuration, or tags
change. Spec Kit handoff: `specs/172-wave-ci-efficiency/`.
