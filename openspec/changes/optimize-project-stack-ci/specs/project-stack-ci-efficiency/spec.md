# Project stack CI efficiency

## Purpose

Avoid duplicate project integration across a reviewed stack's complete
lifecycle while retaining coverage for all uncertain and mixed inputs.

## ADDED Requirements

### Requirement: Project-specific eligibility

Trusted policy SHALL restrict eligibility to explicit project opt-in and the
existing two-file project scope, with current same-repository PR chains or
verified merged same-head metadata. Wave eligibility SHALL NOT suppress project CI.

#### Scenario: Wrong scope or stale data

- **WHEN** a PR changes unrelated files, lacks project opt-in, or cannot be verified
- **THEN** project component CI runs in full

### Requirement: Push suppression requires exact evidence

Author pushes SHALL require head-bound opt-in and exact Git scope.
Candidate pushes SHALL require verified queue admission. Landing pushes SHALL
match an ordered prefix of an already-successful project candidate, including
its base, original heads, trees and GitHub merge records.

#### Scenario: Actor without proof

- **WHEN** a Mergify-looking push lacks matching successful candidate evidence
- **THEN** project CI runs in full

### Requirement: Preserve integration and safe fallback

The combined candidate SHALL retain the full component fixtures, syntax and
platform checks. Classifier errors, missing outputs, tags and ordinary changes
SHALL NOT suppress existing checks.

#### Scenario: Incomplete platform result

- **WHEN** any required project matrix job fails, is cancelled or is skipped
- **THEN** the existing aggregate cannot authorize landing
