## ADDED Requirements

### Requirement: Automated work uses the selected account
Automated Codex launchers MUST resolve the selected profile and its own credential home, and SHALL preserve that home for main and delegated work.

#### Scenario: Lane starts an automated review
- **WHEN** a lane with a selected profile launches a review
- **THEN** the selected Codex profile is used despite stale default-account environment state

### Requirement: Account selection fails closed
Automated execution MUST refuse missing selection, unknown profiles, missing auth and credential email mismatches before starting Codex. It MUST NOT silently use the default home or an inherited API key.

#### Scenario: Selection is absent or invalid
- **WHEN** selection or matching credentials are unavailable
- **THEN** execution fails with an actionable error and no provider call

### Requirement: Explicit valid account selection remains available
The launcher MUST allow any explicitly selected valid profile, including max-001, and preserve argument boundaries and exit status.

#### Scenario: Intended account is selected
- **WHEN** a valid explicit profile launches a task with quoted arguments
- **THEN** exactly that account receives the original arguments and its exit status is returned
