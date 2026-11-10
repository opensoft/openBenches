# Design

Status: draft

## Scope

Repair the shared distribution first, with one implementation task list in feature 177. openMFA consumes exact tested source bytes with source commit/digests recorded; its local core-creation correction remains explicit, while the shared resume correction supersedes the local resume patch. Do not run park against the operator's real workspace to test this change.

## Decisions

All legs are preflighted before any commit. Resolve their real Git common directory and top-level path, compare with the expected leg repository, then require the recorded feature branch. Refuse mismatched, detached, foreign or unreadable state without committing either leg. Existing conflict/rebase checks and old-record retention remain intact. No branch switching or repair is automatic.

A subset park carries an internal selected-branch scope into the existing writer. Merge selected feature blocks against the manifest currently read by that writer, retaining other blocks and unknown fields. A repeated write uses its refreshed input rather than an old shell snapshot. On a concurrent push, the existing three-way rebase/refusal path preserves the unselected lines because they are absent from the local change; an injected peer-push fixture verifies this actual retry. No public manifest key or schema version changes. An ordinary full park retains its existing removal of gone features.

## Validation

Use disposable paired repositories and local bare remotes. Assert the refusal leaves both heads, indexes, dirty content and remote refs unchanged. For subset writes, assert open and no-longer-open unselected records survive, full-park behavior is retained, and a refreshed unselected record survives replay of a partial update. Run the full feature/compatibility/bootstrap suites through the declared bench and CI. Preserve Bash 3.2 and Git 2.34.1 compatibility.

## Delivery

The fresh consumer review also reproduced a resume shortcut that accepts existing worktrees before verifying origin. SET-03 moves current-origin and divergence checks before that shortcut. A failed fetch refuses rather than using a stale tracking ref. The check still permits an unchanged origin with this workspace's already-uncommitted WIP, retaining existing idempotence and local-branch checks. All legs are checked before any WIP reset. Dry-run remains a no-write cached preview, not a fresh remote attestation.

SET-04 separates conditional manifest commit creation from publication. Even an unchanged writer result must retry a previously pending commit through the existing non-force push/rebase path. Publication failure, including exhausted retries, is unsuccessful and retains the local commit for another attempt. A restored origin must receive the original commit without requiring a new feature change or empty commit.

SET-05 refreshes a receiving workspace under the existing mutex before loading its manifest. Resume uses the shared synchronization helper in a strict mode: failed origin fetch refuses cached data, and any dirty content blocks a required rebase without automatic commits or stashing. The existing rebase-conflict abort is retained. The mutex releases on every exit, including before record temporaries exist. A workspace without origin retains local-only compatibility. Dry-run takes no lock and performs no fetch or synchronization.

SET-01 is branch/repository preflight with its tests and governance packet. SET-02 depends on SET-01 and changes partial manifest updates with its tests. Use gh-stack for authoring ordinary PR dependencies, without registered-stack or queue policy changes. Record local, CI, exact-head Codex review, upstream merge and downstream readback separately. Do not claim shared-main landing or fleet installation before it occurs.
