# Feature Specification: HTTPS Ubuntu Mirrors

**Feature Branch**: `253-https-ubuntu-mirrors`

**Created**: 2026-11-23

**Status**: Approved for implementation

**Input**: Apply the HTTPS mirror fix, rebuild the three selected benches, start them through Wave, and preserve host data, rollback storage and maintenance holds.

## User Scenarios & Testing

### User Story 1 - Complete the declared tool installation (Priority: P1)

An operator rebuilding a bench gets its declared software without repeated failures on unencrypted Ubuntu mirror requests.

**Independent Test**: After the existing certificate bootstrap, official Ubuntu mirror entries use verified HTTPS and retain their existing paths, suites, components and signing keys.

**Acceptance Scenarios**:

1. Given default Ubuntu mirror entries, when the shared base is built, subsequent package operations use HTTPS.
2. Given an already encrypted or unrelated repository, its configuration remains unchanged.
3. Given no optional source-list files, normalization succeeds without creating repositories.

### User Story 2 - Resume the three benches safely (Priority: P2)

The operator can open the rebuilt py, cloud and Microsoft 365 benches using the existing Wave launcher.

**Independent Test**: Each launcher check succeeds as brett UID 1000, using the existing host projects and an init process.

**Acceptance Scenarios**:

1. Each selected bench starts with its rebuilt personalized image and retained host binds.
2. Repeated launcher checks reuse its existing container.
3. CI and watchdog remain paused; no host data, volume or Desktop rollback disk is removed.

### Edge Cases

- A vanilla upstream image has no certificate trust bundle before the existing signed-package bootstrap.
- Legacy source lists, deb822 source files, ARM ports, missing globs and repeated normalization.
- A download failure must remain visible and must not be described as fully verified software.

## Requirements

- **FR-001**: Convert only official archive, security and ports Ubuntu mirror URL schemes after trusted certificates are installed.
- **FR-002**: Preserve package selection, repository paths, suites, components and signature verification; do not disable TLS verification.
- **FR-003**: Cover legacy and deb822 sources, missing optional files, nonmatching repositories and idempotence.
- **FR-004**: Rebuild the shared dependencies and the three personalized benches using declared tooling.
- **FR-005**: Verify Wave startup, identity, host projects, command availability and process reaping before reporting readiness.
- **FR-006**: Preserve host data, Desktop rollback storage, source WIP and CI/watchdog holds.

## Success Criteria

- **SC-001**: All transport fixture tests pass and no unrelated repository text changes.
- **SC-002**: All three selected benches pass the declared Wave check as the intended user.
- **SC-003**: The previously skipped testing utilities and browser are checked in the rebuilt Python image.
- **SC-004**: No host data or rollback storage is deleted, and all five maintenance tasks remain disabled.

## Assumptions

- This is an implementation-only correction to existing layered-build behavior, consistent with `specs/002-cascade-image-validation/spec.md`; no new layer, package policy or runtime interface is introduced.
- The existing first signed-package installation provides certificate trust and remains the bootstrap boundary.
- A PR merge and OS reboot require separate authorization and are not included here.
