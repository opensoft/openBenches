# Design

## Context

See proposal.md. Only candidate PR metadata selection changes. The policy
runs from trusted main; fetched commits remain Git data, not executable code.

## Goals / Non-Goals

Avoid duplicate component work on proven candidate metadata, including a
closed draft whose source PRs were dequeued without merging. Do not modify
author PR classification, push/landing actor checks, admission or workflows.

## Decisions

- Exempt only `edited` events from the Mergify event-actor requirement. Live
  candidate creator, repo, exact head/base, scope and ordered batch checks
  remain authoritative. Other actions keep their existing actor boundary.
  Do not whitelist Sourcery or trust a branch name without proof.
- For closed or asynchronously updated candidates, query the known workflow
  by exact head SHA and push event, bounded to 20 runs. Omit the server-side
  success filter that missed the canary run, but still validate every run's
  exact SHA/ref/actor/repo, attempt, completed success, complete jobs and
  unchanged policy. Main landing discovery is deliberately unchanged.
- Keep closed-unmerged source PRs, missing/failed proof, changed snapshots,
  mixed paths, API/Git errors and policy drift on full fallback.
- Strengthen the existing wrong-tree regression by matching its synthetic
  merge record, so tree equality is independently exercised.

## Risks / Trade-offs

Missing or stale exact-run results still produce extra full CI. Bounded
lookup and conservative errors remain intentional; fixtures are not live
qualification. No queue is restarted or canary repeated in this change.

## Migration Plan

Open one config PR, validate fixtures and hosted full fallback, and request
exact-head Codex review. Merge and a repeat live canary require later authority.
