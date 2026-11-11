# Docker / WSL diagnostic runbook

The implementation plan is [feature 181](../specs/181-docker-flight-recorder/plan.md). This records evidence; it does not automatically repair Docker or prove its root cause.

## Installation and status

Use native standalone Windows PowerShell 7, not a WSL terminal or an agent-bundled executable:

```powershell
pwsh -NoProfile -File scripts/tests/test-docker-wsl-flight-recorder.ps1
pwsh -NoProfile -File scripts/install-docker-wsl-flight-recorder.ps1 -Action Install
pwsh -NoProfile -File scripts/install-docker-wsl-flight-recorder.ps1 -Action Status
```

The installer creates only `workBenches Docker WSL Flight Recorder`, under the current interactive user with Limited privilege. Its task launches a Windows-local source copy independently of the agent. At-logon and one-minute supervision triggers use IgnoreNew, with an exclusive state-file lock as a second overlap guard. It does not enable/resume any existing watchdog or CI task. Logoff/sign-in recovery remains a separate live acceptance gate.

Runtime files are under `$env:LOCALAPPDATA/workBenches/docker-wsl-diagnostics/`; evidence is in its `state/` directory. `status.json` is the latest sample, `samples.jsonl` plus three rotations retain history, and `incident-*.json` retain twelve issue transitions. Source SHA-256 is reported by installer Status. The recorder samples every thirty seconds and rotates one selected bench per cycle; every bench sample carries its own timestamp. `collector_state=current` means the recorder is alive and fresh; `health=degraded` can instead mean the external CI/watchdog tasks are stopped, not that Docker has failed.

Records contain allowlisted metrics, identity/state metadata, separate process-leader zombie and blocked-thread counts, cache/anonymous/kernel memory, and recent aggregate polling counts. They exclude arguments, environments, credential contents, raw application logs, raw Docker log lines and packet contents. Routine collection never calls Docker's stats endpoint. Treat retained metadata as private operational evidence nonetheless; nothing is uploaded automatically.

## Bounded probes and rollback

External probes have an eight-second deadline by default. Only the owned diagnostic client can be terminated, never an entire process tree. A timeout or interrupted probe persists a circuit latch so automatic process replacement cannot continually spawn guest work into a wedged kernel. Other independent evidence can continue. Missing data is not a successful probe.

Both redirected streams are drained through fixed buffers, with at most 64 KiB of stdout retained transiently and no stderr retained. Excess output is `output-limit`; incomplete reads are `output-incomplete`. Missing required guest metrics are `metrics-unavailable`, even after exit zero. Probe cleanup does not depend on successful disk writes; a persistence failure stops further client submission (`collection-stopped`) and retains the interrupted-probe marker. Guest commands use each distribution/container's configured identity, not a host-specific username.

The recorder first enumerates already-running WSL distributions. It skips a stopped Ubuntu rather than starting it. For a fully quiet offline maintenance window, stop this recorder too using the command below, alongside the existing watchdog/CI drain procedure. No live shutdown was used to test this guard; stopped-name and Windows encoding fixtures cover it without interrupting workloads.

```powershell
pwsh -NoProfile -File scripts/install-docker-wsl-flight-recorder.ps1 -Action Stop
```

Stop disables/stops only the recorder's scheduled task, preserving all evidence. After inspecting a failure and confirming it is safe to probe again, use the installed copy while the recorder is stopped:

```powershell
$installed = Join-Path $env:LOCALAPPDATA 'workBenches/docker-wsl-diagnostics/docker-wsl-flight-recorder.ps1'
pwsh -NoProfile -File $installed -Mode ResetProbes
pwsh -NoProfile -File scripts/install-docker-wsl-flight-recorder.ps1 -Action Start
```

Do not reset latches blindly while WSL/kernel work remains blocked. A client timeout does not prove a guest process has exited. Stopping the recorder is not a Docker/WSL recovery action.

## Dashboard A/B experiment

1. Keep bench and CI workloads unchanged. Observe the Docker Containers dashboard and mark `dashboard-open` with the installed script's `-Mode Mark -Phase dashboard-open`.
2. Retain at least two fresh samples. Close only the dashboard window's **Close window** control, not Docker's Quit action. Verify Docker API and existing container IDs remain unchanged. Mark `dashboard-closed`.
3. Retain at least two further samples, reopen the existing dashboard and mark `dashboard-reopened`. Keep the running-only filter and all other settings unchanged across the comparison.
4. Compare aggregate polling and API latency only when the polling window timestamps fall inside the corresponding observed UI phase. A tail can include older entries; unavailable data is not zero requests. Rotated log tails are samples, not complete request totals. A minimized window is not the same condition as a closed window.
5. Repeat under comparable workload before attributing a freeze to polling. Closing a window might not stop a background Desktop client, so a negative test does not completely exonerate Desktop.

## Real failure capture and later gates

- Preserve local ring and incident records before restarting anything. Correlate Windows commit/available RAM and paging, guest available RAM/pressure, cache accounting, task disappearance, zombie leaders, blocked threads and wait channels.
- Docker API failure with responsive WSL differs from WSL transport failure with responsive Docker exec. High load and low CPU can indicate blocked kernel work. A zombie leader with blocked live threads is not necessarily an absent-reaper defect.
- Collect `docker desktop diagnose` locally at the failure; do not add `--upload` without approval. Separately coordinate a bounded debug-log reproduction and Microsoft WSL trace. Debug logging is not enabled by recorder installation. Full VM dumps can be very large and sensitive.
- Task Scheduler Operational history was disabled at the initial diagnosis. Current task metadata alone cannot establish who caused an earlier termination. Enabling that Windows log requires a separately coordinated administrative action; do not manufacture historical events.
- Container reaper activation, workload/PID limits, Kubernetes changes, VPN/MTU/networking changes, version rollback and engine migration are separately approved experiments. Never change several variables together or restart live work as a diagnostic shortcut.
- A Linux Engine pilot must be isolated, with a disposable bench and explicit data/mount/CI/Wave migration and rollback checks. Do not point two daemons at the same Docker data directory. Engine inside WSL removes Desktop but not the WSL kernel/transport dependency.

## Primary references

- [Docker daemon logs and debug logging](https://docs.docker.com/engine/daemon/logs/)
- [Docker Desktop diagnose](https://docs.docker.com/reference/cli/docker/desktop/diagnose/)
- [Microsoft WSL troubleshooting](https://learn.microsoft.com/en-us/windows/wsl/troubleshooting-guide)
- [Docker WSL backend](https://docs.docker.com/desktop/features/wsl/)
- [Linux wait and zombie semantics](https://man7.org/linux/man-pages/man2/wait.2.html)
