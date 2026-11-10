# Proposal

## Why

The helper candidate currently runs only three Ubuntu suites, while ordinary
helper edits also receive full Bash regression, Git 2.34.1, Bash 3.2 and
PowerShell Linux/Windows coverage. Establish parity before considering any
future per-PR optimization in #250.

## What Changes

- Share existing integration commands through local composite actions without
  changing ordinary job names, environments, triggers or required suites.
- Add five exact-candidate helper jobs and require every result in the heavy
  aggregate. Exercise them on configuration PRs as well.
- Freeze the pre-change command inventory in offline parity tests and verify
  missing/failed/cancelled/skipped helper results cannot pass.
- Keep ordinary checks full; no helper classifier, opt-in, live stack or merge.

## Capabilities

### New Capabilities

- `helper-stack-coverage`: complete candidate integration with ordinary CI retained.

### Modified Capabilities

None. Published capabilities do not include helper integration coverage.

## Impact

Non-release CI workflows, local actions, gate verification, tests and delivery
documentation. Queue configuration, application behavior, permissions, app
access and release files/tags remain unchanged. Spec Kit handoff:
`specs/176-helper-coverage-parity/`.
