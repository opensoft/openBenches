# Tasks: Park handoff safety

## Task Sets and Pull Requests

| Set | Outcome | Task IDs | Parent | Fast verification | Safe intermediate state |
| --- | --- | --- | --- | --- | --- |
| SET-01 | Refuse wrong leg repository/branch before park commits | T001–T003 | main | bash devBenches/devcontainer.test/test-speckit-git-feature.sh | Existing subset behavior remains unchanged; no new activation |
| SET-02 | Preserve unselected parked records at each manifest write | T004–T005 | SET-01 | bash devBenches/devcontainer.test/test-speckit-git-feature.sh | Backward-compatible partial scope; full park unchanged |
| SET-03 | Verify origin before accepting an existing resumed worktree and reconcile the consumer | T006–T009 | SET-02 | python3 devBenches/devcontainer.test/test-speckit-park-handoff.py | Current-origin refusal restored; safe idempotence retained |

## Governance and US1

- [x] T001 [S] Capture commissioned scope, draft origin, decisions and the dependency-chain delivery; files: openspec/changes/fix-park-handoff-integrity/**, specs/177-park-handoff-safety/**.
- [x] T002 [O] Reproduce and fix wrong repository/branch preflight before either leg commits; files: shared park.sh, test-speckit-git-feature.sh and test-speckit-park-handoff.py; verify heads, dirty state and refs are preserved on refusal.
- [x] T003 [S] Validate SET-01 locally, publish its PR and request exact-head Codex review; files: feature evidence and PR. Shared PR #310 at 0fb4061a5a2357d81735a431cbf8cb206e55a8a2 has green CI and an exact-head Codex receipt with no findings.

## US2 and downstream reconciliation

- [x] T004 [O] Reproduce and fix selected-feature preservation using the current manifest for each writer invocation and the existing rebase/refusal path on push retry; files: shared park.sh, workspace-common.sh and fixtures.
- [x] T005 [S] Run full source suites, publish dependent SET-02 and request exact-head Codex review; PR #311 at abfd44e8696608ba46e2e180d73b5f97f82526d7 passed CI and exact-head Codex review without findings.

## US3 and final consumer reconciliation

- [x] T007 [O] Reproduce moved/deleted/unavailable origin on existing worktrees and gate the existing-worktree shortcut before any reset; files: shared resume.sh and focused handoff fixtures. Three refusal cases failed before correction; all eleven focused cases passed afterward.
- [ ] T008 [S] Validate safe repeat resume, publish SET-03 and obtain current-head CI/Codex evidence.
- [ ] T006 [S] Copy the tested shared corrections into openMFA PR #2, retain declared unrelated local deviations, rerun its tests/CI/Codex review and reconcile evidence. Upstream merge/fleet installation remain distinct unclaimed states.
- [ ] T009 [S] Record final source/consumer heads, hashes, test results and review dispositions without claiming upstream landing.

Dependencies: T001 → T002 → T003 → T004 → T005 → T007 → T008 → T006 → T009. The fresh review expansion is captured before dependent implementation. No parallel-agent execution is required. No queue/ruleset change or release task is included.
