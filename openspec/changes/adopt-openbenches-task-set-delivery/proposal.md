# Proposal

## Why

The live #250 smoke tests found that local skill installation works, but a clean
OpenBenches clone does not receive the skill assets or adoption pointers.

## What Changes

- Track unchanged portable skill copies for Codex and Claude alongside their
  repository instruction pointers.
- Make Claude import AGENTS.md rather than duplicate the repository process.
- Check asset parity, clean-source availability and active-plan preservation.

## Capabilities

### New Capabilities

- `openbenches-workflow-adoption`: discover the shared workflow in a clean clone.

### Modified Capabilities

None. The shared workflow, queue allowlists and bootstrap behavior are unchanged.

## Impact

Only repository instruction/assets, source-adoption tests, additive ordinary CI
trigger coverage and documentation. Spec Kit handoff: feature 180. No active-plan,
bench, release, app-access, ruleset, model-profile or tag changes.
