## ADDED Requirements

### Requirement: Authors use the official GitHub CLI extension

The OpenBenches runbook SHALL use gh-stack for local branch ordering and pushes,
without requiring Graphite authentication. It SHALL publish ordinary pull
requests, with each upper member targeting its predecessor's head and declaring
`Depends-On: #N`.

#### Scenario: Author prepares a two-member stack

- **WHEN** the author pushes both gh-stack branches and opens their dependent PRs
- **THEN** Mergify can recognize the same-repository branch chain without a GitHub stack registration

### Requirement: Authoring does not alter queue policy

Mergify SHALL remain the only queue for this rollout. The change SHALL NOT modify
existing fast CI, heavy CI, app access, rulesets or release workflows.

#### Scenario: A remote rule refuses a branch rewrite

- **WHEN** a restack would require a prohibited non-fast-forward push
- **THEN** the author uses fresh branches and revalidates the replacement PRs rather than bypassing the rule
