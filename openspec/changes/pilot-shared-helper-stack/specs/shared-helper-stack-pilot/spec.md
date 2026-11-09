# Shared helper stack pilot

## Purpose

Verify that one tightly scoped code stack can use the two-step merge process
without weakening the admission, review or release boundaries.

## ADDED Requirements

### Requirement: Admit only the reviewed helper stack

The helper pilot SHALL be manual-only, accept two or three ordered same-repository
PRs, and cover only the shared last-worktree helper and its regression suite.
Each member SHALL pass focused fast CI and have approval for its exact head,
immediate base and ordered stack before the candidate is eligible to land.

#### Scenario: Review or membership is stale

- **WHEN** a candidate contains an unapproved revision, base, or member
- **THEN** the candidate fails verification and does not authorize a merge

### Requirement: Test the combined candidate

The pilot SHALL run the existing non-release integration suite on the exact
Mergify candidate. It SHALL leave all existing checks, app access, branch
protections and release workflows unchanged.

#### Scenario: A reviewed helper stack passes integration

- **WHEN** the candidate contains the exact approved stack and integration passes
- **THEN** the maintainer can compare the tested tree with the landed tree
