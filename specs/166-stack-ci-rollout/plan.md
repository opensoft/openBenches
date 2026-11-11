# Plan: OpenBenches stack CI bootstrap

Use two GitHub-hosted workflows with different event sources and check names.
Gate the heavy checkout on the Mergify actor and temporary branch; verify the
candidate SHA, current-main ancestry and path allowlist. Reuse the existing
non-release Spec Kit integration suites. Limit the prepared queue to manually
admitted canary stacks and leave current protections intact.

The rollout issue tracks live Graphite authentication, app authorization,
candidate membership, and positive and negative queue tests separately.

Authoring decision superseded by [gh-stack authoring](../167-github-native-stack-ci/tasks.md):
use the official GitHub CLI extension and ordinary dependent PRs. The Mergify
queue, candidate checks, and outstanding live acceptance are unchanged.
