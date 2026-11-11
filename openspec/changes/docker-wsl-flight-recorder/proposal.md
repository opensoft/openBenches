## Why

Intermittent Docker Desktop / WSL freezes lose their evidence when services are restarted. A healthy post-restart snapshot cannot distinguish Windows memory pressure, Linux cache, WSL transport failure, daemon failure, task termination, or process-reaping defects.

## What Changes

- Add an opt-in Windows-native, bounded, local-only flight recorder and installer.
- Record independent Docker / WSL / bench probes, cache-aware memory accounting, zombie and blocked-thread counts, scheduled-task state and freshness, and bounded Docker API polling summaries.
- Preserve rotating samples and failure transitions without restarting anything, killing user jobs, enumerating interfaces, or uploading diagnostics.
- Update the diagnostic plan with the dashboard A/B experiment and explicit gates for later debug logging, runtime changes, and migration.

## Capabilities

### New Capabilities

- `docker-wsl-diagnostics`: bounded, non-disruptive evidence collection and honest freshness reporting.

### Modified Capabilities

None. Existing launchers, images, runner acceptance and watchdog behavior remain unchanged.

## Impact

New Windows PowerShell 7 tooling under `scripts/`, focused tests, a runbook, and one Speckit feature. Host-local output stays outside Git. Implementation is authorized by the user's request to update and implement the diagnostic plan; disruptive experiments remain explicit approvals. Speckit handoff: `specs/181-docker-flight-recorder/`.
