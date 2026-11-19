---
name: task-set-delivery
description: Plan and deliver small Spec Kit task-set PRs using gh-stack authoring and Mergify merging in repositories that adopt this workflow.
metadata:
  version: "1.7-preview.1"
---

# Task-set delivery

Use this process for feature planning, task generation, implementation and PR
delivery in an opted-in repository. Honor narrower repository instructions and
the user's current action scope. Planning does not authorize publishing or merging.

## Plan small, safely landable sets

Read the constitution, feature plan/tasks and repository CI/merge contract.
Keep Spec Kit's feature/worktree naming and task IDs. Add a task-set table to
`tasks.md`: set ID, outcome, task IDs, immediate predecessor, fast verification
command and safe intermediate state. Assign each implementation task to exactly
one set and one PR; do not duplicate the task checklist. Aim for one review
decision and roughly two to five related tasks, not an arbitrary line limit.
Keep tests with their behavior. A dependent change must still be safe if its
lower PR lands alone; use a compatibility boundary or disabled feature when needed.

## Check the target repository, not just the installed tools

- Verify `gh stack --version` reports 0.3.0. If missing, request permission to run
  `gh extension install github/gh-stack --pin v0.3.0`, or use the bootstrap's
  explicit `--install-stack-tools` option. Do not replace another installed version.
- Use existing GitHub authentication. Do not create tokens or change app access,
  rulesets, bypasses, billing, permissions or release workflows to unblock delivery.
- Check whether the target repository has an approved Mergify queue and CI scope.
  Tool installation grants neither. Outside an approved complete stack scope,
  keep ordinary full CI. Mixed or uncertain changes always retain full checks.
- In OpenBenches, read `docs/task-set-delivery.md` and current queue policy before
  choosing any efficiency label, branch prefix, body marker or admission receipt.
  This skill does not widen the helper/project/Wave allowlists.

## Author ordinary dependent PRs

Use `gh stack init --base main <first-branch>`, `gh stack add <next-branch>`,
`gh stack view --short` and `gh stack push` for local ordering and branch pushes.
Create ordinary PRs with `gh pr create`: lower targets main, each upper targets
its immediate predecessor's head branch. Put `Depends-On: #N` in every upper
PR body, together with set/task IDs and verification commands.

Do not use `gh stack submit`, `gh stack link` or `gh stack merge` in this rollout.
Registered GitHub stack objects need different Mergify governance; the current
contract uses ordinary dependent PRs and Mergify as the only merger.

## Review, queue and verify within granted authority

Verify checks for every current head and immediate base. Request Codex review
with a top-level comment exactly `@codex review`, unless the user explicitly
waives that PR or an exact-head connector review already exists. A quota error,
Copilot review or old-head receipt is not Codex approval. Recheck unresolved
threads and invalidate prior evidence after meaningful pushes, restacks or base changes.

Do not enqueue without the required review, checks, repository admission proof
and user merge authority. When authorized, use the repository's Mergify procedure
to queue the top PR and include its predecessors. Do not restack while queued.
If a check fails, fix the source and obtain fresh head/base evidence; do not
silence it, stamp an unearned status or fall back to direct merging.

For a qualified efficiency stack, record the original heads, ordered members,
combined candidate SHA, heavy run/attempt, and landed parent/tree identities.
One heavy run means one genuine combined validation, not a green author PR or
main push. A split/retry or partial landing is not a clean one-run result.
Report local tests, hosted checks, reviews, merges and live acceptance separately.
Release qualification remains independent; this workflow does not authorize a tag.
