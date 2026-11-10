# Wave stack CI efficiency

## Purpose

Avoid redundant workstation integration work for explicitly qualified Wave
stacks while retaining conservative coverage for ordinary or uncertain inputs.

## ADDED Requirements

### Requirement: Explicit and narrow fast-only eligibility

The PR workflow SHALL omit the four redundant workstation jobs only when a
trusted policy verifies opt-in, the same-repository current dependency chain,
and exclusively regular content modifications to the three approved Wave files.

#### Scenario: Qualified Wave member

- **WHEN** the complete chain from current main to an opted-in member is eligible
- **THEN** it keeps focused fast CI and defers full Wave integration to the queue candidate

#### Scenario: Mixed or uncertain input

- **WHEN** any input is stale, mixed, ambiguous, untrusted, missing, or unreadable
- **THEN** all existing workstation integration jobs remain eligible to run

### Requirement: Existing acceptance gates remain

Classification SHALL NOT grant review, authorize admission, or replace the full
two-platform candidate check. Non-PR events SHALL retain full workstation CI.

#### Scenario: Manual, push, or release execution

- **WHEN** the workflow is triggered outside a pull request
- **THEN** the classifier cannot omit existing jobs

#### Scenario: Candidate does not pass

- **WHEN** a candidate fails verification or either platform does not succeed
- **THEN** the existing aggregate cannot authorize queue landing
