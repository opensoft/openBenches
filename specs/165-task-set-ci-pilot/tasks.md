# Tasks: Task-set PR and CI pilot

| Set | Outcome | Tasks | Predecessors | Verify |
| --- | --- | --- | --- | --- |
| SET-01 | OpenBenches can plan small PRs without changing its release workflow | T001 | None | Strict OpenSpec validation and path-scope diff |
| SET-02 | The private sandbox has a checked two-step CI harness | T002 | SET-01 | Valid workflow/queue schema and hosted PR checks |
| SET-03 | A real stack proves the combined candidate gate | T003 | SET-02 | Compare original head receipts, Mergify batch membership, heavy run, and resulting target SHA |

- [X] T001 [O] Adopt the task-set constitution and synchronize the Spec Kit templates and guidance — files: `.specify/memory/constitution.md`, `.specify/templates/tasks-template.md`, `.specify/templates/plan-template.md`, `docs/task-set-delivery.md` — verify: `openspec validate task-set-pr-queue-pilot --strict --no-interactive && git diff --check`
- [X] T002 [O] Provision and validate the synthetic two-step CI sandbox without any existing-repo ruleset changes — files: `docs/task-set-delivery.md` (external sandbox artifacts listed there) — verify: `test -n "$PILOT_FAST_RUNS" && for run in $PILOT_FAST_RUNS; do gh run view "$run" --repo "$PILOT_REPO" --exit-status || exit; done`
- [ ] T003 [O] Prove Graphite-authored stack recognition, failed-batch isolation, and successful combined validation with Mergify — files: `docs/task-set-delivery.md` (pilot acceptance procedure) — verify: `test -n "$PILOT_HEAVY_RUN" && gh run view "$PILOT_HEAVY_RUN" --repo "$PILOT_REPO" --exit-status`
