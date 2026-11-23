# Implementation Plan: HTTPS Ubuntu Mirrors

## Summary

Normalize official Ubuntu sources in the shared Layer 0 immediately after its existing certificate-providing package bootstrap. Inherited family and bench installs then use verified HTTPS. Preserve the existing bootstrap, package choices, signing keys and source snapshot. Rebuild only the developer/system families and py/cloud/m365 branches needed by this migration.

## Technical Context

- Build system: existing Dockerfiles and Bash build wrappers.
- Patch: one bounded shell block in `base-image/Dockerfile`.
- Tests: Python standard-library fixture tests that execute the exact Dockerfile block in a disposable Python bench image.
- No new dependencies, data model, public interface or package pins.
- Host-local evidence stays outside the repository; use `MIGRATION_EVIDENCE_ROOT` to identify the operator's private receipts.

## Constitution Check

- One task set: HTTPS transport correction plus focused verification.
- No governance, CI workflow, submodule pin or source-backup branch change.
- Local source verification is distinct from a PR candidate, integration gate and merge; no landing is claimed.
- Current canonical WIP is preserved. The feature checkout is isolated from its operational snapshot.

## Design

The initial Ubuntu image has no CA bundle. Retain the existing signed-package bootstrap, then assert the bundle exists before changing official archive/security/ports schemes. Do not rewrite custom mirrors, comments, signing-key paths or package lists. GNU sed and POSIX shell are already available.

## Verification

1. Prove the fixture tests fail before implementation and pass after it.
2. Rebuild through the declared scripts, retaining the 100 GiB Windows reserve and separate ext4 data root.
3. Verify source schemes in the resulting images; audit actual testing tools and Chromium, not just installer exit status.
4. Run the three Wave checks, command/user/mount/reaping checks and repeated-start identity checks.
5. Recheck maintenance holds, source WIP and Desktop disk preservation.

## Governed invariants

- `base-image/Dockerfile` — shared package initialization and inherited image content; the patch does not alter selections or signing policy.

## Analysis

Requirements FR-001..FR-003 map to T001/T002; FR-004..FR-006 map to T003/T004. No uncovered requirement or constitution conflict was identified. No public contract or data-model change is needed.
