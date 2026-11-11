# SET-04 evidence

Fresh Codex review of openMFA PR #2 at
819195462ea10a21dc535b380f538148e13252f7 found that an unchanged manifest
skipped publication of a pending commit from an earlier failed park.

Two disposable fixtures failed before correction. One kept origin unavailable
for a second unchanged park, then restored it and required the original
pending commit at origin with no empty commit. The other rejected all six
push attempts and required an unsuccessful result with the local commit
retained. Both previously returned success without a completed handoff.

The correction keeps commit creation conditional on changed content and moves
publication outside that condition. Exhausted push retries return failure.
All thirteen focused cases passed in 34.550 seconds after correction.
OpenSpec strict validation and diff whitespace validation passed.

The fixtures use temporary local repositories and bare origins only.
Published CI, exact-head Codex review and downstream consumer reconciliation
are separate evidence gates, recorded on the PRs and in the consumer's
provenance. No operator handoff, upstream merge, queue admission, shared image
installation, provider operation or release qualification is claimed.
