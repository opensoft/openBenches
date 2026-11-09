## ADDED Requirements

### Requirement: PR fast check tests the immediate base

The fast check SHALL identify the PR head, immediate base and tested merge
revision. It SHALL fail if the checkout or merge parents do not match.

#### Scenario: Upper member targets a feature branch

- **WHEN** GitHub supplies a merge revision of the upper member and its immediate base
- **THEN** the fast check verifies the revision and runs without requiring the base to be main

### Requirement: The heavy check tests the exact queue candidate

The heavy check SHALL run only on Mergify queue pushes in OpenBenches, on a
GitHub-hosted runner with read-only permissions and no publishing. It SHALL
reject a stale, empty, or out-of-scope candidate before integration tests.

#### Scenario: Approved canary stack enters the queue

- **WHEN** the authorized Mergify actor pushes a candidate based on main and within the canary path allowlist
- **THEN** one integration job tests the combined revision and records its commit and tree

#### Scenario: The queue candidate does not match the allowed scope

- **WHEN** the candidate contains a release or workflow path, or is not based on current main
- **THEN** the heavy gate fails and cannot authorize landing

### Requirement: Bootstrap leaves existing release and app state unchanged

The bootstrap SHALL preserve current CI, app access, branch rules and release
automation. Queue activation and any permissions change require separate approval.

#### Scenario: The bootstrap PR is opened

- **WHEN** the additive CI change is submitted for review
- **THEN** no release workflow, release ref, or repository access is changed
