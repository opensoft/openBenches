# Plan: Park handoff safety

Status: draft commissioned implementation

## Summary

Implement [the governed change](../../openspec/changes/fix-park-handoff-integrity/proposal.md) in two task-set PRs, preserving existing public formats and merge policy.

## Technical Context

Bash 3.2-compatible shared templates, Git 2.34.1-compatible commands, Python standard-library manifest writer. Tests are the existing disposable Git fixture suites. Source files are owned by workBenches; no bench image build or live workspace write is needed.

## Constitution Check

One set per PR, each with related tests and a focused command. SET-02 names SET-01 as predecessor and immediate base. CI/review bind exact heads; no queue bypass or pilot scope expansion. The merged candidate and release gates are distinct from source validation. Owner ratification/archive is not invented.

## Design

[Research](research.md) and [data model](data-model.md) define full-leg preflight and current-file partial merge. Use canonical common-directory and worktree-root comparison before requiring the recorded branch. Carry partial selected-branch intent into the writer so retry uses the refreshed unselected records. Keep full park behavior unchanged.

## Analysis and validation

FR-001/002 map to SET-01 refusal and no-write fixtures. FR-003/004 map to SET-02 subset, gone-feature, retry, and full-reconciliation fixtures. The complete feature, compatibility and bootstrap suites catch shared regressions. Downstream openMFA compares exact copied shared bytes and reruns its fixture suite and CI. Follow the single [task list](tasks.md).

## Delivery

Use gh-stack for ordinary dependent PR authoring. No registered stack, Mergify queue admission, ruleset change, main-branch push, fleet installation or release is part of this task. Record upstream branch/PR/commit provenance in the updated openMFA candidate. Preserve its unrelated local creation/resume deviations.
