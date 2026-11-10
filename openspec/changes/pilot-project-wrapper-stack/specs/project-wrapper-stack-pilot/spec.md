# Project wrapper stack pilot

## Purpose

Verify cross-platform combined testing for a narrowly scoped checkout wrapper
without changing existing checks or repository protections.

## ADDED Requirements

### Requirement: Manual project stack admission

The queue SHALL admit only reviewed same-repository wrapper and fixture changes
on the dedicated branch namespace. Approval SHALL identify the exact head,
immediate base and ordered stack.

#### Scenario: Stale or out-of-scope input

- **WHEN** a proposed candidate has a stale receipt or mixes allowed and unrelated paths
- **THEN** it cannot authorize landing

### Requirement: Both platforms gate the candidate

One combined workflow SHALL run the fixture suite on Ubuntu and macOS and
require both results before it reports success. Config PRs SHALL run the same
matrix without posting a candidate merge check.

#### Scenario: A platform does not pass

- **WHEN** either platform fails, is cancelled, or is skipped for a project candidate
- **THEN** the aggregate merge check cannot succeed
