## ADDED Requirements

### Requirement: Preflight all parked leg identities
The shared park command SHALL require every selected feature leg to be the expected repository's worktree and to have the recorded feature branch checked out before committing any leg. It SHALL refuse mismatches without automatic checkout or commit, while retaining previously recorded handoff evidence.

#### Scenario: Code leg switched branch
- WHEN the spec leg remains on the feature branch and the code leg has switched branches
- THEN park refuses before either leg is committed or pushed.

#### Scenario: Foreign repository at the code path
- WHEN a code path contains another repository
- THEN park refuses without writing that repository or claiming it was pushed.

### Requirement: Preserve unselected parked records
A park invocation with explicit feature selection SHALL update only the selected feature records and SHALL preserve all unselected feature records from the current manifest, including records whose worktrees are no longer open. It SHALL preserve newer unselected values when a write is retried after workspace synchronization.

#### Scenario: Park one of two recorded features
- WHEN a workspace already records two features and park selects one
- THEN the other feature's record remains available for resume.

#### Scenario: Retry after an unselected record changes
- WHEN a selected update is reapplied to a refreshed workspace manifest
- THEN the refreshed unselected record is retained rather than replaced from an earlier snapshot.

### Requirement: Keep full-park and delivery boundaries
A full park without explicit selection SHALL retain its existing reconciliation behavior for gone features. The repair SHALL NOT change branch protection, merge queues, public manifest schema, live workspace data or release qualification.

#### Scenario: Full reconciliation
- WHEN a full park no longer discovers a previously recorded feature
- THEN the existing full-park removal behavior remains in effect.

### Requirement: Verify origin before every active resume path
Resume SHALL verify that each origin branch is still at its recorded parked commit before accepting an existing worktree or resetting any parked WIP. Failed origin verification SHALL refuse without trusting a cached ref. An unchanged origin SHALL retain safe idempotent handling of already-resumed WIP.

#### Scenario: Existing worktrees and a moved origin
- WHEN either origin branch has moved after parking while both worktrees still exist
- THEN resume refuses without resetting either leg or changing its dirty state.

#### Scenario: Existing worktrees with unavailable origin
- WHEN origin cannot be verified
- THEN resume refuses without using the old tracking ref.

#### Scenario: Already-resumed work and unchanged origin
- WHEN the same workspace resumes twice against the unchanged parked remote
- THEN the second call preserves the already-restored work without another reset.

### Requirement: Retry pending handoff publication
Park SHALL retry publication of an existing pending workspace-manifest commit even when the writer reports unchanged content. Failed publication SHALL return unsuccessful without discarding that commit. Exhausted race retries SHALL NOT be reported as success.

#### Scenario: Retry after origin access returns
- WHEN the previous manifest commit could not be pushed and the feature state has not changed
- THEN a retry publishes that pending commit without creating an empty commit.

#### Scenario: Publication still fails
- WHEN origin is still unavailable or all push retries are rejected
- THEN park refuses success and retains the local manifest commit.

### Requirement: Read the refreshed receiving manifest
An active resume SHALL synchronize a configured workspace origin before loading its manifest. It SHALL refuse unavailable origin and unsafe synchronization without creating or resetting feature worktrees. It SHALL preserve dirty content, abort conflicting rebases, and release its mutex on every exit. Dry-run SHALL NOT synchronize or lock the workspace.

#### Scenario: Clone predates a published handoff
- WHEN the receiving workspace clone has no copy of the latest parked feature
- THEN resume refreshes it and restores that published feature.

#### Scenario: Unsafe or unavailable synchronization
- WHEN refresh requires a rebase of dirty content, conflicts, or cannot reach origin
- THEN resume refuses, preserving the local workspace and feature heads.

#### Scenario: Dry-run on a stale clone
- WHEN a stale receiving clone is used with dry-run
- THEN its files, refs and lock state remain unchanged.

### Requirement: Publish the manifest without clobbering existing temporary paths
The writer SHALL exclusively create its temporary file, SHALL NOT follow or truncate a pre-existing temporary leaf, and SHALL preserve the existing manifest on refusal. It SHALL atomically replace the manifest only after a successful write and clean up only temporary files created by that invocation.

#### Scenario: Temporary path is a symlink
- WHEN the predictable manifest temporary path points to an unrelated file
- THEN park refuses publication without changing that target, the symlink or the existing manifest.

#### Scenario: Temporary path is an ordinary file
- WHEN an existing file occupies the temporary name
- THEN publication refuses without truncating or deleting that file.

#### Scenario: Publication directory or selector is a symlink
- WHEN a manifest directory component or active-feature selector points outside its intended checkout
- THEN publication refuses without changing any unrelated target.
