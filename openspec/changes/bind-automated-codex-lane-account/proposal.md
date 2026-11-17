## Why
Automated review launchers invoke Codex directly without selecting the lane account, allowing the default subscription to pay for main and delegated work. The user explicitly authorized repairing account inheritance and refusing silent default-account fallback on 2026-11-17.

## What Changes
- Add a guarded automated Codex entry point that requires a selected profile and verifies its credential identity before execution.
- Bind child Codex work to the profile selected by the Claude lane launcher, overriding stale inherited account state.
- Route the shared CLI adapter and the observed generated review launchers through the guarded entry point.
- Refuse absent profiles, missing credentials and identity mismatches; preserve explicit selection of any valid account.

## Capabilities
### New Capabilities
- `automated-codex-account-binding`: Automatic work uses an explicitly selected account and cannot fall back to default credentials.
### Modified Capabilities
None.

## Impact
Shared profile launchers, base-image installation, CLI adapter and focused offline regression tests. Host-local review launchers receive a reversible installation patch. No token values, model requests, account changes or running-session restarts are required. Implementation is tracked only in specs/251-codex-lane-account/tasks.md.
