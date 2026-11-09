## Why

The sandbox proved two-step CI for a synthetic stack. OpenBenches needs its own
CI before any repository access is granted to Mergify.

## What Changes

- Add one stable fast check for PR merge commits and one distinct integration
  check for authentic Mergify queue candidates.
- Prepare a dormant, manually entered queue for low-risk same-repository
  stacks of at most three PRs. Retain all existing checks.
- Track the rollout in 1.7 under #250. This change does not activate the queue,
  change app access or rulesets, qualify a release, or tag 1.6.2.

## Capabilities

### New Capabilities

- `openbenches-stack-ci`: Exact-candidate validation for an opt-in queue.

### Modified Capabilities

None.
