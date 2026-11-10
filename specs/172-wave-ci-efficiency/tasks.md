# Tasks

| Set | Outcome | Tasks | Verification |
| --- | --- | --- | --- |
| SET-01 | Config-only Wave efficiency PR | T001-T003 | Negative/positive fixtures, full config-PR fallback, Codex review |

- [x] T001 Add fixtures for eligible members, mixed chains, stale inputs, unsafe Git changes, and read failures.
- [x] T002 Implement trusted classification and full-check fallback with routing assertions.
- [x] T003 Document eligibility and validate locally; request exact-head review when opening the config PR.

Before merge, require the hosted full fallback checks and config matrix.
Live fast-only routing remains a separately authorized canary.
