# Fix park/handoff integrity

Status: draft; implementation commissioned by Brett Heap on 2026-11-10

## Why

openMFA PR #2 exposed two inherited park defects: a mismatched code branch can be committed while another ref is pushed, and a selected-feature park can erase other parked records. Both undermine recoverable handoff.

## What Changes

- Preflight repository identity and expected checked-out branch for every leg before any leg commit.
- Treat explicit feature selection as a partial manifest update, preserving unselected records from the current file and through the existing Git rebase/refusal path on push retry.
- Add isolated regression fixtures and carry the tested shared-source correction into the draft openMFA tooling PR.
- Address the fresh consumer review finding: validate origin before accepting an existing resume worktree, preserving already-resumed idempotence and refusing unverified or moved remote branches.

## Capabilities

### New Capabilities
- `park-handoff-integrity`: truthful branch-bound parking and lossless selected-feature updates.

### Modified Capabilities
None; this formalizes the existing refusal/preservation intent without changing permission or workspace schema.

## Impact

Shared bash park/resume tooling, its workspace writer and fixtures. No shape pin, installer activation, live workspace manifest, queue/ruleset, release or public schema change. Follow the current constitution: three task sets and three ordered PRs after the fresh review finding. Existing Mergify pilot allowlists do not include these source paths; no queue admission is inferred.

Implementation handoff: [feature 177](../../../specs/177-park-handoff-safety/plan.md). New source proposals remain draft; the commission is not an invented ratification.
