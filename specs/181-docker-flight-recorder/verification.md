# Verification: Docker / WSL Flight Recorder

Date: 2026-11-11, America/La_Paz. Branch: `181-docker-flight-recorder`.

## Completed gates

- Native Windows fixture suite: **55 checks passed** after PR review. Includes exact owned-client timeout/termination, persistent interrupted-probe latches, singleton exclusion, stale/PID-reuse rejection, cache versus anonymous memory, leader zombies versus blocked threads, phase-window isolation, bounded rotation, privacy allowlists, installer constraints, and exact-name/encoding/stopped-distribution guards. Additional regressions cover bounded stdout/stderr, cleanup despite persistence failure, unhealthy fresh watchdogs, full-sample missing/valid metric payloads, configured identities, unique incident issues and concurrent Windows state replacement. A scoped Windows fixture CI job now exercises this suite without installing tasks or using live Docker.
- OpenSpec strict validation passed. Speckit prerequisite resolution selected this feature. Cross-artifact analysis covered six functional requirements and four acceptance outcomes across four implementation tasks, with no critical inconsistency. The repository constitution remains an unratified placeholder; concrete safety rules were applied instead of inventing a constitution.
- Initial installed source matched the tested implementation. Subsequent PR-review amendments require their own fixture and installed-source hash readback; installer Status reports the current SHA-256 rather than relying on this historical receipt.
- Recorder runs from Windows-local storage on standalone PowerShell 7. Native process ancestry is `pwsh.exe -> svchost.exe`, outside the agent process tree. Task uses Limited privilege, IgnoreNew, at-logon and one-minute periodic supervision triggers.
- Multiple real samples were retained at approximately thirty-second intervals, including all three selected bench accounting samples. Docker/WSL probes succeeded; Windows performance counters were available after correcting an overly short initial CIM timeout. Missing counters remain explicitly unavailable, not zero.
- Supervision fault test stopped only the new recorder while no probe was in flight, at approximately 18:01:19. Status immediately reported **stopped** and exited nonzero. Without manually starting it, the task's periodic trigger restarted it at approximately 18:02:04, with a different PID and independent svchost ancestry. Fresh samples resumed within about 45 seconds. Existing services/tasks were not controlled by this test.
- Original py-bench, cloud-bench and m365-bench container IDs remained unchanged, running, with OOM=false and RestartCount=0. Guest payloads successfully sampled each consuming bench. No image, mount, volume, VPN, Docker or WSL restart/change occurred.
- Existing Windows WSL watchdog and both CI runner tasks remain stopped and are correctly reported as issues. Their old healthy heartbeat is classified **stopped**, not healthy. Task Scheduler Operational history is disabled; the actor behind their earlier termination remains unknown.
- Final maintenance safeguard enumerates running distributions without starting one and skips guest probes when Ubuntu is stopped. This branch was verified with fixtures and normal live enumeration, not by shutting down active WSL. The runbook explicitly pauses the recorder for offline maintenance. The earlier supervision test exercised the unchanged installer/task mechanism before this final guard was added; the final source was then reinstalled and fresh live sampling verified again.

## Dashboard experiment

Computer Use observed the actual Containers dashboard, invoked its Close window control without quitting Docker, and reopened the existing application. Docker's engine session ID did not change. The first reopen helper returned before a window appeared; later fresh observation verified the reopened dashboard. Provisional marker rows before observed transitions were excluded; old log tails were not counted as new-phase traffic.

| Observed condition | Recent stats-request log evidence | Docker API |
|---|---|---|
| Dashboard open, before 17:51:07 | Approximately 56-58 entries/sec, including hundreds of inactive containers | Approximately 0.36-0.53 sec |
| Dashboard closed, from 17:51:07 until reopen | No advancing stats entries observed; repeated log tails still ended at 17:50:56 | Approximately 0.38-0.41 sec |
| Dashboard reopened; verified after 17:54, with later fresh windows | Approximately 57-59 entries/sec resumed | Approximately 0.39-0.60 sec |

This strongly links this polling load to the dashboard. It does **not** establish that polling causes the recurring freezes: no freeze was reproduced, other user workloads continued, and sampled log windows are not complete request totals. A minimized dashboard was already polling in the initial baseline; minimizing and closing are different experiments. The recorder was refined to retain phase start times, reject previous-phase entries and mark old log windows stale instead of displaying an old rate as current.

## Remaining qualification and approvals

The non-disruptive recorder and short dashboard comparison are implemented. Sustained stability and the freeze's initiating root cause are **not** qualified. At the next incident preserve this local evidence before recovery. Local Docker diagnostic bundle capture, a bounded debug-log reproduction, a WSL trace, and administrative Task Scheduler history activation remain coordinated follow-ups. Full logoff/sign-in or reboot acceptance is not implied by the scheduler fault test.

The initial implementation and dashboard measurements did not resume existing CI/watchdog tasks, replace m365-bench, change workload limits/networking/VPN/Kubernetes, roll back versions, migrate engines or upload diagnostics. PR publication/landing and the subsequently authorized CI/watchdog resumption are separate acceptance gates, tracked in PR #328 and the live operator readback. The installed local recorder runs independently of source publication.
