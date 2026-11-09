# Task-set delivery

Use one small PR for each task set in `tasks.md`. Keep the existing story phases,
task IDs, and per-task verification; the set table groups those tasks into PRs.
Start with one outcome and roughly two to five related tasks. Split when a
reviewer needs to make two independent decisions. Keep tests with the behavior
they prove. A lower slice that cannot safely land alone needs a backward-compatible
boundary or a disabled-by-default flag.

## Authoring and review

1. Identify the task set and its parent. Let Spec Kit own the feature and worktree
   names; use Graphite to track the ordered branches. Do not enable its merge
   queue for a branch where Mergify owns landing.
2. Include the set ID, task IDs, verification command, and predecessor in each PR.
   For a same-repo Mergify-recognized stack, add `Depends-On: #N` on every
   upper PR and verify that its base is that predecessor's head branch.
3. Run fast CI against every member's current head and immediate base, including
   non-default bases. Verify exact-head Codex receipts and unresolved review
   threads where required. A push, rebase or restack invalidates old head
   receipts; recheck after base changes too.
4. Only queue the approved stack after all members pass. Do not restack it while
   queued. Record the exact batch head, included PRs, heavy job result, and
   resulting target tree. A combined pass is not a guarantee of atomic landing.
   Queue the top PR with `@mergifyio queue` to include its predecessors. If
   Mergify does not see a green fast check after first activation, trigger a
   fresh fast run on the same reviewed head and confirm the queue sees it.

## CI contract

- **Fast**: `pull_request` (including `synchronize` and base edits), a stable
  check name, lint/compile and focused tests. Do not filter only on `main`.
- **Heavy**: a distinct check on the genuine queue candidate, not the PR tip or
  a `main` push. Check out and record its exact SHA. Run integration/build
  checks on GitHub-hosted runners with read-only permissions, no secrets and no
  publication. Mergify admission and merge conditions must reference the two
  distinct checks. Do not use a skipped ordinary-PR job as heavy evidence.
- **Release**: keep protected release QA, source qualification, and publishing
  separate. This procedure does not replace any release check.

## Pilot acceptance

In a private disposable non-release repository, stage three synthetic PRs.
Prove a malformed upper PR fails fast, a cross-PR conflict can pass the fast
checks but fails the combined check without moving the target, and the corrected
stack lands via Mergify after exactly one successful heavy run for its batch.
Record all original head SHAs and the batch head and final target tree.
A split/retry, partial landing, or missing receipt is not a clean one-run result.
Any new GitHub App grant, ruleset change, or billing approval is a separate step.
Do not apply sandbox settings or bypasses to OpenBenches.

References: [Mergify two-step CI](https://docs.mergify.com/merge-queue/two-step/),
[Mergify stack recognition](https://docs.mergify.com/merge-queue/stacks/),
[Graphite external queue integration](https://graphite.com/docs/external-merge-queue-integration).
