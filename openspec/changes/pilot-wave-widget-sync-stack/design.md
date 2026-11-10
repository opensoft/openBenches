# Design

## Context

Reuse the verified stack admission and hosted candidate checks from the
project wrapper pilot.

## Goals / Non-Goals

- Test Wave widget reconciliation without a running Wave app, real user
  settings, a Docker socket, or credentials.
- Keep the launcher, host discovery, release validation, and existing queue
  routes outside this change.

## Decisions

- Use a dedicated branch prefix and approval context. The same three exact
  paths are checked at queue admission and again for every candidate member.
- Run focused safety fixtures for each PR; run the entire fixture suite on
  native Ubuntu and macOS after verifying a candidate. Reuse the stable
  Mergify gate rather than create a second merge condition. PR validation
  uses a differently named aggregate and cannot authorize a merge.

## Risks / Trade-offs

- GNU fixture success does not exercise the Darwin publication branch:
  require native macOS as well. Neither job proves live Windows/WSL behavior.
- Missing, stale, or mismatched evidence, or any incomplete platform result,
  blocks the candidate. Existing CI stays in place.

## Migration Plan

Review one config PR before enabling live admission. Validate a live stack
only after a separate approval; if the config needs rollback, revert it
through an ordinary PR.
