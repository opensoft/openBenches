# Proposal

## Why

The #250 server-side rollout is not yet part of the shared agent bootstrap.
Current Claude/Codex sessions therefore do not reliably plan or deliver small
task-set PRs using the tested gh-stack/Mergify contract.

## What Changes

- Add an opt-in 1.7 preview skill shared by Claude and Codex.
- Bootstrap repo-local skills, durable instruction pointers and additive
  planning/task-template rules without replacing handwritten content.
- Add explicit installation/verification of pinned gh-stack; never log in or
  upgrade an existing different version silently.
- Document activation, current CI limits and separate live acceptance gates.

## Capabilities

### New Capabilities

- `shared-task-set-delivery`: install and discover one bounded cross-agent delivery process.

### Modified Capabilities

None. Shared AI CLI image baselines and live recreation remain unchanged.

## Impact

Developer Tools bootstrap, one portable skill, packaged skill assets, offline
tests and documentation. Implementation: specs/179-shared-stack-workflow.
No ruleset, app, queue, CI eligibility, release workflow, VERSION or tag changes.
