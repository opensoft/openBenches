# Design

Status: draft

## Scope

Repair the shared distribution first, with one implementation task list in feature 177. openMFA consumes exact tested source bytes with source commit/digests recorded; its earlier local core-creation/resume corrections remain explicit. Do not run park against the operator's real workspace to test this change.

## Decisions

All legs are preflighted before any commit. Resolve their real Git common directory and top-level path, compare with the expected leg repository, then require the recorded feature branch. Refuse mismatched, detached, foreign or unreadable state without committing either leg. Existing conflict/rebase checks and old-record retention remain intact. No branch switching or repair is automatic.

A subset park carries an internal selected-branch scope into the existing writer. Merge selected feature blocks against the manifest currently read by that writer, retaining other blocks and unknown fields. A repeated write uses its refreshed input rather than an old shell snapshot. On a concurrent push, the existing three-way rebase/refusal path preserves the unselected lines because they are absent from the local change; an injected peer-push fixture verifies this actual retry. No public manifest key or schema version changes. An ordinary full park retains its existing removal of gone features.

## Validation

Use disposable paired repositories and local bare remotes. Assert the refusal leaves both heads, indexes, dirty content and remote refs unchanged. For subset writes, assert open and no-longer-open unselected records survive, full-park behavior is retained, and a refreshed unselected record survives replay of a partial update. Run the full feature/compatibility/bootstrap suites through the declared bench and CI. Preserve Bash 3.2 and Git 2.34.1 compatibility.

## Delivery

SET-01 is branch/repository preflight with its tests and governance packet. SET-02 depends on SET-01 and changes partial manifest updates with its tests. Use gh-stack for authoring ordinary PR dependencies, without registered-stack or queue policy changes. Record local, CI, exact-head Codex review, upstream merge and downstream readback separately. Do not claim shared-main landing or fleet installation before it occurs.
