# Proposal

## Why

Helper candidates now preserve all five integration environments, but ordinary
CI repeats them for each reviewed stack member and its queue/landing events.
Extend the proven conservative project deduplication contract to the helper queue.

## What Changes

- Select fast-only ordinary helper CI only from trusted-main, explicit helper
  opt-in and exact scoped Git/GitHub evidence; retain full checks on uncertainty.
- Reuse the project event-proof engine with an explicit helper policy, including
  all five exact-head jobs when reusing completed candidate evidence.
- Keep all five integration jobs and their shared commands unchanged in heavy CI.
- Add offline failure/metadata/landing fixtures and config qualification, not a live canary.

## Capabilities

### New Capabilities

- `helper-ci-efficiency`: conservative ordinary helper CI selection without weakening integration or admission.

### Modified Capabilities

None.

## Impact

Ordinary Bash/PowerShell workflows, CI selection policy/tests and delivery guidance.
No helper product changes, allowlist expansion, Mergify config, app access,
ruleset bypass, release workflow or tag changes. One Spec Kit task set in PR.
