# Feature Specification: Park handoff safety

**Feature Branch**: `177-park-handoff-safety`
**Created**: 2026-11-10
**Status**: Draft commissioned repair

## User Scenarios & Testing

### US1 — Trust the parked branch (P1)
An operator expects both legs of a parked feature to be recoverable from the branch named in its manifest.

Independent test: switch the code worktree to another branch or substitute a foreign repository; park must refuse before either leg commit/push, retaining dirty files and existing records.

### US2 — Park only the selected feature (P1)
An operator selecting one feature expects other parked features to remain recoverable, including ones absent from the current workstation.

Independent test: park two features, select one, and compare the unselected record. Repeat after a refreshed unselected record and for a gone worktree; full park keeps its existing reconciliation semantics.

### US3 — Resume only against verified origin (P1)

An existing worktree is not proof that the remote still matches the handoff. Verify origin before the existing-worktree shortcut, refuse moved/deleted/unavailable origins without resetting either leg, and retain idempotent handling of already-resumed WIP.

### US4 — Retry a failed handoff publication (P1)

A manifest committed locally but absent from origin is not a completed handoff. Retrying unchanged feature state must publish that pending commit or report failure again, without creating an empty commit.

## Requirements

- FR-001: Validate repository/worktree ownership and expected branch for every selected leg before any commit.
- FR-002: Refusal preserves heads, indexes, dirty content, remote refs and earlier manifest evidence.
- FR-003: Explicit selection updates only selected feature records using the writer's current file; the Git rebase/refusal path preserves concurrent unselected changes on push retry.
- FR-004: Full park retains its existing removal behavior, with unchanged manifest schema and delivery/authority boundaries.
- FR-005: Resume verifies origin before existing-worktree acceptance or WIP reset, while unchanged-origin repeat calls preserve restored work.
- FR-006: Park retries pending manifest publication independently of content changes and reports failed or exhausted publication as unsuccessful while retaining local evidence.

## Key Entities

Expected leg repository, actual Git worktree/common directory, expected branch, selected branch set, current workspace project block and per-feature record.

## Success Criteria

The two park defects and fresh resume finding refuse or preserve state as specified; full shared regression/compatibility checks pass; downstream source bytes and exact CI/review heads are recorded. No real workspace handoff or release is claimed from fixtures.
