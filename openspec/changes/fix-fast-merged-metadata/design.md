# Design

## Context

See proposal.md. The existing merged-scoped metadata policy is already used by
ordinary integration classification. Fast CI currently checks out the event's
merge immediately, so an obsolete retarget merge fails its exact-parent check.

## Goals / Non-Goals

Recognize only provable edited metadata after landing. Do not validate stale
trees as source evidence, relax open-PR parent checks, or affect heavy CI.

## Decisions

Check out trusted main first and run a read-only, fail-closed classifier with
the Actions token. Only a live merged, same-head scoped PR with a complete
modified-file allowlist produces `merged_metadata=true`. In that case report
metadata-only success without checking out or testing the stale event merge.
Otherwise check out the exact event SHA and run the existing checks unchanged.
Do not suppress every edited event or accept ancestry instead of exact parents.

## Risks / Trade-offs

- API unavailability retains validation and may retain the old noisy failure.
- A PR cannot activate its own metadata exemption: the classifier comes from main.
- No source qualification is claimed for metadata-only processing.
