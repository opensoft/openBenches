# Task-set delivery

For opt-in Claude/Codex installation and activation, see the
[shared workflow preview](shared-task-set-workflow.md). Agent installation does
not change the CI eligibility or queue admission rules below.

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

### Helper candidate coverage parity

The helper heavy workflow requires five integration jobs: full Ubuntu Bash
regression, Git 2.34.1 compatibility, Bash 3.2 compatibility, full Ubuntu
PowerShell, and native Windows PowerShell state regressions. Every job checks
out and verifies the exact candidate revision. Shared local actions preserve
the ordinary workflow commands, environment overrides and pinned legacy images;
`devcontainer.test/helper-integration-baseline.json` records their pre-extraction
inventory at main `05dce7e` for offline parity checks.

All five results must be successful before `openbenches-stack-heavy` can pass.
Config PRs exercise the same five jobs and retain the distinct config aggregate.
The docs queue keeps its existing inline integration; project and Wave routes
remain unchanged. Helper integration is no longer duplicated inside verification.

### Helper-only CI efficiency

Coverage parity landed in #309. The efficiency config is a separate qualification
step, not live-canary acceptance; authorize and audit the first efficiency stack
separately in #250. Do not admit a stack merely to test this configuration.

For eligible `ci/stack-helpers/` members, put a standalone `Stack-CI: helper`
line in both the PR body and source commit message before pushing. Preserve
`Depends-On: #N`, the two-file allowlist above and existing manual exact-head
review receipts. CI opt-in never grants queue admission.

The trusted-main helper classifier uses the same event-proof engine as project
CI, with explicit helper scope (never selected from event data or environment).
It can omit only duplicate ordinary Bash and PowerShell integration:

- Open author PRs require live same-repo, non-draft head/base, opt-in and an
  unambiguous chain of at most three members rooted at current main, with
  immediate and cumulative regular-content diffs inside the helper allowlist.
- Source pushes require exact event SHA/ref/repository, the helper namespace,
  head-bound commit opt-in, current-main ancestry and scoped regular-content diff.
- Candidate pushes/PRs require Mergify origin and exact ordered-batch receipts.
  Third-party candidate metadata edits still require exact live head/base proof;
  other actions retain the Mergify actor guard. Closed/dequeued candidates need
  completed successful exact-head evidence, not an actor/prefix exemption.
- Landings require a successful first-attempt candidate run with verification,
  aggregate and all five helper jobs; exact parents, heads, receipt chain, trees
  and GitHub merge timing must match. Historical policy and shared command
  actions must equal trusted main. Discovery remains bounded to 20 runs.
- Delayed author `edited` metadata requires a verified same-head merged helper
  PR, complete modified-file allowlist and a regular-content merge reachable
  from main. Real open changes and other closed events are not exempted.

Ordinary, mixed, empty, stale, renamed/deleted/mode/type-changed, fork, manual,
unknown or unproven inputs keep full checks. Classifier errors or missing,
non-successful, non-literal-`true` outputs also keep full checks. All existing
integration job identities, runners, timeouts and original trigger paths remain.

Qualified members retain focused `openbenches-pr-fast`, policy regressions,
applicable CodeQL and exact-head review. One combined heavy workflow retains
all five helper jobs and the fail-closed aggregate; skipped/missing/failed jobs
cannot satisfy it. Config PRs run full ordinary and config integration using
old trusted main. Mergify batching, admission, apps, rulesets and releases are
unchanged. A later live canary must audit source/candidate/main pushes and late
metadata, one heavy workflow and matching landed trees—not just initial PR CI.

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
full project fixture suite on Ubuntu latest, Ubuntu 24.04, and macOS, plus
all syntax checks from the ordinary project workflow. Every matrix job must pass in the
same workflow run before the aggregate `openbenches-stack-heavy` can succeed.
The config PR exercises those platform jobs and a differently named aggregate;
it is not a queue candidate. The optional upstream-CLI test is not covered
without its fixture source. Record the landed tree and stop on any mismatch.

### Project-only CI efficiency

The config implementation is not live-canary acceptance. Authorize and audit
the first efficiency stack separately in #250; do not widen helper or Wave scope.

For each `ci/stack-project/` member, put a standalone `Stack-CI: project` line
in both its PR body **and its source commit message** before pushing. The
commit marker binds pre-PR push intent to the exact SHA; the PR footer alone
cannot deduplicate the push that preceded PR creation. Keep `Depends-On: #N`
and the existing exact-head review receipts. Neither opt-in grants admission.

