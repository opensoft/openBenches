# Proposal: Ignore already-merged Wave metadata events

## Why

The efficiency canary in #250 passed fast admission and the combined merge
gate, but Mergify's metadata edits restarted full CI after the upper PR merged.

## What Changes

- Add a separate trusted classification for edited metadata on an already
  merged, opted-in Wave PR at the exact event head.
- Skip the four redundant workstation jobs for that explicit result only.
- Preserve Wave-only open-PR eligibility and full fallback on uncertain input.

## Capabilities

### New Capabilities

- `merged-wave-metadata-ci`: suppress redundant post-merge metadata work.

### Modified Capabilities

None.

## Impact

Workstation Setup selection, stack-policy fixtures, and maintainer docs.
No live canary, queue changes, app access, rulesets, or release changes.
Spec Kit handoff: `specs/173-wave-merged-metadata/`.
