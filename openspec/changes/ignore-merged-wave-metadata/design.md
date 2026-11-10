# Design

## Context

The full fallback is safe but unnecessary when GitHub confirms an opted-in
Wave PR has already merged at the head named in a delayed edited event.

## Goals / Non-Goals

Suppress only redundant workstation jobs for that lifecycle case. Do not
short-circuit real changes on open PRs or weaken merge gates.

## Decisions

- Keep trusted-main execution. Add `merged_metadata` alongside `wave_only`;
  do not misrepresent a merged PR as an eligible open Wave stack member.
- Require an `edited` PR event, matching positive PR number and full head SHA,
  same-repository head/base, the dedicated Wave prefix and explicit opt-in,
  and fresh API readback showing closed, merged, with a valid merge commit,
  targeting main. Read the complete changed-file list and require only
  modifications within the three Wave paths. The event can predate the merge: only live API confirmation
  qualifies it.
- A successful classifier must explicitly return either eligible result to
  omit jobs. Missing fields, API errors, closed-unmerged PRs, open PRs, other
  event actions, or changed heads cannot qualify through the lifecycle path.
- Leave the existing open-PR classifier, fast CI and candidate gates unchanged.

## Risks / Trade-offs

Trusted main lacks the new result before merge, so the config PR takes full
checks. Validate the new lifecycle path in offline fixtures only. A separately
authorized repeat canary is still needed after review and merge.

## Migration Plan

Open a config PR, verify full fallback and exact-head review, and stop before
merge or live admission. Revert through an ordinary PR if needed.
