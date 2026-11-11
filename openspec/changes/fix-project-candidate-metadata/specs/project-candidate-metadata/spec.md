# Project candidate metadata

## Purpose

Avoid duplicate project integration on authenticated candidate metadata while
retaining full checks when the candidate or its prior testing cannot be proven.

## ADDED Requirements

### Requirement: Metadata editor is not candidate provenance

Candidate `edited` events SHALL be eligible independently of their editor
only when live Mergify origin, repository, exact snapshot and existing batch
proofs succeed. Other actions SHALL retain their actor restrictions.

#### Scenario: Third-party metadata edit

- **WHEN** a third party edits a proven, unchanged Mergify project candidate
- **THEN** only the duplicate ordinary component integration is omitted

#### Scenario: Real or uncertain changes

- **WHEN** the creator, head, base, scope, receipts or current snapshot do not match
- **THEN** ordinary component integration runs in full

### Requirement: Closed and dequeued candidates require completed evidence

Closed draft metadata SHALL require a completed successful push run for that
exact workflow, candidate and branch, all expected jobs, unchanged policy,
and the original ordered batch proof, even when members remain open.

#### Scenario: Dequeued without landing

- **WHEN** a closed draft retains complete exact-candidate successful evidence
- **THEN** duplicate integration is omitted without treating its members as merged

#### Scenario: Missing or unsuccessful evidence

- **WHEN** run/job data are missing, failed, cancelled, skipped, wrong-head or unavailable
- **THEN** the classifier retains full component integration

### Requirement: Preserve independent safety gates

Queue admission, push/landing actor restrictions, full fallback output guards,
Wave behavior and release checks SHALL remain unchanged.

#### Scenario: Non-Mergify queue or landing push

- **WHEN** an ordinary actor pushes a queue-looking branch or main
- **THEN** candidate metadata eligibility does not authorize suppression
