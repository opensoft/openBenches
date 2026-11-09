## Why

Use GitHub's maintained stack-authoring CLI instead of a separate Graphite login
for the OpenBenches 1.7 rollout (#250).

## What Changes

- Author, inspect and push stack branches with the official gh-stack extension.
- Create ordinary same-repository PRs with explicit bases and dependency markers.
  Do not register a GitHub stack object: Mergify documents that this would require
  a ruleset exemption.
- Keep Mergify batching and merging, both CI stages, the existing rulesets,
  release workflows and all app permissions unchanged.

## Capabilities

### New Capabilities

- `gh-stack-authoring`: GitHub CLI authoring for Mergify-compatible PR chains.

### Modified Capabilities

None.
