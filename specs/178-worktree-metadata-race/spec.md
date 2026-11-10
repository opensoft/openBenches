# Worktree metadata race recovery

Fix the disappearing locked-marker discovery failure seen in #250/#318 without
weakening fail-closed worktree parsing, candidate authentication or test coverage.
Use one SET-01 fix PR. Keep #316/#317 unqueued. Propose a fresh canary only after
qualification; no ruleset bypass, app access, release changes or 1.6.2 tag.
