# Proposal: Project-only stacked CI efficiency

## Why

The Wave canary qualified fast-only PR checks with a complete metadata
lifecycle audit. Project component CI also triggers on source, candidate,
and landing pushes, so PR-only suppression would leave duplicate integration.

## What Changes

- Extend trusted scope checks to project PRs and already-merged metadata.
- Deduplicate author pushes only with head-bound opt-in and verified Git scope.
- Deduplicate queue pushes only after exact candidate admission verification.
- Deduplicate landing pushes only when the full landed prefix matches a
  successful project candidate and the original approval receipts.
- Preserve component coverage on the combined candidate; keep full fallback
  for every uncertain case. No live canary in this change.

## Capabilities

### New Capabilities

- `project-stack-ci-efficiency`: scoped PR and push selection with verified batch evidence.

### Modified Capabilities

None.

## Impact

Non-release project and stack workflows, policy helpers, tests, and docs.
Wave behavior, helper queues, app access, rulesets, release files and tags stay
unchanged. Spec Kit handoff: `specs/174-project-ci-efficiency/`.
