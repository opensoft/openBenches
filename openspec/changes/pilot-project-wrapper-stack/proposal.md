# Proposal: Pilot the project wrapper queue

## Why

Three helper stacks proved the queue mechanics. The next bounded pilot needs
the same admission checks plus combined behavior tests on Linux and macOS.

## What Changes

- Add a manual queue for `scripts/project` and its fixture suite only.
- Require focused fast tests, exact head/base approvals and one aggregate
  result for the two-platform candidate run.
- Exercise the platform matrix on the config PR without a live queue run.

## Capabilities

### New Capabilities

- `project-wrapper-stack-pilot`: manual admission and cross-platform candidate
  validation for the checkout wrapper.

### Modified Capabilities

None.

## Impact

Non-release stack CI and queue configuration only. The wrapper, installation,
existing CI, GitHub app access, rulesets and release automation do not change.
Spec Kit handoff: `specs/169-project-queue-pilot/`.
