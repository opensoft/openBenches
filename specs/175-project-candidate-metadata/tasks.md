# Tasks

| Set | Outcome | Tasks | Verification |
| --- | --- | --- | --- |
| SET-01 | Candidate metadata config fix | T001-T003 | Offline lifecycle/negative fixtures, hosted fallback, review |

- [x] T001 Reproduce third-party and closed/dequeued failures, and strengthen negative assertions; verify red fixtures.
- [x] T002 Implement metadata-only editor handling and exact-candidate evidence lookup; verify lifecycle and full-fallback regressions.
- [x] T003 Update the delivery guide, validate and open an unqueued config PR; verify hosted checks and request exact-head review. Do not merge or run a canary.

Delivered as PR #305. Local verification: 31 project policy tests, 32 shared
stack/Wave tests, 77 project fixtures (one optional upstream-CLI skip), 21 Wave
fixtures, workflow lint, diff checks and strict OpenSpec validation. An
in-memory mutation removing landed-tree equality is caught by the strengthened
regression. Hosted CI and exact-head Codex review remain required before a
later authorized merge; fixtures are not repeat-canary acceptance.
