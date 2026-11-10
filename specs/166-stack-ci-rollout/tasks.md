# Tasks: OpenBenches stack CI bootstrap

| Set | Outcome | Task IDs | Parent | Fast verification | Safe intermediate state |
| --- | --- | --- | --- | --- | --- |
| SET-01 | Add exact-head fast CI and candidate-only integration for the opt-in queue | T001, T002, T003 | None | `python3 devcontainer.test/test-stack-ci.py` and workflow lint | App access and all existing gates unchanged |

- [x] T001 Add both workflow checks and a fail-closed candidate guard.
- [x] T002 Prepare the dormant queue and document canary admission and rollback.
- [x] T003 Cover accepted and rejected Git revisions with focused fixtures.
