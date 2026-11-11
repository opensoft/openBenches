# Tasks: Docker / WSL Flight Recorder

## Phase 1: Foundations

- [X] T001 [O] Add deadline, parsing, freshness, privacy and retention tests — files: `scripts/tests/test-docker-wsl-flight-recorder.ps1` — verify: `pwsh -NoProfile -File scripts/tests/test-docker-wsl-flight-recorder.ps1`

## Phase 2: User Story 1 and 2

- [X] T002 [US1] [O] Implement bounded recorder, independent health and circuit latches — files: `scripts/docker-wsl-flight-recorder.ps1` — verify: `pwsh -NoProfile -File scripts/tests/test-docker-wsl-flight-recorder.ps1`
- [X] T003 [US2] [O] Add independently supervised installation and honest Status/Stop — files: `scripts/install-docker-wsl-flight-recorder.ps1`, `scripts/tests/test-docker-wsl-flight-recorder.ps1` — verify: `pwsh -NoProfile -File scripts/tests/test-docker-wsl-flight-recorder.ps1`

## Phase 3: User Story 3 and acceptance

- [X] T004 [US3] [O] Document experiment and verify installed non-disruptive recording — files: `docs/docker-wsl-diagnostics.md`, `specs/181-docker-flight-recorder/verification.md`, `specs/181-docker-flight-recorder/tasks.md` — verify: `pwsh -NoProfile -File scripts/install-docker-wsl-flight-recorder.ps1 -Action Status`

Dependencies: T001 -> T002 -> T003 -> T004. No parallel writer is needed. Future disruptive experiments remain runbook gates, not implementation tasks or authorization.
