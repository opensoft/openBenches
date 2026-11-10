# Fast CI merged metadata

Related: #250; openspec/changes/fix-fast-merged-metadata.

Recognize the stale retarget event seen on PR #322 only after trusted live proof
that its unchanged, same-repository scoped head has merged. Report metadata-only
handling, not tested-tree evidence. Every uncertain or real source event retains
the existing exact merge-parent validation and policy suites. No release,
ruleset, application access, queue or heavy-coverage changes.
