# Feature Specification: Docker / WSL Flight Recorder

**Feature Branch**: `181-docker-flight-recorder`
**Created**: 2026-11-11
**Status**: Approved for scoped implementation by the current user request
**Input**: Update and implement the existing Docker diagnostic plan.

## User Scenarios & Testing

### User Story 1 - Preserve a freeze's evidence (Priority: P1)

The operator needs timestamped observations from before a freeze, without losing working sessions or worsening a stuck system.

**Independent Test**: Simulate a hung diagnostic client; later evidence remains readable and no further client is launched on the affected path.

**Acceptance Scenarios**:
1. Given a healthy runtime, when recording starts, then repeated observations appear without changing existing workloads.
2. Given a hung probe, when its deadline expires, then only its diagnostic client is stopped and that probe path is latched off.

### User Story 2 - Interpret resources and stale monitoring honestly (Priority: P1)

The operator needs to distinguish cached files, real application memory, unreaped processes, blocked threads, and dead monitoring.

**Independent Test**: Cache-heavy and stale-heartbeat fixtures retain separate accounting and report stale/stopped rather than healthy.

**Acceptance Scenarios**:
1. Given cache-heavy memory, when a sample is reviewed, then cache and anonymous memory are separate.
2. Given an old healthy heartbeat with no daemon, when status is requested, then it reports stopped/stale.

### User Story 3 - Compare diagnostic hypotheses (Priority: P2)

The operator needs labeled evidence windows for dashboard-open versus dashboard-closed tests and explicit approval gates for disruptive follow-up.

**Independent Test**: Mark two phases and compare recent polling counts without saving raw Docker log content.

### Edge Cases

Missing tools, stopped/missing benches, malformed or rotated logs, concurrent recorder starts, unkillable clients, stale PID reuse, unavailable performance counters and task history, workstation logoff, and later manual recorder restart.

## Requirements

- **FR-001**: Local recording must preserve all unrelated workloads and configuration.
- **FR-002**: Each external probe must have a deadline and one owned client; timed-out or interrupted paths remain latched across process replacement until explicit probe reset while stopped.
- **FR-003**: Evidence must separate resource usage, runtime reachability, process hygiene and task freshness.
- **FR-004**: Retention must be bounded; no raw arguments, environments, credentials or application logs may be collected.
- **FR-005**: The recorder must survive the agent's exit and expose its own freshness and process identity.
- **FR-006**: Experimental phase markers must be fixed labels rather than arbitrary sensitive free text.

### Key Entities

Sample, probe result, task observation, phase marker, recorder identity and incident transition.

## Success Criteria

- **SC-001**: A hung probe is classified within 10 seconds plus at most 2 seconds for owned-client termination.
- **SC-002**: Stale/dead monitoring is never presented as current healthy monitoring in fixture and live status tests.
- **SC-003**: Multiple real samples are retained with unchanged bench identities and uninterrupted user jobs.
- **SC-004**: Sample retention stays within four bounded ring files plus twelve incident summaries.

## Assumptions

Native Windows execution is required. Initial recording is authorized; closing the Docker dashboard for the A/B test will be coordinated with the operator. Restarting Docker/WSL, resuming CI, replacing m365-bench, changing VPN/networking or migrating engines is not implied by this request.
