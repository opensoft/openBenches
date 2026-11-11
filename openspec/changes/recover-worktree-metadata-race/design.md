# Design

## Context

The failed #318 candidate ran Git 2.56.0 and PowerShell 7.6.9. Git's
worktree_lock_reason checks file existence before reading the locked marker;
concurrent worktree creation can remove it in that interval and cause exit 128.
See the recorded #250 job and [upstream Git v2.56.0 worktree.c](https://github.com/git/git/blob/v2.56.0/worktree.c#L285-L303).

## Goals / Non-Goals

Recover that bounded read race in PowerShell lookup, not arbitrary process or
filesystem failures. Do not retry writes, loosen parsing, skip tests, change
Bash discovery, alter the CI roster or run/merge another canary.

## Decisions

- Use a small nested snapshot reader inside lookup for both NUL and legacy
  formats. At most three attempts, 100ms apart; fresh process output replaces
  the previous attempt. No recovery configuration knob.
- Match exit 128 plus the whole single-line C-locale missing
  worktrees/<id>/locked diagnostic. Other errno/path/exit combinations return
  immediately to the existing error handling.
- Set LC_ALL=C only on the Git discovery child process so the diagnostic match
  does not depend on the user's locale. Do not change the parent environment.
- Preserve exit-129-only legacy fallback and every candidate validator.
- Reproduce via deterministic fault injection at the existing lookup boundary,
  proving red before the fix. Add success, exhaustion, partial-output and error
  exclusion fixtures; keep the real eight-creator concurrency test unchanged.

## Risks / Trade-offs

A bounded retry cannot guarantee progress under indefinite churn; after the
bound it must throw. Fault injection is deterministic boundary reproduction,
not a claim of forcing the exact native TOCTOU on every operating system.
Validate full Linux/Windows suites and repeat real concurrency stress.

## Migration Plan

One ordinary fix PR, not an allowlisted helper stack member. Require normal
full CI and request fresh Codex review (the previous waivers do not carry over).
Propose a new two-PR test-only canary after an authorized merge and fresh base,
receipts/review, one heavy run and landed-tree audit. Do not enqueue now.
