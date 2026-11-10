# Design

## Context

Wave-only PRs trigger four Workstation Setup jobs even though the queue has
a full, separately gated Ubuntu/macOS Wave fixture matrix.

## Goals / Non-Goals

Reduce only those four redundant non-release PR jobs. Preserve all push,
tag, manual, release, ordinary PR, mixed-change, and candidate behavior.

## Decisions

- Execute the classifier from a read-only, trusted `main` checkout. Fetch
  PR commits as Git data only; never execute PR code with the read token.
- Require an explicit `Stack-CI: wave-widget-sync` footer on every member,
  the Wave branch prefix, same-repository open non-draft PRs, current event
  heads/bases matching the API, and an unambiguous predecessor chain rooted
  at current main. Walk at most three members. A bottom PR can qualify while
  its dependants are being authored; this does not authorize queue admission.
- Check both each member's diff and the full main-to-head diff. Only content
  modifications of the three existing regular Wave files qualify; deletes,
  renames, type/mode changes, and out-of-scope ancestors select full checks.
- Default to full checks on every error or missing result. The four jobs
  explicitly run when classification fails, including checkout/API failures.
- Leave focused fast CI, CodeQL, review, admission receipts, and the queue's
  candidate and aggregate gates unchanged. Classification is not approval.

## Risks / Trade-offs

- Trusted main will not yet understand this mode on the config PR: select
  full checks. Validate positive routing with offline fixture tests first.
- The workflow also handles tags and dispatches: they always select full
  checks. No release trigger, test registry, or release script changes.
- A newer main makes a stack stale: keep full checks until rebased/reviewed.

## Migration Plan

Open one config PR and verify full fallback plus fixtures. No live canary or
merge in this task. A separately authorized canary must demonstrate fast-only
PR routing, one heavy candidate run, and the exact landed tree before rollout.
