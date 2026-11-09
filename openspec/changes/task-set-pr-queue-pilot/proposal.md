## Why

Make stacked Spec Kit work reviewable in small units without running the full integration suite on every edit. Keep the full combined check before landing.

## What Changes

- Adopt one task set per PR in the OpenBenches constitution and Spec Kit templates.
- Define a pilot that uses Graphite for stacking, GitHub Actions for two CI stages, and Mergify for landing.
- Keep the pilot isolated from OpenBenches release workflows, protected QA, existing benches, and other repository settings.

## Capabilities

### New Capabilities

- `task-set-delivery`: Reviewable Spec Kit slices and a separate pre-merge integration gate.

### Modified Capabilities

None.

## Impact

Project governance and Spec Kit templates in OpenBenches. The live experiment is limited to an approved private non-release sandbox with synthetic source and GitHub-hosted CI. App access, authorization, and any ruleset changes require separate scope approval.
