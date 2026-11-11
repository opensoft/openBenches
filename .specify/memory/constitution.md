<!--
Sync Impact Report
Version: unratified template -> 1.0.0 (initial adoption)
Principles added: One Task Set per Pull Request; Validate the Candidate Before Landing.
Sections added: Development Workflow; Governance.
Templates updated: .specify/templates/tasks-template.md; .specify/templates/plan-template.md.
Feature spec template remains compatible: user stories and acceptance criteria retain their existing shape.
Guidance added: docs/task-set-delivery.md.
Deferred placeholders: none.
-->

# OpenBenches Constitution

## Core Principles

### I. One Task Set per Pull Request

Every Spec Kit implementation PR MUST deliver exactly one named task set: one
reviewable outcome, its related task IDs, and a focused verification command.
A task set MUST be testable against its declared parent. Tests and compatibility
changes needed for that set MUST accompany it. An intermediate landing MUST
leave the target branch usable; incomplete behavior MUST remain inactive.

### II. Validate the Candidate Before Landing

Each PR MUST pass its fast checks and applicable review on the current head
before enqueue. The combined candidate MUST pass the required integration check
before landing. Tests on an earlier head or after the merge do not satisfy these
gates. Higher-risk changes retain any additional checks the repository requires.

## Development Workflow

Use one Spec Kit task list and split a set when it needs more than one independent
review decision. Record parent dependencies in the task list and PRs. Keep
ordinary pre-merge CI separate from release qualification and publication.
See [task-set delivery](../../docs/task-set-delivery.md) for the procedure.

## Governance

Changes to these principles require maintainer approval, a version update, and
synchronized planning guidance. A new or expanded principle bumps the minor
version; incompatible changes bump the major version; clarifications bump the
patch version. Reviewers check that the PR maps to one set and that required
checks match its current head. Any exception must be explicit and scoped; this
constitution does not grant queue, ruleset, or release bypass authority.

**Version**: 1.0.0 | **Ratified**: 2026-11-09 | **Last Amended**: 2026-11-09
