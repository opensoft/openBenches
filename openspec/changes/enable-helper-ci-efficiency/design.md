# Design

## Context

See proposal.md. PR #309 merged as fa17727, establishing all five integration
jobs. Project efficiency already handles author/source/candidate/landing/late
metadata with conservative proof. Helper admission already has a two-file scope.

## Goals / Non-Goals

Reuse the event-proof algorithm, not a second divergent copy. Scope selection is
an explicit trusted loader argument, never an event/environment input. Project
defaults and Wave behavior stay unchanged. No new admission, live stack or releases.

## Decisions

- Extend the existing project engine with an explicit project/helper scope and
  a tiny helper entry point. This avoids copying the complex landing proof.
- Helper evidence requires Verify queue candidate, openbenches-stack-heavy and
  all five named helper jobs in the same exact-head first-attempt successful run.
- Include helper ordinary workflows, shared actions, baseline, policy and tests
  in historical policy comparison, so changed commands cannot reuse old success.
- Add trusted-main read-only classifiers to both ordinary workflows. Retain every
  integration job and trigger path. Only successful literal skip_helper=true
  omits jobs; failed/missing outputs and unsupported events retain full coverage.
- Parameterize existing offline fixtures and run the same event failure suite
  for both policies, plus helper-specific five-job and workflow assertions.
- Keep heavy commands/admission unchanged. Config changes trigger full config CI.

## Risks / Trade-offs

Shared-engine regression -> run project fixtures unchanged in semantics plus
helper fixtures. No fork execution -> checkout trusted main, isolated Python,
no persisted credentials. Historical lookup is bounded; unavailable proof costs
extra ordinary CI instead of weakening validation.

## Migration Plan

Open one unqueued 1.7 config PR, require full ordinary/config hosted jobs and
exact-head Codex review. No merge/live canary in this phase. Reverting selection
wiring restores full ordinary checks without changing integration commands.
