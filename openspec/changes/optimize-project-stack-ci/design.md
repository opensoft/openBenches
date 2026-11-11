# Design

## Context

Reuse the Wave guards, but emit a project-specific result consumed only by
project component CI. Its unrestricted push trigger requires additional proof.

## Goals / Non-Goals

No integration is removed until the same component commands/platforms run on
the candidate. Do not modify release automation or enable helper efficiency.

## Decisions

- Execute policy only from trusted main, with read-only job-scoped API access.
  PR commits are Git data, never code executed with the API token.
- Generalize the existing allowlist checks while keeping Wave wrapper entry
  points and behavior. Require `Stack-CI: project` on PR bodies and on source
  commit messages for pre-PR push opt-in.
- Author pushes must match their exact event SHA, project namespace, current
  main ancestry and regular-content allowlist. Unknown pushes keep full CI.
- Queue pushes require the existing Mergify actor/ref checks and full exact
  head/base/receipt verification. The heavy workflow still always verifies.
- For main pushes, reconstruct a completed successful candidate's ordered
  merge chain and approval receipts. Compare every landed prefix parent,
  original head, base and tree; require matching GitHub merge records after
  the heavy aggregate. Mergify identity or a similar tree alone is insufficient.
  Bound the search to recent runs. Missing/expired/ambiguous evidence means full CI.
- Add Ubuntu latest to the existing Ubuntu 24.04/macOS candidate matrix and
  carry all component syntax checks. This preserves both existing platform
  selections. The aggregate must require the full selected matrix.

## Risks / Trade-offs

Old trusted policy on the config PR cannot select the new fast route, so that
PR runs full checks. Candidate/run lookup is conservative and can produce
extra full checks, never an unverified skip. A separate live canary remains
necessary after review and merge.

## Migration Plan

Open one config PR with offline graph/API tests and hosted full fallback.
Stop before merge or live admission. Roll back through an ordinary PR.
