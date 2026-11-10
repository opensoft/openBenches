# Tasks

| Set | Outcome | Tasks | Verification |
| --- | --- | --- | --- |
| SET-01 | Bounded discovery race recovery | T001-T003 | Red/green fault injection, full platform suites, unchanged CI and fresh canary proposal |

- [x] T001 Add deterministic reproduction and safety cases; demonstrate the recorded transient error fails before implementation.
- [ ] T002 Implement bounded fresh snapshot recovery; validate exclusions, parsing/corroboration and unchanged concurrency stress.
- [ ] T003 Qualify the normal fix PR, request exact-head review and propose (do not run) a fresh helper canary for #250.
