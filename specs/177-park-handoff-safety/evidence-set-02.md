# SET-02 evidence

Status: local focused validation passed; combined CI/review pending

Parent SET-01: openBenches PR #310, commit
0fb4061a5a2357d81735a431cbf8cb206e55a8a2. Its published checks passed,
including Bash 3.2, Git 2.34.1 and PowerShell regression matrices; Codex
completed review on that exact head with no findings. These are source/CI
results, not shared-main landing or fleet installation.

The two subset fixtures and current-file writer replay fixture reproduced
missing unselected records before the fix. The six-case focused suite then
passed. A seventh case separately injected an unselected peer commit during
the real workspace push: the first push raced, the existing rebase/retry
succeeded, and both selected and peer-updated hashes survived at origin.

Partial intent is internal record metadata. Each writer invocation preserves
unselected raw feature blocks from its current input. The existing Git
three-way rebase/refusal path is retained for push races; it is not replaced
with an unconditional snapshot rewrite. Full park still removes gone records.
The public workspace schema and JSON output are unchanged.

Fixtures use disposable local repositories and a disposable workspace only.
The consumer copy and its exact hashes/CI/Codex review are recorded separately.
No real operator handoff, shared-source merge, queue admission or release
qualification is claimed here.
