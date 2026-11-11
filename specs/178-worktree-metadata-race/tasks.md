# Tasks

| Set | Outcome | Tasks | Verification |
| --- | --- | --- | --- |
| SET-01 | Bounded discovery race recovery | T001-T003 | Red/green fault injection, full platform suites, unchanged CI and fresh canary proposal |

- [x] T001 Add deterministic reproduction and safety cases; demonstrate the recorded transient error fails before implementation.
- [x] T002 Implement bounded fresh snapshot recovery; validate exclusions, parsing/corroboration and unchanged concurrency stress.
- [x] T003 Qualify the normal fix PR, request exact-head review and propose (do not run) a fresh helper canary for #250.

Delivered in PR #320. See evidence.md for source qualification and the local
resource-allocation exception. Codex review was requested but quota-blocked,
not approved. Recheck exact-head CI/review after follow-up pushes; no merge or
fresh-canary execution is authorized by this task set.
