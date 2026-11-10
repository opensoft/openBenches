# Design

## Context

See proposal.md. Ordinary Bash CI has three jobs; PowerShell CI has Linux and
Windows jobs. The helper candidate currently runs bootstrap/feature/compatibility
inline in verification. Do not remove ordinary checks in this phase.

## Goals / Non-Goals

Add all five integration environments to helper candidates and config PRs,
with exact-SHA checkout and a fail-closed aggregate. No skip selection,
classifier, queue configuration, product helper changes or live canary.

## Decisions

- Share commands via local composite actions while retaining ordinary job
  IDs/names, runners, timeouts, environment overrides and every original path
  trigger. Add triggers for the new actions/tests; do not narrow existing ones.
- Freeze the baseline command inventory at main `05dce7e` for offline parity
  checks, including pinned Docker images, legacy versions and special env.
- Use five explicit helper jobs in the candidate workflow. Keep docs integration
  inline, but move helper integration out of verification to avoid duplicate
  bootstrap/feature/compatibility work within the same heavy workflow.
- Require every helper result to be success for helper candidates and config
  PRs; require them skipped for other existing candidate scopes. Missing or
  failed results cannot authorize `openbenches-stack-heavy`.
- A config PR exercises all five helper jobs alongside existing project/Wave
  config jobs. Ordinary workflows also run in full, intentionally duplicating
  coverage until a later reviewed efficiency change.

## Risks / Trade-offs

Hosted Git 2.34.1/Bash 3.2 containers and native Windows cannot be replaced by
local current-runtime tests. Their real hosted outcomes remain required.
Baseline failures must be reported or fixed explicitly, never bypassed or
silently omitted. Preserve comments and commands when extracting shared steps.

## Migration Plan

Publish one unqueued config PR and request exact-head Codex review. No merge,
live stack, skip-routing rollout, app access or release action is authorized.
