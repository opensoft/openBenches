## Purpose

Keep Spec Kit changes independently reviewable and test the aggregate result before it reaches the target branch.

## ADDED Requirements

### Requirement: One task set per pull request

Spec Kit plans SHALL group related tasks into small, named sets, each with a verifiable outcome, explicit predecessors, and a safe intermediate landing state. Each implementation PR SHALL correspond to one task set.

#### Scenario: A story needs multiple increments

- **WHEN** a story needs changes that require separate review decisions
- **THEN** the task list declares separate sets without duplicating task IDs, and each PR carries the tests for its own behavior

### Requirement: Two independent validation stages

Every PR head SHALL pass fast checks and applicable review before enqueue. The combined merge candidate SHALL pass its integration check before landing. The pilot SHALL NOT change any OpenBenches release workflow.

#### Scenario: A stack member changes after review

- **WHEN** a push or restack changes a reviewed PR head
- **THEN** the previous fast check and exact-head review do not qualify the new head

#### Scenario: Fast checks pass but combined behavior is wrong

- **WHEN** the heavy check fails on the combined candidate
- **THEN** the pilot does not advance the target branch
