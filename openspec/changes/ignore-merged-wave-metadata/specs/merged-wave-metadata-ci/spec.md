# Merged Wave metadata CI

## Purpose

Avoid repeated workstation integration jobs for verified post-merge Wave
metadata events without suppressing coverage of open or uncertain PRs.

## ADDED Requirements

### Requirement: Verified merged metadata may omit duplicate jobs

The trusted classifier SHALL expose a separate positive result only for edited
metadata on an opted-in same-repository Wave PR that live GitHub readback
confirms is merged into main at the event head.

#### Scenario: Edited event processed after merge

- **WHEN** a queued metadata edit names the same head as a currently merged Wave PR
- **THEN** redundant workstation jobs are omitted without claiming open-PR eligibility

### Requirement: Uncertain and open inputs retain existing policy

Open PRs SHALL remain subject to the existing Wave-only or full-check policy.
Missing, mismatched, closed-unmerged, unreadable, or non-metadata inputs SHALL
NOT receive the merged-metadata exemption.

#### Scenario: Open PR with real changes

- **WHEN** a PR remains open or its head differs from the event
- **THEN** the new exemption cannot omit its checks

#### Scenario: API read is unavailable

- **WHEN** merge confirmation cannot be read or validated
- **THEN** the workflow retains full fallback
