# Proposal

## Why

The #250 helper efficiency canary failed in the unchanged PowerShell concurrency
suite: Git worktree discovery exited 128 while another creator removed a worktree
`locked` marker. A transient metadata read must not abort an otherwise safe creator.

## What Changes

- Add deterministic red/green reproduction of the recorded failure at the lookup boundary.
- Retry only the specific missing worktree locked-marker diagnostic, with a small
  fixed bound, fresh output each time and unchanged final validation.
- Preserve fail-closed behavior for persistent races, other errors, malformed
  records, ambiguous candidates and failed corroboration.
- Qualify a normal fix PR; propose but do not run a fresh helper efficiency canary.

## Capabilities

### New Capabilities

- `worktree-metadata-race-recovery`: bounded PowerShell discovery recovery without weakening worktree validation.

### Modified Capabilities

None.

## Impact

PowerShell create-new-feature lookup and its existing fixture suite; planning
records and #250 evidence. No job removals, broad error swallowing, app access,
ruleset bypass, release changes, tags, canary admission or automatic merge.
