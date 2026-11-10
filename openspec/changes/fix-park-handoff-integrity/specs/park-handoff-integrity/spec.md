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
