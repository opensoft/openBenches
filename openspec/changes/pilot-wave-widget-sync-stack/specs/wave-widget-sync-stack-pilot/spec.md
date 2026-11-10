# Wave widget sync stack pilot

## Purpose

Qualify the Wave widget reconciler for narrowly scoped, two-platform stacked
delivery without opening Wave or touching live workstation settings.

## ADDED Requirements

### Requirement: Manual Wave widget sync admission

The queue SHALL admit only manually submitted same-repository Wave widget
sync stacks whose receipts identify each reviewed head, immediate base, and
the exact ordered stack. Only the two widget sync scripts and their fixture
suite SHALL be eligible.

#### Scenario: Stale, different, or mixed inputs

- **WHEN** a receipt is stale or names different members, or a PR changes an ineligible file
- **THEN** the candidate cannot authorize landing

### Requirement: One combined two-platform gate

Verified candidates SHALL run the complete widget fixture suite in one
workflow on Ubuntu and native macOS. The stable candidate check SHALL require
both platforms to succeed. The config PR SHALL exercise both platforms
without publishing the candidate check.

#### Scenario: A platform does not pass

- **WHEN** either platform fails, is cancelled, or is skipped for a Wave widget candidate
- **THEN** the candidate check does not succeed
