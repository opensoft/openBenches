# Handoff repair evidence

Snapshot: 2026-11-10. Implementation and CI are complete. Final Codex review
acceptance is blocked by the review account's usage limit; T013 remains open.
All source and consumer PRs are draft and unmerged. Governance remains draft;
no ratification, archive, queue admission or installation is claimed.

| Set | PR | Verified implementation snapshot | CI | Exact-head Codex |
| --- | --- | --- | --- | --- |
| 01 | openBenches #310 | 0fb4061a5a2357d81735a431cbf8cb206e55a8a2 | Passed | Completed, no findings |
| 02 | openBenches #311 | abfd44e8696608ba46e2e180d73b5f97f82526d7 | Passed | Completed, no findings |
| 03 | openBenches #312 | 6f00587571b97bcbee2a09c1f0ac9c66e9c50dc8 | Passed | Completed, no findings |
| 04 | openBenches #313 | 0ac1aa4411669ebf78a62445b953a1d81b8180d4 | Passed | Completed, no findings |
| 05 | openBenches #315 | a20cb8ff38ff325f98e22a7521cd01242782168b | Passed | Failed, usage limit |
| Consumer | openMFA #2 | 12dc8723239f340c7727387b4a4a36c4359aa2cd | Passed | Failed, usage limit |

The consumer's three helpers and canonical fixture copy match SET-05's
implementation snapshot byte-for-byte; git-common also compared identical.
Exact paths and SHA-256 values live in openMFA docs/shared-park-source.md.
Later evidence-only source commits do not change these copied bytes.

Source focused suite: 18 passed locally. Published full source/compatibility
CI passed, including Bash 3.2, Git 2.34.1, PowerShell Linux/Windows and shared
image regression. Image publication was skipped. The full local feature
suite passed at SET-03, and subsequent source changes passed full CI.

Consumer: 25 passed locally in 40.33 seconds and in runtime-tooling CI run
42887164171 in 16.35 seconds. Validate run 42887164283 and SonarCloud passed.
All Bash files passed syntax validation. Both original leg pins and all 11
shape digests remain unchanged.

The seven prior Codex findings are fixed with regression evidence and their
threads are resolved, including the original two park blockers and the fresh
resume-origin, pending-publication and stale-receiver findings. Their
resolution does not substitute for the blocked final review.

The reviewer explicitly reported that the account reached its code-review
usage limit on both final implementation heads. No repetitive retry or
billing change was attempted. Once review usage is available, post exactly
`@codex review` on openBenches #315 and openMFA #2 and verify completed
receipts against their then-current heads. Do not merge on an older receipt.

Feedback/support stays deferred. Neither previously blocked write was
replayed. Fixtures used disposable local origins only; the operator workspace,
live benches, unrelated parent changes and product pins were preserved.
