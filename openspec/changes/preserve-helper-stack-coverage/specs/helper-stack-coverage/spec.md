# Helper stack coverage

## Purpose

Preserve the complete existing integration coverage on combined helper stack
candidates before any future per-PR CI optimization can be considered.

## ADDED Requirements

### Requirement: Five complete integration environments

Helper candidates SHALL execute the full ordinary Ubuntu Bash regression,
Git 2.34.1 compatibility, Bash 3.2 compatibility, Ubuntu PowerShell regression,
and native Windows PowerShell state regression on the exact candidate SHA.

#### Scenario: Verified helper candidate

- **WHEN** the existing queue verifier accepts an exact helper batch
- **THEN** all five jobs run their preserved suites on that revision

### Requirement: Ordinary CI remains full

Ordinary workflow job identities, existing path triggers, environments and
suites SHALL remain intact. This phase SHALL NOT introduce skip classification.

#### Scenario: Ordinary PR or push

- **WHEN** an event matches an existing ordinary workflow trigger
- **THEN** its existing full integration jobs remain enabled

### Requirement: Complete aggregate evidence

The helper aggregate SHALL require success from every helper job. Config PRs
SHALL exercise all five jobs. Other existing candidate scopes SHALL retain
their original integration requirements without executing helper jobs.

#### Scenario: Incomplete helper result

- **WHEN** any required result is missing, failed, cancelled or skipped
- **THEN** the aggregate cannot pass
