# Proposal

## Why

Native Arch QA capacity is unavailable. On 2026-11-08 the release maintainer
approved an explicit Arch-only exception for exact stable version 1.6.2, accepting
that this release will not have fresh native Arch acceptance evidence.

## What Changes

- Record a reviewed, exact-version waiver in the release manifest, with reason,
  approval and restoration conditions.
- Exclude only arch-native from 1.6.2 release-mode requirements, without removing
  the suite or changing its minimum version.
- Expose the exception as waived-not-executed in planning, validation summaries,
  and published release notes/report; never manufacture a passing suite report.
- Require Arch again for every other applicable version. Retain all remaining
  suites, cleanup, freshness, source/run binding and publication controls.

## Capabilities

### New Capabilities

- `release-qualification-waivers`: Reviewed exact-version native/live exceptions
  with transparent reporting and automatic scope expiry.

### Modified Capabilities

None; existing release governance is amended by the new capability.

## Impact

Release manifest, shared suite selection/evidence gate, publisher, regression
tests, release automation documentation and candidate release notes. No worker,
credential, environment-readiness or published-tag changes. Implementation handoff:
`specs/163-release-arch-waiver/` in the linked feature checkout. Approval source:
the maintainer's explicit instruction to implement the Arch-only 1.6.2 waiver.
