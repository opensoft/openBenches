# SET-05 evidence

Codex review of openMFA PR #2 at
7ab6ea004ea3df3a7437b9dbd6395a45dfaf0ca8 found that resume read a stale
receiving workspace without refreshing the published manifest.

Four new checks failed before correction: a clone predating park missed the
record; dirty and conflicting receiving workspaces were not diagnosed by a
refresh; unavailable workspace origin was accepted. The dry-run control
already left the stale clone unchanged.

Resume now refreshes before manifest loading under the existing workspace
mutex, using strict shared synchronization. Failed origin fetch refuses
cached data; dirty content blocks a required rebase; a conflicting rebase
aborts. No automatic commit or stash is used by this path. A no-origin local
workspace retains compatibility. Dry-run does not fetch, synchronize or lock.
The early trap and record cleanup both release the mutex.

All eighteen focused cases passed in 35.706 seconds after correction.
OpenSpec strict and diff whitespace validation passed. Published CI and
exact-head review remain separate evidence gates. SET-04 PR #313 at
0ac1aa4411669ebf78a62445b953a1d81b8180d4 passed all published CI and
exact-head Codex review without findings.

The consumer records exact source bytes/hashes, tests and CI/review evidence
separately. These fixtures use disposable local repositories only; they do not
perform an operator handoff, upstream merge, installation or release.
