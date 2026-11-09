## Context

The existing Spec Kit task list is organized by phase and user story. It has no explicit pull-request boundary. Release qualification already uses a separate source-bound workflow and is out of scope.

## Goals / Non-Goals

Keep one canonical task list. Define small, safe-to-land task sets and test a three-PR stack on synthetic code only. Do not activate a queue or change branch protections on OpenBenches.

## Decisions

- Ratify a vendor-neutral principle in the constitution; put the operating procedure and task-set metadata in the task template and repository guidance.
- Run fast checks on every member, including PRs with a non-main base. Run the combined integration check only on the genuine Mergify queue revision, on a GitHub-hosted runner without release access.
- In the pilot, target one serial batch of three members. Admit only reviewed, explicitly eligible heads. Do not turn on Graphite auto-merge or automatic Mergify queueing. Retain existing GitHub protections.

## Risks / Trade-offs

- Graphite's external queue handoff can be sequential. Test Mergify's recognition of the explicit same-repository dependency chain instead of assuming a Graphite stack implies a single batch.
- A batch can be recomposed or split. Set zero automatic retries and failure splits in the sandbox, and treat any partial or multi-run result as evidence rather than calling it a successful one-run pilot.
- App repository grants and organization-level bypasses are independent authority decisions. Do not widen an inherited ruleset or install an app on additional repositories.
