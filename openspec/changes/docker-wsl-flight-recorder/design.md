## Context

Recent observations include cache-heavy memory figures, a stale Windows watchdog and stopped CI tasks, and repeated stats requests for inactive containers. An older captured RTNL stall included zombie process leaders with blocked worker threads. These are separate hypotheses, not an established shared cause.

## Goals / Non-Goals

Goals: retain evidence across WSL transport failure, distinguish failure layers, bound overhead, expose stale monitoring, and support a reproducible dashboard experiment.

Non-goals: automatic recovery, CI resumption, image changes, cleanup, VPN changes, debug-mode activation, data upload, or a Linux migration.

## Decisions

- Native PowerShell 7 runs from a local Windows copy launched by Task Scheduler, not the interactive agent's process tree. A restart-on-failure policy and periodic trigger supervise only this recorder. Alternatives: a WSL collector would disappear with the failing subsystem; a background child of the agent repeats the termination risk.
- One sequential probe at a time. Terminate only the exact owned diagnostic client after a deadline. Persist timed-out or interrupted path latches across automatic recorder replacement until explicit ResetProbes while stopped; never automatically kill guest processes or continuously repeat probes against a wedged kernel.
- Record Windows metrics, WSL memory/pressure, Docker inventory and one selected bench per cycle. Bench samples include cgroup anon/file/kernel memory and process-leader zombies versus blocked threads. Never use the Docker stats endpoint for routine collection.
- Record only allowlisted metrics and task/heartbeat metadata. Docker log analysis emits aggregate endpoint counts, never raw lines. No command arguments, environments, credential/config contents, job logs, packet captures or automatic uploads.
- Keep a 4 MiB x 4 sample ring and at most 12 bounded incident records. Status verifies timestamp and process identity; a dead recorder cannot remain healthy on readback.

## Risks / Trade-offs

- A killed WSL client cannot guarantee a kernel-blocked guest exited: latch that path after timeout.
- A current healthy snapshot cannot prove sustained stability: retain sampling timestamps and pending acceptance gates.
- Task Scheduler may itself be stopped: status checks daemon PID/start time and sample age, not task enablement alone.
- Docker log rotation can race reads: treat missing/partial log windows as unavailable, not a zero request rate.

## Migration Plan

Test synthetic fixtures and real read-only samples, install into a user-local Windows directory, verify independent ancestry and repeated samples, then run the manual dashboard A/B experiment without quitting Docker. Rollback stops/disables only the recorder and preserves evidence. Publish/merge and disruptive experiments remain separate approvals.
