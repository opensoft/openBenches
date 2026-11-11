# Implementation Plan: Docker / WSL Flight Recorder

Date: 2026-11-11. Governing change: `openspec/changes/docker-wsl-flight-recorder/`.

## Updated diagnosis and scope

The prior chat plan becomes this executable plan. Healthy post-restart snapshots do not explain earlier freezes. Four hypotheses remain separate: dashboard/API polling overhead; WSL networking/transport stalls; real resource pressure versus cache; unreaped children versus blocked kernel threads. The Windows WSL watchdog and both CI tasks stopped with the same exit result while heartbeat files remained apparently healthy. Task Scheduler Operational history is disabled, so the historical initiator remains unknown.

Implement and activate non-disruptive evidence collection. Do not restart existing services, resume CI, replace benches, change memory/network/VPN settings, enable debug mode, upload bundles or migrate Docker incidentally.

## Technical Context

Windows-native PowerShell 7, .NET ProcessStartInfo.ArgumentList, CIM and Task Scheduler; Linux `/proc`, cgroup v2 and procps through bounded read-only probes. No new package dependency. Source files: `scripts/docker-wsl-flight-recorder.ps1`, `scripts/install-docker-wsl-flight-recorder.ps1`, `scripts/tests/test-docker-wsl-flight-recorder.ps1`, `docs/docker-wsl-diagnostics.md`. Windows-specific tests run in the declared Windows host runtime. Guest payloads are smoke-tested against the consuming benches.

## Constitution Check

The constitution file is a placeholder, not ratified policy. Concrete gates: preserve unrelated changes and sessions, no host-specific committed paths, feature worktree isolation, bounded output/retention, no secret-bearing raw logs, no automated recovery. All require tests and live verification.

## Design and phases

1. Fixture-first tests for deadlines, singleton exclusion, stale identity/heartbeat detection, cache accounting, process/thread classification, polling aggregation, rotation and privacy.
2. Sample every 30 seconds from Windows. Probe Docker API and WSL separately, inspect selected bench state, and rotate one bench accounting sample per cycle. Enumerate already-running WSL distributions first; never start a stopped Ubuntu. Never call Docker stats. On timeout persist a circuit latch; interrupted probes also latch after process replacement. Only an explicit ResetProbes operation while stopped clears these latches. An unkillable owned client stops collection rather than spawning replacements.
3. Record task state/results and external-watchdog freshness without restarting them. Self-status checks timestamp, PID and start time. Keep four 4 MiB sample files and twelve incident summaries. Emit aggregate API endpoint counts from a bounded log tail, never raw logs, arguments, environments or arbitrary error text.
4. Install into Windows local application data. Launch by an independent non-elevated scheduled task with at-logon and periodic supervision triggers. Verify ancestry, unchanged bench IDs and repeated fresh samples.
5. Completed the short dashboard-open / dashboard-closed / dashboard-reopened comparison on 2026-11-11 without quitting Docker. Observed polling stopped advancing after Close window and returned on reopening; API responsiveness and container identities were preserved. See `verification.md`. Sustained freeze causation remains unproven; sampled polling correlation is not a stability qualification.
6. During a real freeze preserve evidence and collect a local Docker diagnose bundle before a user-approved restart. Debug-mode reproduction and a WSL trace remain follow-up approval gates. Only then test networking/VPN, Kubernetes, resource limits, version changes or a disposable Linux Engine pilot, one variable at a time.

## Governed invariants

- `scripts/docker-wsl-flight-recorder.ps1` — privacy allowlist, latching and owned-client-only termination.
- `scripts/install-docker-wsl-flight-recorder.ps1` — native independent execution; no existing task/service mutation.
- `specs/181-docker-flight-recorder/` — separate installation, baseline and root-cause acceptance.

## Verification

Run fixtures, syntax checks and real Once sampling, then installed Watch sampling. Compare container IDs and validate singleton, retention, task ancestry, freshness and honest reporting of stopped external tasks. Record remaining gates in `verification.md`; a recorder installation does not solve or prove the freeze's root cause.
