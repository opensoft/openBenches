# Spec Delta

## Purpose

Deduplicate ordinary helper integration only when exact scoped evidence preserves
the complete five-environment candidate check and existing manual admission.

## ADDED Requirements

### Requirement: Conservative helper qualification
Ordinary helper workflows SHALL omit duplicate integration only for explicit
helper opt-in, current same-repository scoped inputs, and trusted-main proof.
Ordinary, mixed, uncertain, manual and unsupported events MUST retain full checks.

#### Scenario: Qualified author stack
- **WHEN** a non-draft ci/stack-helpers PR has Stack-CI: helper and an exact scoped chain rooted at current main
- **THEN** focused fast CI remains and duplicate ordinary integration can be omitted

#### Scenario: Uncertain inputs
- **WHEN** inputs are mixed, stale, missing, renamed, deleted, mode/type changed, untrusted or classification fails
- **THEN** all applicable ordinary integration jobs run

### Requirement: Exact duplicate event proof
Source pushes SHALL require an exact-head commit opt-in and scoped diff.
Queue events MUST prove the reviewed ordered batch; landing reuse MUST prove
successful exact-candidate jobs, unchanged policy, matching parents/trees and
GitHub merge records after completion. Delayed metadata MUST not exempt real changes.

#### Scenario: Post-merge and candidate metadata
- **WHEN** delayed metadata matches exact live candidate evidence or a verified merged scoped author head
- **THEN** only duplicate ordinary integration is omitted without queue admission

#### Scenario: Invalid historical proof
- **WHEN** any of five required jobs is absent, duplicate, failed, skipped, stale or incomplete
- **THEN** candidate/landing historical proof cannot omit ordinary integration

### Requirement: Preserve complete integration
Heavy helper CI SHALL retain all five jobs, shared command inventory, exact SHA
checks and fail-closed aggregate. CI selection MUST NOT alter admission or releases.

#### Scenario: Configuration qualification
- **WHEN** the config PR is opened against old trusted main
- **THEN** ordinary Bash and PowerShell checks and all five helper config jobs run in full
