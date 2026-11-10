# Tasks

| Set | Outcome | Tasks | Verification |
| --- | --- | --- | --- |
| SET-01 | Helper coverage parity | T001-T003 | Baseline command parity, five-job gate tests, hosted jobs |

- [x] T001 Freeze the baseline inventory and add parity/gate fixtures; verify failures before implementation.
- [x] T002 Share existing commands, preserve ordinary CI and add all five exact-candidate jobs; verify parity, gate and regression tests.
- [x] T003 Document the boundary, validate locally and on hosted runners, and open an unqueued config PR with exact-head review. No merge or live canary.

Delivered as PR #309. Source qualification at `3a8442d`: all five helper config
jobs and the existing project/Wave matrix passed; ordinary Bash (three jobs)
and PowerShell (two platforms) also passed in full for PR and push events.
Local parity/gate tests, 32 shared policy tests, 31 project policy tests,
workflow lint, diff checks and strict OpenSpec validation passed. Exact-head
Codex review was clean. Recheck CI/review on later commits before any authorized
merge; this is not skip-routing or live-canary acceptance.
