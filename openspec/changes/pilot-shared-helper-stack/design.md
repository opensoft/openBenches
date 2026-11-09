# Design

## Context

The docs queue has a live success receipt. The sandbox replay confirmed fast
rejection, cancellation on a new head, whole-batch failure, and corrected
landing. A separate helper queue preserves the existing docs rule.

## Goals / Non-Goals

- Admit only the last-worktree helper and its existing Bash regression suite.
- Do not onboard other code paths, disable checks, or alter app or branch settings.

## Decisions

- Retain same-repository ordinary PRs and the normal merge method. Maintainers
  check fast logs and applicable review before setting the admission label and
  recording a per-head success status with the immediate base and ordered PR
  numbers. A label alone cannot bind that evidence to an immutable revision.
- The Mergify candidate guard matches its first-parent merge chain against
  current GitHub PRs and the per-head approvals. Read-only API access is scoped
  to the validation step. The job does not use queue-draft text as approval.
- When a PR changes one of the helper paths, fast CI runs the existing feature
  behavior suite. The combined candidate keeps all three integration suites.

## Risks / Trade-offs

- A missing or changed PR, base or receipt fails closed. Dequeue, recheck every
  member and issue fresh approvals before trying a new candidate.
- The original PRs land in order, not atomically. Admit one stack at a time;
  inspect the target and halt new admission on a partial landing or mismatch.

## Migration Plan

Land the additive config PR through the ordinary review route. Then authorize
one real helper stack. If it fails, dequeue and leave the docs canary and
normal merge route intact.
