# Release qualification waivers

## Purpose

Represent explicitly approved, narrowly scoped release qualification exceptions
without disguising missing test execution as successful acceptance evidence.

## ADDED Requirements

### Requirement: Reviewed exact-version external exceptions

The release gate SHALL accept only reviewed manifest exceptions identifying an
existing external suite, one exact stable version, reason, approval and restoration
condition. Invalid or duplicate entries MUST be rejected. Hosted suites MUST NOT
be waived. Only arch-native on exact version 1.6.2 is approved by this change.

#### Scenario: Approved Arch exception
- **WHEN** full qualification is planned for exact stable VERSION 1.6.2
- **THEN** arch-native is not required and all twelve hosted and four other
  applicable external suites remain required.

#### Scenario: Automatic expiry
- **WHEN** qualification is planned for 1.6.1, 1.6.3, 1.7.0 or a 1.6.2 prerelease
- **THEN** arch-native remains required with its existing cases and cleanup.

### Requirement: Transparent qualification reporting

Plans, validation summaries and published release notes/reports MUST identify
applicable exceptions as waived-not-executed, separately from passed suites.
Publication MUST recompute applicable waivers from trusted source-bound policy.

#### Scenario: Missing other live evidence
- **WHEN** Arch is waived but any remaining required native/live evidence is absent
- **THEN** publication is refused and the exception remains explicitly disclosed.

#### Scenario: Invalid publication summary
- **WHEN** a supplied summary omits or changes an applicable waiver
- **THEN** publication refuses it even if the remaining suite reports pass.
