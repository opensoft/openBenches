# Proposal: Pilot the Wave widget sync queue

## Why

The project wrapper stacks proved two-platform batching. Wave widget sync is a
bounded next step with distinct GNU and macOS file publication paths and
fixtures for preserving concurrent user edits.

## What Changes

- Add a manual-only Mergify queue scoped to the widget sync shell entrypoint,
  its Python reconciler, and its fixture suite.
- Verify exact admission evidence, then run one full hosted Ubuntu and macOS
  workflow per approved candidate. Exercise both platforms on the config PR.

## Capabilities

### New Capabilities

- `wave-widget-sync-stack-pilot`: bounded stack admission and platform gates.

### Modified Capabilities

None.

## Impact

Non-release stack CI, queue configuration, fixtures for the CI policy, and
maintainer documentation only. No widget behavior, host discovery, bench
lifecycle, app access, ruleset, or release changes. No live stack in this PR.
Spec Kit handoff: `specs/170-wave-widget-sync-queue/`.
