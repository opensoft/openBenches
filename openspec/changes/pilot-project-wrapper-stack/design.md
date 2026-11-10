# Design

## Context

The existing docs and helper queues use one heavy check on a Mergify push.
The project wrapper also needs the same fixture suite on macOS.

## Goals / Non-Goals

- Admit only the wrapper and its existing test file, one stack at a time.
- Do not admit setup, installer, pin, release, or mixed-component changes.

## Decisions

- Reuse the reviewed merge-chain verifier with a distinct path set, branch
  namespace and approval context. Keep the two existing queue rules unchanged.
- Verify the candidate before either platform tests it. Run the full fixture
  suite on Ubuntu and macOS, with one aggregate check consuming the matrix
  result. Preserve the existing integration suites for docs and helper scopes.
- Run the same matrix for config PRs, but under a distinct aggregate check name
  that cannot satisfy the Mergify merge condition.

## Risks / Trade-offs

Failed, cancelled or skipped project jobs do not satisfy the gate. Keep the
existing project CI while evaluating the new lane. A fresh approved stack is
needed if the base, head or membership changes.

## Migration Plan

Review the configuration through an ordinary PR. Live admission is a separate
step after approval and merge; no stack is authorized by this PR.
