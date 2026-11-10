# Tasks

| Set | Outcome | Tasks | Verification |
| --- | --- | --- | --- |
| SET-01 | Conservative helper CI efficiency | T001-T003 | Offline event/gate/parity tests and full hosted config coverage |

- [x] T001 Add helper policy fixtures, including all-five evidence and full fallback; prove red before wiring.
- [x] T002 Reuse the proof engine for helper and wire ordinary classifiers without removing coverage; pass both policy suites and parity tests.
- [x] T003 Document opt-in and boundaries, qualify config CI and publish an unqueued PR with exact-head Codex review requested. No merge/live canary.

Delivered as PR #314. Source head `0cceeef` passed all five helper config jobs,
the config aggregate, ordinary Bash/legacy/PowerShell PR and push checks,
106 policy/parity fixtures, project/Wave jobs and CodeQL. Local workflow lint,
strict OpenSpec validation and isolated-Python CLI fallback also passed.
Codex review was explicitly requested but could not complete due to the account
review usage limit; this is not a clean review or merge authorization. Keep
the PR unmerged/unqueued and require fresh exact-head review before merge.
Recheck CI on documentation follow-up heads. No live efficiency canary ran.
