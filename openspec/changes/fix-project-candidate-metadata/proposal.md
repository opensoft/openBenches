# Proposal

## Why

The #250 project canary exposed duplicate integration after a third-party
candidate edit and after dequeue. Event-editor identity is not candidate
provenance, and the success-filtered historical list omitted an exact
completed run visible through candidate-specific lookup.

## What Changes

- Allow third-party `edited` events only after existing live Mergify creator,
  repository, exact snapshot and batch proofs succeed.
- Look up closed/dequeued candidate evidence by exact head SHA, without a
  server-side success filter; continue verifying success and all platform jobs.
- Add lifecycle and negative regressions, including the existing wrong-tree
  assertion follow-up. Publish one config PR, without merge or live admission.

## Capabilities

### New Capabilities

- `project-candidate-metadata`: editor-independent, proof-bound metadata routing.

### Modified Capabilities

None. The prior project-efficiency specification remains in its original
unarchived change; the published capability inventory has no project entry.

## Impact

Project policy helper, offline tests and delivery documentation only. No
workflow permissions/triggers, queue rules, release files, app access or tags.
Spec Kit implementation handoff: `specs/175-project-candidate-metadata/`.
