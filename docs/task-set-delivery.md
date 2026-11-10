# Task-set delivery

Use one small PR for each task set in `tasks.md`. Keep the existing story phases,
task IDs, and per-task verification; the set table groups those tasks into PRs.
Start with one outcome and roughly two to five related tasks. Split when a
reviewer needs to make two independent decisions. Keep tests with the behavior
they prove. A lower slice that cannot safely land alone needs a backward-compatible
boundary or a disabled-by-default flag.

## Authoring and review

1. Identify the task set and its parent. Let Spec Kit own the feature and worktree
   names; use GitHub's `gh-stack` extension to track the ordered branches.
   Keep Mergify as the only merge queue for this rollout.
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

## Publish a stack for Mergify

Use the [official GitHub CLI extension](https://github.com/github/gh-stack)
with your normal GitHub authentication; no Graphite account is required.
Install it once with `gh extension install github/gh-stack --pin v0.3.0`.
For a two-task-set canary:

```bash
gh stack init --base main ci/stack-canary/example-first
# Implement, stage and commit the first task set.
gh stack add ci/stack-canary/example-second
# Implement, stage and commit the second task set.
gh stack view --short
gh stack push
gh pr create --draft --base main --head ci/stack-canary/example-first
gh pr create --draft --base ci/stack-canary/example-first --head ci/stack-canary/example-second
```

In the second PR body, include `Depends-On: #N`, replacing `N` with the
first PR's number. Use the actual Spec Kit set IDs and PR verification commands.
`gh stack push` publishes branches without creating or linking PRs. Do not use
`gh stack submit` or `gh stack link` here: they register a GitHub stack object,
and [Mergify requires a ruleset exemption for registered stacks](https://docs.mergify.com/merge-queue/stacks/).
The ordinary PR chain has no GitHub-native stack map; Mergify recognizes it
from the PR bases and dependency markers. Use Mergify to enqueue and land it,
not `gh stack merge` or GitHub's native merge queue.

Rebase locally before the first push if needed. If GitHub blocks a
non-fast-forward update to published branches, use fresh branches and new
PRs, verify their dependency chain, and obtain fresh CI and review evidence.
Never bypass the ruleset or rewrite an enqueued stack.

## OpenBenches rollout canary

Keep the current merge path and existing checks in place. Admit only a
separately approved canary; do not queue release work.

- Use the gh-stack authoring and ordinary PR steps above to publish one
  same-repository stack of two or three PRs from
  `ci/stack-canary/` branches, rooted at `main`. The first canary is limited
  to this guide and Markdown files directly under `.specify/templates/`.
- A maintainer compares each PR's current head and immediate base with the
  `openbenches-pr-fast` log and checks applicable review on that head. Then
  apply `stack-ci-reviewed` to each member. A label is not approval of a new
  head or base: remove it and obtain fresh evidence after any change.
- Before queueing, record the PR numbers, head and immediate-base SHAs, fast CI
  runs, and applicable review receipts in the rollout issue. This makes it
  possible to compare the approved stack with the queue candidate.
- With the queue empty, enqueue from the top PR using `@mergifyio queue`.
  Do not edit or restack in flight. Inspect the queue's candidate PR against
  `main`: it must contain exactly the approved members. If the stack or base
  moves, dequeue and revalidate. Do not add unrelated PRs to the batch.
- Capture one successful `openbenches-stack-heavy` run on the exact candidate
  and compare its tree with the landed tree. A failed candidate must not
  move the target. Stop admitting stacks and dequeue outstanding work if the
  canary fails; never manually merge past a failed heavy check.

Existing release validation and publishing are independent of these checks.

## Shared-helper pilot

Use the same authoring and queue procedure for an approved code pilot, with
`ci/stack-helpers/` branches. Only these paths are eligible:

- `devBenches/base-image/files/speckit-worktree/templates/specify/extensions/git/scripts/bash/get-last-worktree.sh`
- `devBenches/devcontainer.test/test-speckit-git-feature.sh`

Fast CI also runs the Bash feature behavior suite for these paths. Before
queueing, a maintainer records the exact heads and immediate bases, fast CI and
applicable review in the rollout issue. For each PR in the same ordered stack,
the maintainer applies `stack-ci-reviewed` and posts a GitHub commit status on
that PR's reviewed head. Use the full immediate-base SHA, the same ordered PR
numbers (bottom first, comma-separated) for every member, and the evidence link:

```bash
gh api "repos/$repo/statuses/$head" \
  -f state=success -f context=openbenches-helper-reviewed \
  -f "description=base=$immediate_base stack=$ordered_pr_numbers" \
  -f "target_url=$evidence_url"
```

The label alone does not authorize a helper candidate. Heavy CI verifies the
ordered merge parents, current GitHub PR heads and bases, and those receipts
before testing the combined tree. If an input changes, dequeue the stack and
remove its admission labels. Recheck the new inputs and post fresh receipts
before queueing again. For a partial landing, stop and verify the target before
retrying. Do not manually merge past a failed heavy run.

## Project wrapper pilot

For a separately approved stack, use `ci/stack-project/` branches and the
ordinary same-repo dependency chain described above. Only `scripts/project`
and `devcontainer.test/test-project-command.py` are eligible. Installer, setup,
pin, and other component paths stay out of this queue.

Use the same head/base evidence and `stack-ci-reviewed` label as the helper
pilot, but post the exact-head status as `openbenches-project-reviewed`. Keep
the same ordered PR list in each receipt and require focused wrapper fast CI,
applicable exact-head review, and the existing component checks.

On a Mergify candidate, verify the exact approved stack before running the
full project fixture suite on Ubuntu and macOS. Both jobs must pass in the
same workflow run before the aggregate `openbenches-stack-heavy` can succeed.
The config PR exercises those platform jobs and a differently named aggregate;
it is not a queue candidate. The optional upstream-CLI test is not covered
without its fixture source. Record the landed tree and stop on any mismatch.

## Wave widget sync pilot

For a separately approved live stack, use `ci/stack-wave-widget-sync/`
branches and the same exact head/base and ordered-stack receipts as the
project pilot, with the `openbenches-wave-widget-sync-reviewed` context and
the `stack-ci-reviewed` label. The manual queue admits only
`scripts/sync-wave-widgets.sh`, `scripts/sync-wave-widgets.py`, and
`devcontainer.test/test-wave-widget-sync.py`. Keep the Wave launcher,
workstation setup, and Windows/WSL host discovery changes out of this pilot.

Require focused per-PR fixtures and existing CI before admission. The
candidate verifier must approve the entire chain before the full widget
fixture suite runs on Ubuntu and macOS. Both must pass within one workflow
before `openbenches-stack-heavy` succeeds. These fixtures use disposable
settings, not a running Wave app or a bench. A config PR uses the separately
named `Stack config aggregate`; it cannot authorize a queue merge.
Record the candidate, workflow, and matching landed tree in #250.
