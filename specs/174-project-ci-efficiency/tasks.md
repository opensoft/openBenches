# Tasks

| Set | Outcome | Tasks | Verification |
| --- | --- | --- | --- |
| SET-01 | Project efficiency config PR | T001-T003 | Scope/push/lifecycle fixtures, lint, hosted fallback and review |

- [x] T001 Add positive and negative fixtures for project PRs and push proof.
- [x] T002 Implement scoped classification, full fallback and preserved candidate coverage.
- [x] T003 Document intent/proof, validate, and open a config PR without live admission.

Delivered as PR #301. Local validation: 22 project policy tests, 32 shared
stack-policy tests, 77 project fixtures (one optional upstream-CLI skip), 21
Wave fixtures, syntax checks, actionlint and strict OpenSpec validation.
Hosted checks and exact-head review remain mandatory before any later merge;
this task does not authorize merge or live-canary admission.
