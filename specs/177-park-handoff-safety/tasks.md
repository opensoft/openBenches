# Tasks: Park handoff safety

## Task Sets and Pull Requests

| Set | Outcome | Task IDs | Parent | Fast verification | Safe intermediate state |
| --- | --- | --- | --- | --- | --- |
| SET-01 | Refuse wrong leg repository/branch before park commits | T001–T003 | main | bash devBenches/devcontainer.test/test-speckit-git-feature.sh | Existing subset behavior remains unchanged; no new activation |
| SET-02 | Preserve unselected parked records at each manifest write | T004–T005 | SET-01 | bash devBenches/devcontainer.test/test-speckit-git-feature.sh | Backward-compatible partial scope; full park unchanged |
| SET-03 | Verify origin before accepting an existing resumed worktree | T007–T008 | SET-02 | python3 devBenches/devcontainer.test/test-speckit-park-handoff.py | Current-origin refusal restored; safe idempotence retained |
| SET-04 | Retry pending handoff publication | T010–T011 | SET-03 | python3 devBenches/devcontainer.test/test-speckit-park-handoff.py | Pending commit retained on failure; no new activation |
| SET-05 | Refresh receiving manifest and reconcile the consumer | T006, T009, T012–T013 | SET-04 | python3 devBenches/devcontainer.test/test-speckit-park-handoff.py | Refuse unsafe refresh; dry-run unchanged |
| SET-06 | Preserve existing temporary paths during atomic publication and land reviewed tooling | T014–T017 | SET-05 | python3 devBenches/devcontainer.test/test-speckit-park-handoff.py | Refuse occupied temporary paths before manifest replacement |

## Governance and US1

- [x] T001 [S] Capture commissioned scope, draft origin, decisions and the dependency-chain delivery; files: openspec/changes/fix-park-handoff-integrity/**, specs/177-park-handoff-safety/**.
- [x] T002 [O] Reproduce and fix wrong repository/branch preflight before either leg commits; files: shared park.sh, test-speckit-git-feature.sh and test-speckit-park-handoff.py; verify heads, dirty state and refs are preserved on refusal.
- [x] T003 [S] Validate SET-01 locally, publish its PR and request exact-head Codex review; files: feature evidence and PR. Shared PR #310 at 0fb4061a5a2357d81735a431cbf8cb206e55a8a2 has green CI and an exact-head Codex receipt with no findings.

## US2 and downstream reconciliation

- [x] T004 [O] Reproduce and fix selected-feature preservation using the current manifest for each writer invocation and the existing rebase/refusal path on push retry; files: shared park.sh, workspace-common.sh and fixtures.
- [x] T005 [S] Run full source suites, publish dependent SET-02 and request exact-head Codex review; PR #311 at abfd44e8696608ba46e2e180d73b5f97f82526d7 passed CI and exact-head Codex review without findings.

## US3

- [x] T007 [O] Reproduce moved/deleted/unavailable origin on existing worktrees and gate the existing-worktree shortcut before any reset; files: shared resume.sh and focused handoff fixtures. Three refusal cases failed before correction; all eleven focused cases passed afterward.
- [x] T008 [S] Validate safe repeat resume, publish SET-03 and obtain current-head CI/Codex evidence. PR #312 at 44adc6717af32edae21e85fda7cc849ba1c7592c passed published CI and exact-head Codex review without findings; the full local feature suite also passed.

## US4

- [x] T010 [O] Reproduce an unchanged-content retry after failed manifest publication and exhausted push attempts; separate conditional commit creation from publication and preserve pending evidence. Both fixtures failed before correction; all thirteen focused cases passed afterward.
- [x] T011 [S] Validate and publish dependent SET-04 with current-head CI and Codex review. PR #313 at 0ac1aa4411669ebf78a62445b953a1d81b8180d4 passed CI and exact-head Codex review without findings.

## US5 and final consumer reconciliation

- [x] T012 [O] Reproduce stale receiving manifest and implement safe pre-read refresh; verify dirty/conflicting/unavailable refusals, mutex release and unchanged dry-run. Four new checks failed before correction and the dry-run control passed; all eighteen focused cases passed afterward.
- [x] T013 [S] Validate and publish dependent SET-05 with applicable review. Source CI passed. GitHub Codex review remained quota-blocked; Brett Heap subsequently authorized local review instead. The ten-role local panel reviewed SET-05 head 1d86af68eb789dd19a643a4b7874c1f41567d790 against 0ac1aa4411669ebf78a62445b953a1d81b8180d4 without an independent SET-05 finding. Consumer publication findings are fixed under T014; no GitHub bot receipt is fabricated.
- [x] T006 [S] Copy the tested shared corrections into openMFA PR #2, retain declared unrelated local deviations, rerun its tests/CI/Codex review and reconcile evidence. Consumer 12dc8723239f340c7727387b4a4a36c4359aa2cd passed all 25 cases locally/in CI plus validation and SonarCloud. Its requested review failed on the usage limit recorded under T013. Upstream merge/fleet installation remain distinct unclaimed states.
- [x] T009 [S] Record source/consumer snapshots, hashes, test results and review dispositions without claiming upstream landing; see final-evidence.md. Final clean-review acceptance remains under T013.

## US6 and authorized landing

- [x] T014 [O] Reproduce temporary, directory and selector symlink overwrites and fix descriptor-relative atomic publication with owned-file cleanup — files: shared `workspace-common.sh`, `git-common.sh`, `resume.sh`, `devBenches/devcontainer.test/test-speckit-park-handoff.py`, governing feature/change documents — verify: `python3 devBenches/devcontainer.test/test-speckit-park-handoff.py`. Exact shared fixture copies pass all 27 cases through the consumer; independent security and focused pre-reset QA checks passed.
- [ ] T015 [O] Validate and publish SET-06 with exact-head local review and current CI — files: feature evidence and PR metadata — verify: `git diff --check`.
- [ ] T016 [O] Verify the current-main combined candidate and land eligible shared PRs in dependency order through ordinary protected PR merges — files: landing evidence and PR metadata — verify: `git log -1 origin/main`.
- [ ] T017 [O] Update openMFA #2 to corrected shared bytes and safe core selector publication, rerun tests/CI and local review, and record source landing readback without advancing product pins — files: consumer tooling copies, `.specify/scripts/bash/common.sh`, fixture, tests and provenance/evidence — verify: `python -m pytest tests/runtime_tooling -q`.

Dependencies: T001 → T002 → T003 → T004 → T005 → T007 → T008 → T010 → T011 → T012 → T013 → T006 → T009 → T014 → T015 → T017 → T016. Review expansions are captured before implementation. The local review panel is required by the invoked pr-review skill. No queue/ruleset change, bypass or release task is included.
