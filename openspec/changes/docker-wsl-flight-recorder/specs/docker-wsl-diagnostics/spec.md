## ADDED Requirements

### Requirement: Non-disruptive bounded evidence

The recorder SHALL preserve bounded local evidence without restarting services, replacing containers, killing user jobs, uploading data or changing runtime configuration. It SHALL terminate only an owned diagnostic client on timeout and persistently latch the affected path until an explicit probe reset while stopped. An interrupted probe SHALL latch its path after process replacement.

#### Scenario: A probe hangs

- **WHEN** a diagnostic client exceeds its deadline
- **THEN** the recorder records a timeout, stops that client only, and does not submit another probe on that path until an explicit probe reset

### Requirement: Independent and cache-aware health

The recorder SHALL report Docker API, WSL transport, selected bench, Windows resource and task health separately. It SHALL distinguish reclaimable/cache memory, process-leader zombies and blocked threads. A stale heartbeat or dead daemon SHALL not be reported healthy.

#### Scenario: Old healthy status survives daemon termination

- **WHEN** the status file says healthy but its timestamp is stale or its recorded process identity is absent
- **THEN** status reports stale or stopped rather than healthy

### Requirement: Bounded privacy-preserving retention

The recorder SHALL retain rotated samples and failure transitions outside the repository. Routine samples SHALL exclude process arguments, environments, credentials, raw application logs and Docker stats polling. Log analysis SHALL emit aggregate counts only.

#### Scenario: Docker logs contain sensitive unrelated content

- **WHEN** the recorder summarizes recent API polling
- **THEN** only matching endpoint counts and the observed time window enter its output