The trusted-main project classifier can omit only the duplicate
`project-command` integration matrix:

- Open PR: verify live same-repo, non-draft head/base, explicit opt-in, an
  unambiguous chain of at most three members rooted at current main, and both
  immediate and cumulative regular-content diffs in the two-file allowlist.
- Source push: require the exact event SHA/ref/repository, project namespace,
  head-bound commit marker, current-main ancestry, and regular-content scope.
- Queue push or Mergify draft PR: verify the exact ordered batch, original
  heads, bases and project receipts. A delayed draft metadata event can instead
  use a completed successful run at that exact candidate, with matching policy
  and all project platform jobs. Actor identity or a branch prefix is not proof.
- Main landing push: find a recent successful candidate run and reconstruct
  its ordered Git/receipt chain. Match every landed prefix's parents, original
  heads and trees, and GitHub merge records after the heavy aggregate finished.
  Candidate policy/workflows must equal trusted main. The lookup is bounded to
  20 successful push runs and rejects incomplete jobs or rerun attempts.
- Delayed `edited` metadata on a merged author PR: require the same live head,
  complete modified-file allowlist, and a matching regular-content merge already
  reachable from trusted main. Other closed events do not get this exception.

For candidate PR `edited` events, the metadata editor can be a maintainer or
another bot: the live creator must still be Mergify, and exact head/base, repo,
scope and batch proof must match. Non-metadata actions retain the Mergify actor
requirement. A closed/dequeued draft uses an exact-head workflow lookup bounded
to 20 push runs, without a server-side success filter; the policy itself still
requires completed success, every expected job and unchanged policy. Dequeue
alone is not an exemption. Missing or unsuccessful proof, closed-unmerged
members and real or uncertain input changes retain full checks. This changes
neither queue admission nor push/landing actor guards and never requeues work.

Qualified author PRs keep focused `openbenches-pr-fast`, policy regressions,
applicable CodeQL, and exact-head review. The **single** combined-candidate
heavy workflow still verifies admission and runs every project platform job.
The aggregate cannot pass a failed, cancelled, skipped, or missing matrix.
Mergify batching, manual labels/receipts, rulesets, apps, and releases are unchanged.

Mixed ancestors, empty diffs, renames/deletions/type/mode changes, stale heads,
missing markers, unknown events, ordinary/tag pushes, failed or unavailable
proof, classifier failure, and missing/non-`true` outputs retain full checks.
The config PR itself uses old trusted-main policy, so it must exercise the
full ordinary component matrix and the separately named config aggregate.
An efficiency canary must also audit source/candidate/main pushes and late
metadata, not merely the initial per-PR run.

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

### Wave-only per-PR CI efficiency

To opt in, add a standalone `Stack-CI: wave-widget-sync` line to each PR body.
The Workstation Setup classifier runs trusted code from `main`, checks live
GitHub heads and bases, and reads PR commits only as Git data. Eligible members
must be open, non-draft, same-repository PRs on `ci/stack-wave-widget-sync/`.
Their `Depends-On` chain must be unambiguous, contain at most three members,
and root at current `main`. The bottom member can opt in before its dependants
exist; this is CI selection only, not queue admission.

Only regular content modifications to the three Wave pilot files qualify.
Both immediate member diffs and the cumulative main-to-head diff must stay
within that scope. Renames, deletions, file-mode/type changes, mixed ancestors,
stale event data, missing opt-in, API errors, and classification failures all
retain the full workstation checks. Push, tag, and manual runs also stay full.

An eligible PR keeps focused `openbenches-pr-fast` checks and applicable
CodeQL/review, but omits Workstation Setup's `regression`, `tools-runtime`,
`credential-images`, and `component-lifecycle` jobs. The existing manual
admission receipts and full Ubuntu/macOS queue candidate gate are unchanged.
Do not apply this opt-in to other components. The config PR is not a live
efficiency canary; authorize and record that separately in #250.

Already-merged metadata is a separate, narrow exception: for an `edited`
event, trusted GitHub readback must confirm that the opted-in, same-repository
Wave PR is closed and merged into main at the exact event head, with a complete
list of modified files limited to the Wave allowlist. The classifier then
reports `merged_metadata=true`, not `wave_only=true`. This handles edits queued
before the merge but processed afterward. Open PRs continue through the
existing eligibility checks; changed heads, other event actions, unmerged
closures, missing data, or API errors do not receive this exception. Only
successful explicit classifier outputs can omit workstation jobs.
