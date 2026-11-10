# Implementation Plan

## Technical Context

Python standard library for catalog projection, identity binding, and atomic state preparation. PowerShell for native Windows package lifecycle. The declared `py-bench` runs fixture tests; native Windows validates Windows-only behavior. Source files use runtime-resolved paths.

## Constitution Check

Use the existing per-family metadata contract, preserve credential isolation and shared history links, avoid live database changes, and retain unknown account preferences. Approved scope comes from the user's request. No runtime setting is copied between packages.

## Governed invariants

- `scripts/codex-project-state.py` — family and runtime isolation, projected data allowlist, backups and concurrency.
- `scripts/codex-desktop.ps1` — selected Windows package only; no WSL execution or runtime-setting mutation.

## Structure and sequence

T001 implements the pure state model and fixture tests. T002 adds offline CLI and native launch wrapper. T003 integrates setup and documents the launch boundary. T004 validates, installs host-local tooling, and restores the current profile with observable API evidence.

## Verification

Run `python3 devcontainer.test/test-codex-project-state.py` inside the declared bench. Run native Python fixtures and PowerShell parsing on Windows. Compare backups and account projections, then check the app APIs after relaunch. No speculative root deduplication or SQLite rebuild.
