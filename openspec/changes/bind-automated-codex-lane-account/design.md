## Context
Named provider launchers already resolve profile metadata and isolate credentials. Generated reviews bypass them by invoking a Codex binary with no explicit account. Claude-selected accounts and Codex-selected accounts have independent registries.

## Goals / Non-Goals
Goals: bind automated review work and its children to the selected account; refuse missing or mismatched credentials before model execution; retain normal explicit account selection.
Non-goals: rotate credentials, ban an intentionally selected account, restart sessions, change Windows/Beta runtime separation, or attribute server-side bills.

## Decisions
- Add `codex-exec`, requiring CODEX_PROFILE_NAME or the launching lane's CLAUDE_PROFILE_NAME. Reuse codex-profile resolution rather than guessing account aliases or copying tokens.
- Add an offline `home` action to codex-profile. Claude run exports its selected name and resolved Codex home, replacing stale inherited state. An unavailable mapping gets a profile-specific unauthenticated path; guarded execution refuses it, while the Claude session remains usable.
- Automated execution validates the selected auth file's email after existing credential synchronization, forces ChatGPT/file auth, and removes inherited API-key/access-token overrides. Missing or mismatched identities fail closed. Explicit selection of max-001 remains valid.
- Patch observed host-local generated launchers to call codex-exec, and route the shared adapter through it. Preserve prompt checks, report paths and argument vectors.

## Risks / Trade-offs
- Existing sessions do not gain new environment variables: the guarded entry point can still resolve their CLAUDE_PROFILE_NAME. No process is restarted.
- Raw binaries can deliberately bypass the entry point: inherited CODEX_HOME protects newly launched lanes; observed direct scripts are patched separately.
- Decoded email claims establish local configured identity, not token validity or billing: Codex performs authentication and refresh normally.

## Migration Plan
Run offline fake-provider tests, install the tested shared entry points and merge only the account-binding hunk into the active Claude launcher. Back up and patch generated launch scripts reversibly. Do not modify credentials or running processes. Revert installed paths and backed-up script contents to roll back.

## Open Questions
None for the authorized scope.
