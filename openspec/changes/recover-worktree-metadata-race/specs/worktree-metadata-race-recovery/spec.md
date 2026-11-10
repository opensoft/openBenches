# Spec Delta

## Purpose

Keep concurrent feature creation reliable when Git briefly loses a worktree lock
marker, while retaining strict discovery errors and candidate authentication.

## ADDED Requirements

### Requirement: Bounded fresh snapshot recovery
PowerShell worktree discovery SHALL retry only Git exit 128 with the exact
missing worktree locked-marker diagnostic, for at most three attempts per
porcelain format, with 100ms between retries. Failed output MUST be discarded.

#### Scenario: Marker vanishes during enumeration
- **WHEN** a snapshot fails with the known missing locked-marker error and a later bounded attempt succeeds
- **THEN** lookup uses only the fresh successful snapshot and retains normal candidate validation

#### Scenario: Persistent or unrelated failure
- **WHEN** all attempts fail or Git reports another error
- **THEN** discovery throws without returning an empty or fabricated successful result

### Requirement: Preserve strict worktree validation
Recovered snapshots SHALL retain existing parsing, ambiguity, scope and live
candidate authentication. Legacy format fallback MUST remain limited to exit 129.

#### Scenario: Bad recovery payload
- **WHEN** a retry succeeds with malformed, ambiguous or uncorroborated candidate data
- **THEN** existing validation rejects it rather than treating retry as permission to proceed
