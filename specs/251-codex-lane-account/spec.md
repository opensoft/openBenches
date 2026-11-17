# Feature Specification: Automated Codex lane account binding

**Feature Branch**: `251-codex-lane-account`
**Created**: 2026-11-17
**Status**: Accepted for implementation by the user's direct request.
**Input**: Fix launchers so automated Codex exec runs use the lane's selected account and cannot silently fall back to max001.

## User Scenarios & Testing
### User Story 1 - Pay with the selected account (Priority: P1)
An operator selects an account for a lane. Automated reviews and their children use that account.
Independent test: a fake provider records the selected identity and receives quoted task arguments intact.
Acceptance: stale default-account state is overridden; explicitly selecting max-001 remains supported.

### User Story 2 - Refuse unselected charges (Priority: P1)
A review with absent, unknown, missing or mismatched account credentials stops before provider execution.
Independent test: each invalid fixture exits nonzero with no fake-provider invocation.

### Edge Cases
Profile aliases; profile names absent from the other provider's registry; stale inherited home; API key environment; delegated children; new tmux child launch; existing active launcher modifications.

## Requirements
- FR-001: Automated work MUST use the lane's selected account.
- FR-002: Missing selection or matching credentials MUST stop before provider execution.
- FR-003: An inherited API key MUST NOT override selected subscription credentials.
- FR-004: Main and child work MUST retain the same selected identity.
- FR-005: Argument boundaries, exit codes and unrelated launcher behavior MUST be preserved.

## Success Criteria
All valid fixtures execute with the selected identity; every invalid fixture makes zero provider calls; live installation readback matches tested account-binding changes; no credentials or running sessions change.

## Assumptions
The selected Codex profile takes precedence for explicit Codex launches. Claude lane launches reset their child selection to their own selected profile. Unavailable cross-provider profiles are refused when automated Codex is requested.
