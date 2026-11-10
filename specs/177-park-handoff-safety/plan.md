# Plan: Park handoff safety

Status: draft commissioned implementation

## Summary

Implement [the governed change](../../openspec/changes/fix-park-handoff-integrity/proposal.md) in four ordered task-set PRs, including fresh resume and pending-publication findings, preserving existing public formats and merge policy.

## Technical Context

Bash 3.2-compatible shared templates, Git 2.34.1-compatible commands, Python standard-library manifest writer. Tests are the existing disposable Git fixture suites. Source files are owned by workBenches; no bench image build or live workspace write is needed.

## Constitution Check

One set per PR, each with related tests and a focused command. SET-02 names SET-01 as predecessor and immediate base; SET-03 names SET-02; SET-04 names SET-03. CI/review bind exact heads; no queue bypass or pilot scope expansion. The merged candidate and release gates are distinct from source validation. Owner ratification/archive is not invented.

## Design

[Research](research.md) and [data model](data-model.md) define full-leg preflight and current-file partial merge. Use canonical common-directory and worktree-root comparison before requiring the recorded branch. Carry partial selected-branch intent into the writer; preserve the existing Git three-way rebase/refusal path for push retries. Verify origin before the existing-worktree resume shortcut, refusing failed fetches. Keep full park behavior and safe repeat resume unchanged.

## Analysis and validation

FR-001/002 map to SET-01 refusal and no-write fixtures. FR-003/004 map to SET-02 subset, gone-feature, retry, and full-reconciliation fixtures. FR-005 maps to SET-03 changed/unverifiable-origin refusals and repeat resume. FR-006 maps to SET-04 unavailable-origin retry and exhausted-push fixtures. The complete feature, compatibility and bootstrap suites catch shared regressions. Downstream openMFA compares exact copied shared bytes and reruns its fixture suite and CI. Follow the single [task list](tasks.md).

## Delivery

Use gh-stack for ordinary dependent PR authoring. No registered stack, Mergify queue admission, ruleset change, main-branch push, fleet installation or release is part of this task. Record upstream branch/PR/commit provenance in the updated openMFA candidate. Preserve its unrelated local creation deviation; the shared resume correction supersedes its earlier local resume patch.
